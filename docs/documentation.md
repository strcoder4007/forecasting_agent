
Goal: To make a forecasting agent that can predict SKU-size-store demand. I have taken learnings from Akshay's ML approach and Ravi's forecasting agent requirements to create this doc.


1) Required data
The agent must be able to read these tables or CSVs and aggregate them to weekly (Monday start).

Sales: store_id, sku_id, date, qty_sold (preferably 2 years of history).  
Stock on hand: store_id, sku_id, date, stock_qty (same history).  
Promotions calendar: store_id, sku_id, start_date, end_date, discount_pct.  
Store metadata: store_id, cluster_label, price_elasticity_score, region.  
Optional holidays table: date, holiday_name. If missing, use a small holidays library.  
Agent note: read, validate, then aggregate to week_start before any feature computations.


2) The 10 features and how to compute them
All stats are computed per combo combo_id = store_id + '_' + sku_id. Shift any rolling or series-based statistic by one week to avoid leakage.

n_stores — number of stores carrying this SKU.
n_stores = df.groupby('sku_id')['store_id'].nunique()  

rolling_cv_4 — coefficient of variation over trailing 4 weeks, shifted.
rolling_cv_4 = rolling_std_4 / (rolling_mean_4 + 1e-6)  

rolling_std_4 — standard deviation of qty over trailing 4 weeks, shifted.
rolling_std_4 = groupby(combo).qty.shift(1).rolling(4).std()  

avg_rsp — average retail selling price for the combo, fallback to category mean if needed.
avg_rsp = df.groupby(combo)['price'].transform('mean')  

season_to_date_qty — cumulative qty in the current season to date, shifted. Define season by business rule (fiscal quarter or custom season).
season_to_date_qty = groupby(combo).qty.shift(1).groupby(season).cumsum()  

qty_vs_rolling_mean — ratio of last observed week qty to rolling mean over 4 weeks.
qty_vs_rolling_mean = qty_lag_1 / (rolling_mean_4 + 1e-6)  

pattern_type_std_cat — categorical encoding of demand pattern: smooth, intermittent, or lumpy. Rules: percent zero weeks > 50% -> intermittent; cv > 1 -> lumpy; otherwise smooth. Encode as integers.  
ewma_4 — exponentially weighted moving average with span 4, shifted.
ewma_4 = qty.shift(1).ewm(span=4).mean()  

qty_lag_3 — qty three weeks ago. qty_lag_3 = qty.shift(3)  
qty_lag_2 — qty two weeks ago. qty_lag_2 = qty.shift(2)  
Implementation hint: do weekly aggregation once, then compute these features in a vectorized pass. Persist the feature table.


3) Where complexity was reduced
I kept all business rules and preserved the pipeline behavior, while removing sources of engineering and compute friction.

Features: reduced from 31 to your 10 features. 
Model zoo: limit to four models only: Seasonal Naive baseline, Ridge regression, LightGBM, and Croston for intermittent demand. Remove heavy neural models. 
Validation: two-round walk-forward validation instead of more rounds. Two rounds still give time-aware checks and are much faster. 
Model routing: route models by demand segment only, with the smaller model set above. 
External signals: keep promotion and holiday signals only. Drop weather and other brittle APIs or make them optional. 
Post-processing: a single section bias correction plus a 50/50 blend with recent on-shelf average sales. Remove complex stacking and heavy ensembling. 
Confidence intervals: estimate empirically from validation residuals rather than training quantile models. 
These choices keep signal and business rules while making the system deterministic and easy to automate.


4) Agent workflow, step by step
Follow these steps in order. Each step is actionable and deterministic.

Load and aggregate Read Sales, Stock, Promotions, and Store metadata. 
Aggregate daily to weekly with week_start Monday. Compute qty_weekly = sum(qty_sold) and stock_weekly = max(stock_qty).    
False-zero correction If stock_weekly == 0 and qty_weekly == 0, replace qty_weekly with the category median weekly value computed from weeks where stock_weekly > 0. Flag is_false_zero = 1.    
Demand segmentation Per combo, compute percent zero weeks and coefficient of variation (std/mean). Assign pattern_type_std_cat as smooth, intermittent, or lumpy using the rules in Section 2.    
Compute the 10 features Use shifted rolling windows and vectorized transforms. Persist a single feature table keyed by combo_id and week_start.    
Prepare training and validation windows Use recent 6 to 12 months as the general training range. Create two walk-forward rounds: R1: train up to T1, validate on T1+1 week. 
R2: train up to T2 (T1+1), validate on T2+1 week. 
Save validation residuals for each round for later CI estimation and bias correction. 
Model training and selection by combo For each combo, route models by segment: Smooth: Seasonal Naive, Ridge, LightGBM. 
Intermittent: Croston, Ridge, Seasonal Naive. 
Lumpy: LightGBM, Ridge, Seasonal Naive. 
Train the routed models on R1 and R2 train sets. Evaluate WMAPE on both validation rounds. Select the model with the lowest average WMAPE and record model_used in a model registry.    
Inference Compute feature values up to the last available week with no leakage. Load the selected model for each combo and predict the point forecast. 
Post-processing and blending Apply zero-forecast gate conditions and set point_forecast = 0 if the gate triggers.  
Apply section-level multiplicative correction using historical residuals. 
Compute recent on-shelf average sales, ros = avg(last 4 weeks qty). Blend: final = round(0.5 * point_forecast + 0.5 * ros). Clip at zero.  
Estimate lower and upper 80 percent intervals using empirical quantiles of validation residuals. 
Publish results Write final records to the shared output store in a compact schema described below. 
Quick run checklist (for the agent to follow each cycle)

Read source tables and weekly aggregate. 
Run false-zero correction and flag items. 
Compute pattern_type_std_cat and the 10 features.  
Run two-round walk-forward training for routed model sets. 
Select best model per combo by average WMAPE. 
Predict, apply zero gate, apply section correction and ROS blend. 
Compute empirical 80 percent CI from validation residuals. 
Publish forecasts to shared storage. 


5) Minimal outputs and schema
Downstream consumers need a compact, stable set of fields. Output exactly these columns:
store_id, sku_id, combo_id, forecast_week_start, horizon, point_forecast, lower_80, upper_80, model_used, demand_segment, is_zero_forecast
Write outputs as Parquet or a database table with append semantics. Keep only these fields to avoid downstream mapping work.


6) Engineering guardrails and operational limits
Make the agent fail-safe and observable.
Leakage checks

All rolling, EWMA, and lag features must use .shift(1) before rolling windows. If any rolling computation includes the target week, fail the run and log the combo.  
NaN policy

Impute numeric NaNs with zero for features, but log combos with more than 20 percent NaNs and skip training for them. 
Compute budget and model limits

LightGBM default: n_estimators = 200, max_depth = 6 to keep training time bounded. Do not run neural models.  
Monitoring and drift

Persist weekly WMAPE per model and per combo to a small monitoring table. Trigger an alert if WMAPE increases by a configurable threshold, for example 30 percent from baseline. 
Other rules

Keep promotion and holiday flags only. Make weather and other signals optional and configurable. 
Model registry must record model_used, training_time, validation_wmape, and the validation residual distribution.  
Why this is agent-friendly

The feature set is small and deterministic, so vectorized computation is straightforward. 
The model set is small and well known, which makes training, evaluation, and inference fast and reliable. 
Two validation rounds enforce time-aware checks without heavy compute. 
Post-processing and CI estimation use empirical residuals, which avoids training additional complex models. 
The output schema is minimal and stable, which reduces downstream integration work.

