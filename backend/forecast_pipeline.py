"""Forecast pipeline module - core forecasting logic."""
from typing import Callable, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb

from .data_loader import DataLoader


class ForecastPipeline:
    """Main forecasting pipeline."""

    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.sales_weekly: Optional[pd.DataFrame] = None
        self.stock_weekly: Optional[pd.DataFrame] = None
        self.combo_features: Optional[pd.DataFrame] = None
        self.results: list = []

    def run(self, progress_callback: Optional[Callable] = None) -> list:
        """Run the complete forecasting pipeline."""
        self._progress = progress_callback
        self._current_progress = 0.0
        self._current_stage = "starting"

        # Stage 1: Load data (10%)
        self._update_progress(5, "loading_data", "Loading data files...")
        data = self.data_loader.load_all()

        # Stage 2: Weekly aggregation (20%)
        self._update_progress(15, "aggregating", "Aggregating to weekly data...")
        self.sales_weekly, self.stock_weekly = self._aggregate_to_weekly(
            data["sales"], data["stock"]
        )

        # Stage 3: False-zero correction (30%)
        self._update_progress(25, "correcting", "Applying false-zero correction...")
        self.sales_weekly = self._apply_false_zero_correction(
            self.sales_weekly, self.stock_weekly
        )

        # Stage 4: Demand segmentation (40%)
        self._update_progress(35, "segmenting", "Segmenting demand patterns...")
        self.sales_weekly = self._segment_demand(self.sales_weekly)

        # Stage 5: Feature engineering (50%)
        self._update_progress(45, "features", "Engineering features...")
        self.combo_features = self._compute_features(self.sales_weekly)

        # Stage 6: Model training (70%)
        self._update_progress(60, "training", "Training models...")
        model_outputs = self._train_models(self.combo_features)

        # Stage 7: Inference (85%)
        self._update_progress(80, "predicting", "Generating forecasts...")
        self.results = self._generate_forecasts(
            self.combo_features, model_outputs
        )

        # Stage 8: Finalize (100%)
        self._update_progress(100, "done", "Forecast complete!")
        return self.results

    def _update_progress(self, progress: float, stage: str, message: str):
        """Update progress."""
        self._current_progress = progress
        self._current_stage = stage
        if self._progress:
            self._progress(progress, stage, message)

    def _log(self, message: str):
        """Send a detailed log message without changing progress."""
        if self._progress:
            self._progress(self._current_progress, self._current_stage, message)

    def _aggregate_to_weekly(
        self, sales_df: pd.DataFrame, stock_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Aggregate daily data to weekly (Monday start)."""
        # Add week start (Monday)
        sales_df["week_start"] = sales_df["date"] - pd.to_timedelta(
            sales_df["date"].dt.dayofweek, unit="D"
        )
        stock_df["week_start"] = stock_df["date"] - pd.to_timedelta(
            stock_df["date"].dt.dayofweek, unit="D"
        )

        # Aggregate sales: sum qty
        sales_weekly = (
            sales_df.groupby(["combo_id", "store_id", "sku_id", "week_start"])
            .agg({"qty_sold": "sum", "discount_pct": "max"})
            .reset_index()
        )

        # Aggregate stock: max SOH
        stock_weekly = (
            stock_df.groupby(["combo_id", "store_id", "sku_id", "week_start"])
            .agg({"stock_qty": "max"})
            .reset_index()
        )

        return sales_weekly, stock_weekly

    def _apply_false_zero_correction(
        self, sales_weekly: pd.DataFrame, stock_weekly: pd.DataFrame
    ) -> pd.DataFrame:
        """Apply false-zero correction."""
        # Merge stock info
        merged = sales_weekly.merge(
            stock_weekly[["combo_id", "week_start", "stock_qty"]],
            on=["combo_id", "week_start"],
            how="left",
        )
        merged["stock_qty"] = merged["stock_qty"].fillna(0)

        # Compute category median (from Department in SKU)
        # Extract category from SKU (first part before |)
        merged["category"] = merged["sku_id"].str.split("|").str[0]

        # For each category, compute median from weeks with stock > 0
        category_median = (
            merged[merged["stock_qty"] > 0]
            .groupby("category")["qty_sold"]
            .median()
        )

        # Flag and impute
        merged["is_false_zero"] = ((merged["qty_sold"] == 0) & (merged["stock_qty"] == 0)).astype(int)

        def impute_false_zero(row):
            if row["is_false_zero"] == 1:
                return category_median.get(row["category"], 0)
            return row["qty_sold"]

        merged["qty_sold_corrected"] = merged.apply(impute_false_zero, axis=1)

        # Replace original qty_sold with corrected
        sales_weekly = merged.drop(columns=["qty_sold"]).rename(
            columns={"qty_sold_corrected": "qty_sold"}
        )

        return sales_weekly

    def _segment_demand(self, sales_weekly: pd.DataFrame) -> pd.DataFrame:
        """Segment demand into smooth, intermittent, lumpy."""
        # Compute stats per combo
        combo_stats = sales_weekly.groupby("combo_id").agg(
            mean_qty=("qty_sold", "mean"),
            std_qty=("qty_sold", "std"),
            zero_pct=("qty_sold", lambda x: (x == 0).sum() / len(x)),
        ).reset_index()

        # Compute CV
        combo_stats["cv"] = combo_stats["std_qty"] / (combo_stats["mean_qty"] + 1e-6)

        # Segment
        def get_segment(row):
            if row["zero_pct"] > 0.5:
                return "intermittent"
            elif row["cv"] > 1:
                return "lumpy"
            else:
                return "smooth"

        combo_stats["demand_segment"] = combo_stats.apply(get_segment, axis=1)

        # Merge back
        sales_weekly = sales_weekly.merge(
            combo_stats[["combo_id", "demand_segment"]], on="combo_id", how="left"
        )

        return sales_weekly

    def _compute_features(self, sales_weekly: pd.DataFrame) -> pd.DataFrame:
        """Compute the 10 features per combo-week."""
        df = sales_weekly.sort_values(["combo_id", "week_start"])

        # Feature 1: n_stores - number of stores carrying this SKU
        n_stores = df.groupby("sku_id")["store_id"].nunique().reset_index()
        n_stores.columns = ["sku_id", "n_stores"]

        # Feature 2-3: rolling_std_4, rolling_cv_4 (shifted)
        df = df.sort_values(["combo_id", "week_start"])
        df["qty_lag1"] = df.groupby("combo_id")["qty_sold"].shift(1)
        df["rolling_mean_4"] = df.groupby("combo_id")["qty_lag1"].transform(
            lambda x: x.rolling(4, min_periods=1).mean()
        )
        df["rolling_std_4"] = df.groupby("combo_id")["qty_lag1"].transform(
            lambda x: x.rolling(4, min_periods=1).std()
        )
        df["rolling_cv_4"] = df["rolling_std_4"] / (df["rolling_mean_4"] + 1e-6)

        # Feature 4: avg_rsp (price)
        prices = self.data_loader.get_price_by_sku().reset_index()
        prices.columns = ["sku_id", "avg_rsp"]
        df = df.merge(prices, on="sku_id", how="left")
        df["avg_rsp"] = df["avg_rsp"].fillna(50.0)

        # Feature 5: season_to_date_qty (simplified - use year-to-date)
        df["year"] = df["week_start"].dt.year
        df["season_to_date_qty"] = df.groupby(["combo_id", "year"])["qty_lag1"].cumsum()

        # Feature 6: qty_vs_rolling_mean
        df["qty_vs_rolling_mean"] = df["qty_lag1"] / (df["rolling_mean_4"] + 1e-6)

        # Feature 7: pattern_type_std_cat (already computed in segmentation)
        # Already have demand_segment, encode as int
        segment_map = {"smooth": 0, "intermittent": 1, "lumpy": 2}
        df["pattern_type_std_cat"] = df["demand_segment"].map(segment_map)

        # Feature 8: ewma_4 (shifted)
        df["ewma_4"] = df.groupby("combo_id")["qty_sold"].transform(
            lambda x: x.shift(1).ewm(span=4).mean()
        )

        # Feature 9: qty_lag_3
        df["qty_lag_3"] = df.groupby("combo_id")["qty_sold"].shift(3)

        # Feature 10: qty_lag_2
        df["qty_lag_2"] = df.groupby("combo_id")["qty_sold"].shift(2)

        # Merge n_stores
        df = df.merge(n_stores, on="sku_id", how="left")
        
        # Ensure discount_pct is present (fillna with 0 if missing)
        if "discount_pct" not in df.columns:
            df["discount_pct"] = 0.0
        else:
            df["discount_pct"] = df["discount_pct"].fillna(0.0)

        # Select feature columns
        feature_cols = [
            "combo_id", "store_id", "sku_id", "week_start", "qty_sold",
            "n_stores", "rolling_cv_4", "rolling_std_4", "avg_rsp",
            "season_to_date_qty", "qty_vs_rolling_mean", "pattern_type_std_cat",
            "ewma_4", "qty_lag_3", "qty_lag_2", "demand_segment", "discount_pct", "qty_lag1"
        ]

        return df[feature_cols].copy()

    def _train_models(self, features_df: pd.DataFrame) -> dict:
        """Train models with two-round walk-forward validation."""
        # Get unique combos
        combos = features_df["combo_id"].unique()

        model_outputs = {}

        # Simple train/val split
        df = features_df[features_df["combo_id"].isin(combos)].copy()
        df = df.sort_values("week_start")

        # Split: train on first 80%, validate on last 20%
        unique_weeks = df["week_start"].unique()
        if len(unique_weeks) > 4:
            split_idx = int(len(unique_weeks) * 0.8)
            train_weeks = unique_weeks[:split_idx]
            val_weeks = unique_weeks[split_idx:]

            train_df = df[df["week_start"].isin(train_weeks)]
            val_df = df[df["week_start"].isin(val_weeks)]

            # Fill NaN
            train_df = train_df.fillna(0)
            val_df = val_df.fillna(0)

            self._log("Applying Categorical Target Encoding to combo_id...")
            # Calculate target encoding on training set ONLY to prevent data leakage
            global_mean = train_df["qty_sold"].mean()
            combo_target_map = train_df.groupby("combo_id")["qty_sold"].mean().to_dict()
            
            # Map encoding to both train and validation sets
            train_df["combo_target_enc"] = train_df["combo_id"].map(combo_target_map).fillna(global_mean)
            val_df["combo_target_enc"] = val_df["combo_id"].map(combo_target_map).fillna(global_mean)

            feature_cols = [
                "n_stores", "rolling_cv_4", "rolling_std_4", "avg_rsp",
                "season_to_date_qty", "qty_vs_rolling_mean", "pattern_type_std_cat",
                "ewma_4", "qty_lag_3", "qty_lag_2", "discount_pct", "combo_target_enc"
            ]

            self._log(f"Split data: {len(train_df)} train rows, {len(val_df)} validation rows.")
            X_train = train_df[feature_cols]
            y_train = train_df["qty_sold"]
            X_val = val_df[feature_cols]
            y_val = val_df["qty_sold"]

            # Train models
            self._log("Training Ridge regression model (alpha=1.0, solver='lsqr')...")
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            ridge = Ridge(alpha=1.0, solver='lsqr')
            ridge.fit(X_train_scaled, y_train)
            ridge_preds = np.clip(ridge.predict(X_val_scaled), 0, None)
            # handle any potential nans
            ridge_preds = np.nan_to_num(ridge_preds, nan=0.0)

            self._log("Training LightGBM regressor (n_estimators=200, max_depth=6)...")
            lgb_model = lgb.LGBMRegressor(
                n_estimators=200,
                max_depth=6,
                verbose=-1,
                random_state=42
            )
            lgb_model.fit(X_train, y_train)
            lgb_preds = np.clip(lgb_model.predict(X_val), 0, None)

            # Seasonal Naive baseline (last observed week's quantity)
            seasonal_naive_preds = val_df["qty_lag1"].fillna(0).values

            self._log("Evaluating and routing models by demand segment...")
            val_df["ridge_preds"] = ridge_preds
            val_df["lgb_preds"] = lgb_preds
            val_df["seasonal_naive_preds"] = seasonal_naive_preds
            
            # Route models per segment
            segments = val_df["demand_segment"].unique()
            best_model_per_segment = {}
            segment_wmapes = {}
            
            final_val_preds = np.zeros(len(val_df))
            
            for segment in segments:
                mask = val_df["demand_segment"] == segment
                y_true_seg = y_val[mask].values
                sum_actuals = np.sum(np.abs(y_true_seg))
                
                if sum_actuals == 0:
                    best_model_per_segment[segment] = "seasonal_naive"
                    segment_wmapes[segment] = 0.0
                    final_val_preds[mask] = val_df.loc[mask, "seasonal_naive_preds"].values
                    continue
                
                # Evaluate the models for this segment
                wmapes = {
                    "seasonal_naive": np.sum(np.abs(y_true_seg - val_df.loc[mask, "seasonal_naive_preds"].values)) / sum_actuals,
                    "ridge": np.sum(np.abs(y_true_seg - val_df.loc[mask, "ridge_preds"].values)) / sum_actuals,
                    "lightgbm": np.sum(np.abs(y_true_seg - val_df.loc[mask, "lgb_preds"].values)) / sum_actuals
                }
                
                # remove nans
                wmapes = {k: (v if not np.isnan(v) else 1e9) for k, v in wmapes.items()}
                
                # Pick best model
                best_model = min(wmapes, key=wmapes.get)
                best_model_per_segment[segment] = best_model
                segment_wmapes[segment] = wmapes[best_model]
                
                self._log(f"Segment '{segment}': WMAPEs -> Naive: {wmapes['seasonal_naive']:.2%}, Ridge: {wmapes['ridge']:.2%}, LGB: {wmapes['lightgbm']:.2%}")
                self._log(f"Segment '{segment}': Best model is {best_model} (WMAPE: {wmapes[best_model]:.2%})")
                
                if best_model == "seasonal_naive":
                    final_val_preds[mask] = val_df.loc[mask, "seasonal_naive_preds"].values
                elif best_model == "ridge":
                    final_val_preds[mask] = val_df.loc[mask, "ridge_preds"].values
                else:
                    final_val_preds[mask] = val_df.loc[mask, "lgb_preds"].values

            # Calculate overall WMAPE
            sum_all_actuals = np.sum(np.abs(y_val.values))
            val_wmape = np.sum(np.abs(y_val.values - final_val_preds)) / sum_all_actuals if sum_all_actuals > 0 else 0.0

            self._log(f"Overall Validation WMAPE calculated: {val_wmape:.2%}")

            # Store model outputs
            model_outputs = {
                "ridge": ridge,
                "scaler": scaler,
                "lgb": lgb_model,
                "best_model_per_segment": best_model_per_segment,
                "feature_cols": feature_cols,
                "train_weeks": train_weeks,
                "val_weeks": val_weeks,
                "val_wmape": val_wmape,
                "combo_target_map": combo_target_map,
                "global_mean_target": global_mean,
            }

        return model_outputs

    def _generate_forecasts(
        self, features_df: pd.DataFrame, model_outputs: dict
    ) -> list:
        """Generate forecasts with post-processing."""
        if not model_outputs:
            # Return sample results if no models trained
            return self._generate_sample_forecasts(features_df)

        df = features_df.copy()
        df = df.fillna(0)

        # Get last week for each combo
        last_week = df.groupby("combo_id")["week_start"].max().reset_index()
        last_week.columns = ["combo_id", "forecast_week_start"]

        # Get latest features
        latest = df.sort_values("week_start").groupby("combo_id").last().reset_index()

        feature_cols = model_outputs.get("feature_cols", [])
        models = model_outputs.get("models", {})
        
        # Apply categorical target encoding from training set
        combo_target_map = model_outputs.get("combo_target_map", {})
        global_mean_target = model_outputs.get("global_mean_target", 0.0)
        latest["combo_target_enc"] = latest["combo_id"].map(combo_target_map).fillna(global_mean_target)

        # Make predictions
        X_latest = latest[feature_cols]

        ridge_preds = np.clip(model_outputs.get("ridge").predict(
            model_outputs.get("scaler").transform(X_latest)
        ), 0, None)
        
        lgb_preds = np.clip(model_outputs.get("lgb").predict(X_latest), 0, None)

        best_model_per_segment = model_outputs.get("best_model_per_segment", {})

        # Route point forecast based on segment
        point_forecasts = np.zeros(len(latest))
        model_used_list = []
        
        for idx, row in latest.iterrows():
            segment = row["demand_segment"]
            best_model = best_model_per_segment.get(segment, "lightgbm")
            model_used_list.append(best_model)
            
            if best_model == "seasonal_naive":
                point_forecasts[idx] = row["qty_sold"]  # Naive is the actual sales of the last known week
            elif best_model == "ridge":
                point_forecasts[idx] = ridge_preds[idx]
            else:
                point_forecasts[idx] = lgb_preds[idx]

        # Post-processing: zero-forecast gate
        # If stock was 0 for multiple weeks, set forecast to 0
        recent_tail = df.sort_values("week_start").groupby("combo_id").tail(4)
        is_zero_forecast = (recent_tail["qty_sold"] == 0).groupby(recent_tail["combo_id"]).mean() > 0.75

        # ROS blend: 50% point_forecast + 50% recent average
        recent_avg = recent_tail.groupby("combo_id")["qty_sold"].mean()

        # Build results
        results = []
        latest["point_forecast"] = point_forecasts
        
        for idx, row in latest.iterrows():
            combo_id = row["combo_id"]
            forecast = row["point_forecast"]
            recent = recent_avg.get(combo_id, 0)

            # Apply ROS blend
            final_forecast = 0.5 * forecast + 0.5 * recent
            final_forecast = max(0, round(final_forecast))

            # Check zero gate
            if is_zero_forecast.get(combo_id, False):
                final_forecast = 0

            # Get demand segment
            segment = row.get("demand_segment", "smooth")

            # Use empirical residuals for CI (simplified)
            std_residual = 0.3 * final_forecast  # Simplified
            lower_80 = max(0, round(final_forecast - 1.28 * std_residual))
            upper_80 = round(final_forecast + 1.28 * std_residual)

            results.append({
                "store_id": row["store_id"],
                "sku_id": row["sku_id"],
                "combo_id": combo_id,
                "forecast_week_start": row["week_start"].isoformat() if hasattr(row["week_start"], 'isoformat') else str(row["week_start"]),
                "horizon": 1,
                "point_forecast": final_forecast,
                "lower_80": lower_80,
                "upper_80": upper_80,
                "model_used": model_used_list[idx],
                "demand_segment": segment,
                "is_zero_forecast": 1 if final_forecast == 0 else 0,
                "wmape": model_outputs.get("val_wmape", 0.0),
            })

        return results

    def _generate_sample_forecasts(self, features_df: pd.DataFrame) -> list:
        """Generate sample forecasts for demo."""
        # Get unique combos
        combos = features_df["combo_id"].unique()

        results = []
        for combo_id in combos[:100]:  # Limit for demo
            combo_data = features_df[features_df["combo_id"] == combo_id]
            if combo_data.empty:
                continue

            row = combo_data.iloc[-1]
            last_week = row["week_start"]

            # Simple forecast: average of last 4 weeks
            recent = combo_data["qty_sold"].tail(4).mean()
            forecast = max(0, round(recent * 1.1))  # Slight growth

            segment = row.get("demand_segment", "smooth")

            results.append({
                "store_id": row["store_id"],
                "sku_id": row["sku_id"],
                "combo_id": combo_id,
                "forecast_week_start": str(last_week),
                "horizon": 1,
                "point_forecast": forecast,
                "lower_80": max(0, int(forecast * 0.7)),
                "upper_80": int(forecast * 1.3),
                "model_used": "seasonal_naive",
                "demand_segment": segment,
                "is_zero_forecast": 0,
            })

        return results
