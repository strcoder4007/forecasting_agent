import os
import json
import duckdb
import pandas as pd
import numpy as np
from google import genai
from google.genai import types

class ChatService:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))
        self.supervisor_model = "gemini-3.1-flash-lite-preview"
        self.analyst_model = "gemini-3.1-pro-preview"
        
        # State to store during a single chat request
        self.current_results_df = None
        self.current_stores_df = None
        self.current_items_df = None
        self.current_features_df = None
        self.current_model_outputs = None
        self.all_runs = {}
        self.trace = []
        
        # Action state
        self.pending_action = None
        self.pending_payload = None

    def start_new_forecast(self) -> str:
        """Instructs the system to start a brand new forecasting run."""
        self.pending_action = "START_FORECAST"
        return "System instructed to start a new forecast."

    def load_historical_run(self, run_id: str) -> str:
        """Loads a specific historical run so its data can be analyzed."""
        if run_id not in self.all_runs:
            return f"Error: Run ID {run_id} not found."
        
        self.pending_action = "LOAD_RUN"
        self.pending_payload = run_id
        return f"SYSTEM_TRIGGER: RUN_LOADED {run_id}"

    def get_historical_runs(self, limit: int = 5) -> str:
        """Returns a list of recent forecast runs, their IDs, timestamps, and status."""
        runs = list(self.all_runs.values())
        runs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if not runs:
            return "There are no historical runs available."
            
        summary = []
        for r in runs[:limit]:
            wmape = f"{r.get('avg_wmape', 0.0):.2%}" if r.get('avg_wmape') else "N/A"
            summary.append(f"- ID: {r['run_id']} | Status: {r['status']} | Date: {r['timestamp']} | WMAPE: {wmape}")
        
        return "\n".join(summary)

    def execute_sql(self, query: str) -> str:
        """Executes a DuckDB SQL query against the forecasting datasets and returns the result as markdown.
        Available tables: results_df, stores_df, items_df, features_df. Do NOT use backticks around table names.
        """
        try:
            results_df = self.current_results_df
            stores_df = self.current_stores_df
            items_df = self.current_items_df
            features_df = self.current_features_df
            
            result_df = duckdb.query(query).df()
            res = result_df.to_markdown(index=False)
            self.trace.append({"type": "tool_result", "agent": "analyst", "name": "execute_sql", "result": f"Returned {len(result_df)} rows"})
            return res
        except Exception as e:
            self.trace.append({"type": "error", "agent": "analyst", "name": "execute_sql", "message": str(e)})
            return f"SQL Error: {str(e)}"

    def simulate_promotion(self, sku_id: str, store_id: str, discount_pct: float) -> str:
        """Simulates the new forecast if a specific discount percentage is applied to a SKU in a Store next week. discount_pct should be a decimal (e.g. 0.2 for 20%)."""
        if self.current_features_df is None or self.current_model_outputs is None:
            err = "Simulation is not available because no context is loaded. Load a completed run first."
            self.trace.append({"type": "error", "agent": "analyst", "name": "simulate_promotion", "message": err})
            return err

        df = self.current_features_df
        mask = (df["store_id"] == store_id) & (df["sku_id"] == sku_id)
        combo_data = df[mask]
        
        if combo_data.empty:
            err = f"Error: No historical data found for SKU {sku_id} in Store {store_id}."
            self.trace.append({"type": "error", "agent": "analyst", "name": "simulate_promotion", "message": err})
            return err
            
        latest_row = combo_data.sort_values("week_start").iloc[-1:].copy()
        
        latest_row["discount_pct"] = float(discount_pct)
        latest_row["is_promotional"] = int(discount_pct > 0)
        
        if discount_pct <= 0:
            depth = 0
        elif discount_pct <= 0.1:
            depth = 1
        elif discount_pct <= 0.2:
            depth = 2
        else:
            depth = 3
        latest_row["promo_depth"] = depth
        
        feature_cols = self.current_model_outputs.get("feature_cols", [])
        if not feature_cols:
            return "Error: Model features not found."
            
        combo_target_map = self.current_model_outputs.get("combo_target_map", {})
        global_mean_target = self.current_model_outputs.get("global_mean_target", 0.0)
        combo_val = latest_row["combo_id"].iloc[0]
        latest_row["combo_target_enc"] = combo_target_map.get(combo_val, global_mean_target)
        
        X_latest = latest_row[feature_cols].astype(np.float64)
        
        ridge = self.current_model_outputs.get("ridge")
        scaler = self.current_model_outputs.get("scaler")
        lgb_model = self.current_model_outputs.get("lgb")
        xgb_model = self.current_model_outputs.get("xgb")
        best_model_per_segment = self.current_model_outputs.get("best_model_per_segment", {})
        
        ridge_preds = np.clip(ridge.predict(np.nan_to_num(scaler.transform(X_latest))), 0, None)
        lgb_preds = np.clip(lgb_model.predict(X_latest), 0, None)
        xgb_preds = np.clip(xgb_model.predict(X_latest), 0, None)
        
        segment = latest_row["demand_segment"].iloc[0]
        best_model = best_model_per_segment.get(segment, "lightgbm")
        
        if best_model == "seasonal_naive":
            forecast = latest_row["qty_sold"].iloc[0]
        elif best_model == "ridge":
            forecast = ridge_preds[0]
        elif best_model == "xgboost":
            forecast = xgb_preds[0]
        else:
            forecast = lgb_preds[0]
            
        recent_avg = combo_data.sort_values("week_start").tail(4)["qty_sold"].mean()
        final_forecast = max(0, round(0.5 * forecast + 0.5 * recent_avg))
        
        res = f"Simulated forecast for SKU {sku_id} at Store {store_id} with {discount_pct*100}% discount: **{final_forecast} units**. (Model used: {best_model}, Segment: {segment})"
        self.trace.append({"type": "tool_result", "agent": "analyst", "name": "simulate_promotion", "result": f"Forecast: {final_forecast} ({best_model})"})
        return res

    def analyze_data(self, complex_query: str) -> str:
        """Handoff tool: Passes complex data queries to the specialized Data Analyst AI."""
        if self.current_results_df is None:
            return "Please load a completed forecast run first."

        # Get analysis report for analyst context
        analysis_report = ""
        if self.current_model_outputs and self.current_model_outputs.get("analysis_report"):
            analysis_report = self.current_model_outputs.get("analysis_report", "")
        
        analyst_system = f"""
        You are an expert Data Analyst AI. Your job is to answer the user's question by querying data.
        
        Available Data (use execute_sql tool):
        - results_df: point_forecast, lower_80, upper_80, model_used, demand_segment, is_zero_forecast, wmape, mape, store_id, sku_id.
        - stores_df: store_id, cluster_label, region.
        - items_df: sku_id, category, price.
        
        Data Exploration Report (for context):
        {analysis_report if analysis_report else "No exploration report available."}
        
        Instructions:
        1. Formulate a DuckDB SQL query to join/filter the data appropriately.
        2. Use `execute_sql` to run it.
        3. For "what-if" promo questions, use `simulate_promotion`.
        4. Read the output, synthesize a beautiful markdown answer, and return it.
        """

        self.trace.append({"type": "tool_call", "agent": "analyst", "name": "Analyst Wakeup", "args": {"query": complex_query}})

        try:
            chat_session = self.client.chats.create(
                model=self.analyst_model,
                config=types.GenerateContentConfig(
                    system_instruction=analyst_system,
                    tools=[self.execute_sql, self.simulate_promotion],
                    temperature=0.1,
                )
            )
            
            # Using native loop here since the tools handle their own trace appends
            response = chat_session.send_message(complex_query)

            if response.usage_metadata:
                self.trace.append({
                    "type": "info",
                    "agent": "analyst",
                    "message": "Analyst completed data analysis.",
                    "tokens": {
                        "input": response.usage_metadata.prompt_token_count,
                        "output": response.usage_metadata.candidates_token_count
                    }
                })

            return response.text
        except Exception as e:
            self.trace.append({"type": "error", "agent": "analyst", "name": "analyze_data", "message": str(e)})
            return f"Analyst Error: {str(e)}"

    def synthesize_forecast_results(self, run_results: list, current_run_id: str) -> str:
        """Synthesizes forecast results into a comprehensive summary when a forecast completes."""
        if not run_results:
            return "Forecast completed but no results were generated."

        results_df = pd.DataFrame(run_results)

        # Calculate key metrics
        total_predictions = len(results_df)
        unique_stores = results_df['store_id'].nunique() if 'store_id' in results_df.columns else 0
        unique_skus = results_df['sku_id'].nunique() if 'sku_id' in results_df.columns else 0

        # WMAPE calculation
        wmape = None
        wmape_value = None
        if 'wmape' in results_df.columns:
            valid_wmape = results_df['wmape'].dropna()
            if len(valid_wmape) > 0:
                weights = results_df.loc[valid_wmape.index, 'qty_sold'] if 'qty_sold' in results_df.columns else None
                if weights is not None and weights.sum() > 0:
                    wmape_value = (valid_wmape * weights).sum() / weights.sum()
                else:
                    wmape_value = valid_wmape.mean()
                wmape = f"{wmape_value:.2%}"

        # Total forecast value
        total_forecast = 0
        if 'point_forecast' in results_df.columns:
            total_forecast = results_df['point_forecast'].sum()

        # Model distribution
        model_counts = {}
        if 'model_used' in results_df.columns:
            model_counts = results_df['model_used'].value_counts().to_dict()

        # Segment distribution
        segment_counts = {}
        if 'demand_segment' in results_df.columns:
            segment_counts = results_df['demand_segment'].value_counts().to_dict()

        # Zero forecasts
        zero_forecasts = 0
        if 'is_zero_forecast' in results_df.columns:
            zero_forecasts = results_df['is_zero_forecast'].sum()

        # Top stores by forecast
        top_stores = []
        if 'store_id' in results_df.columns and 'point_forecast' in results_df.columns:
            store_forecasts = results_df.groupby('store_id')['point_forecast'].sum().sort_values(ascending=False)
            top_stores = store_forecasts.head(5).to_dict()

        # Top SKUs by forecast
        top_skus = []
        if 'sku_id' in results_df.columns and 'point_forecast' in results_df.columns:
            sku_forecasts = results_df.groupby('sku_id')['point_forecast'].sum().sort_values(ascending=False)
            top_skus = sku_forecasts.head(5).to_dict()

        # High error items (if available)
        high_error_items = []
        if 'wmape' in results_df.columns:
            high_error = results_df[results_df['wmape'] > 0.5].head(5)
            if 'sku_id' in results_df.columns and 'store_id' in results_df.columns:
                high_error_items = high_error[['sku_id', 'store_id', 'wmape']].values.tolist()

        # Build summary - make it conversational and exciting
        summary_parts = [
            f"🎉 **Forecast Complete!**",
            f"",
            f"Just finished processing **{total_predictions:,}** predictions covering **{unique_stores}** stores and **{unique_skus}** SKUs. ",
            f"Total forecasted demand: **{total_forecast:,.0f}** units.",
        ]

        if wmape:
            summary_parts.append(f"")
            accuracy_msg = "Excellent work!" if wmape_value and wmape_value < 0.2 else "Good baseline, let's improve it with more data!"
            summary_parts.append(f"📊 **Accuracy:** WMAPE of **{wmape}** - {accuracy_msg}")

        if zero_forecasts > 0:
            summary_parts.append(f"")
            summary_parts.append(f"⚠️ **{zero_forecasts:,}** items have zero forecast (likely out of stock).")

        if model_counts:
            summary_parts.append(f"")
            summary_parts.append(f"**🤖 Models Used:**")
            for model, count in sorted(model_counts.items(), key=lambda x: -x[1])[:3]:
                pct = count / total_predictions * 100
                summary_parts.append(f"- {model}: {count:,} ({pct:.0f}%)")

        if segment_counts:
            summary_parts.append(f"")
            summary_parts.append(f"**📦 Demand Segments:**")
            for segment, count in sorted(segment_counts.items(), key=lambda x: -x[1]):
                pct = count / total_predictions * 100
                summary_parts.append(f"- {segment}: {count:,} ({pct:.0f}%)")

        if top_stores:
            summary_parts.append(f"")
            summary_parts.append(f"**🏪 Top Stores by Forecast:**")
            for store, forecast in list(top_stores.items())[:3]:
                summary_parts.append(f"- Store {store}: {forecast:,.0f} units")

        if top_skus:
            summary_parts.append(f"")
            summary_parts.append(f"**📦 Top SKUs by Forecast:**")
            for sku, forecast in list(top_skus.items())[:3]:
                summary_parts.append(f"- SKU {sku}: {forecast:,.0f} units")

        summary_parts.append(f"")
        summary_parts.append(f"---")
        summary_parts.append(f"🚀 **What's next?** Here are some things we can explore:")
        summary_parts.append(f"")
        summary_parts.append(f"- 📈 **Deep dive**: \"Show me the worst performing store-SKU combinations\"")
        summary_parts.append(f"- 🎯 **What-if**: \"What if we run a 20% promotion on SKU X at Store Y?\"")
        summary_parts.append(f"- 📊 **Risks**: \"Which items are at risk of stockout next week?\"")
        summary_parts.append(f"- 🔍 **Compare**: \"How does this compare to the previous run?\"")
        summary_parts.append(f"")
        summary_parts.append(f"Just ask me anything!")

        if segment_counts:
            summary_parts.append(f"")
            summary_parts.append(f"**Demand Segments:**")
            for segment, count in segment_counts.items():
                pct = count / total_predictions * 100
                summary_parts.append(f"- {segment}: {count} ({pct:.1f}%)")

        summary_parts.append(f"")
        summary_parts.append(f"---")
        summary_parts.append(f"Great news! Your forecast is ready. What would you like to explore next? Here are some suggestions:")
        summary_parts.append(f"- **Dive deeper**: \"Show me the worst performing SKUs\" or \"Which stores have the highest error?\"")
        summary_parts.append(f"- **What-if analysis**: \"What if we ran a 20% promotion on SKU X at Store Y?\"")
        summary_parts.append(f"- **Historical comparison**: \"How does this run compare to last week?\"")

        return "\n".join(summary_parts)

    def chat(self, messages: list, current_run_id: str = None, run_results: list = None, model_outputs: dict = None, features: pd.DataFrame = None, all_runs: dict = None) -> tuple[str, str, str, list]:
        self.pending_action = None
        self.pending_payload = None
        self.all_runs = all_runs or {}
        self.trace = []

        # Check for FORECAST_COMPLETED trigger
        latest_user_query = messages[-1]["content"] if messages else ""
        is_forecast_completed = "SYSTEM_TRIGGER: FORECAST_COMPLETED" in latest_user_query

        if run_results:
            self.current_results_df = pd.DataFrame(run_results)
            try:
                self.current_stores_df = pd.read_csv("backend/data/STORE_MASTER.csv")
                self.current_items_df = pd.read_csv("backend/data/ITEM_MASTER.csv")
            except:
                pass
            self.current_features_df = features
            self.current_model_outputs = model_outputs
        else:
            self.current_results_df = None
            self.current_stores_df = None
            self.current_items_df = None
            self.current_features_df = None
            self.current_model_outputs = None

        # Handle FORECAST_COMPLETED trigger - synthesize results directly
        if is_forecast_completed and run_results and current_run_id:
            self.trace.append({
                "type": "info",
                "agent": "supervisor",
                "name": "Forecast Complete",
                "message": "Pipeline finished! Synthesizing results..."
            })

            # Calculate metrics and generate summary
            synthesis = self.synthesize_forecast_results(run_results, current_run_id)

            # Add the synthesis summary to trace for visibility in AgentActivity
            self.trace.append({
                "type": "info",
                "agent": "supervisor",
                "name": "Results Summary",
                "message": "Forecast complete! Check the chat for detailed results."
            })

            # Store the completed run
            results_df = pd.DataFrame(run_results)
            wmape = None
            if 'wmape' in results_df.columns:
                valid_wmape = results_df['wmape'].dropna()
                if len(valid_wmape) > 0:
                    wmape = valid_wmape.mean()

            self.all_runs[current_run_id] = {
                "run_id": current_run_id,
                "status": "completed",
                "timestamp": pd.Timestamp.now().isoformat(),
                "avg_wmape": wmape,
                "total_predictions": len(results_df),
            }

            # Return synthesis immediately - no need for LLM call
            return synthesis, "FORECAST_COMPLETED", current_run_id, self.trace

        # Get analysis report if available
        analysis_report = ""
        if self.current_model_outputs and self.current_model_outputs.get("analysis_report"):
            analysis_report = self.current_model_outputs.get("analysis_report", "")
        
        supervisor_system = f"""
        You are the **Lead Forecast Supervisor**, the intelligent conductor of this Supply Chain AI. 
        Your goal is to guide the user through the forecasting lifecycle with clarity, proactivity, and professional expertise.

        Current Context:
        - Active Run ID: {current_run_id if current_run_id else "None"}
        - Data Context: {"Loaded & Ready" if self.current_results_df is not None else "Not Loaded"}
        {f"- Stats: {len(self.current_results_df)} predictions generated." if self.current_results_df is not None else ""}
        
        {f"Data Exploration Report from Pipeline: {analysis_report}" if analysis_report else ""}

        Your Personality:
        - Enthusiastic and proactive - you genuinely care about helping the user succeed.
        - Professional yet conversational - like a skilled colleague, not a robot.
        - Aware: You know exactly what's happening in the pipeline at all times.
        - Forward-thinking: Always suggest the next logical step.

        Handling Special Triggers:
        - If you receive "**SYSTEM_TRIGGER: FORECAST_COMPLETED**", it means the background pipeline just finished.
          The results have already been synthesized and presented to the user. Your job now is to:
          1. Acknowledge the completion warmly and professionally.
          2. Highlight 2-3 key insights from the results.
          3. Suggest specific, actionable next steps based on what would be most valuable.
          4. If anything looks concerning (high errors, many zero forecasts), flag it proactively.
        - If you receive "**SYSTEM_TRIGGER: RUN_LOADED**", acknowledge that the historical data is now in your active memory and summarize its key metrics. Be specific - mention WMAPE, total predictions, stores/SKUs covered.

        Your Capabilities (Use Tools!):
        - `start_new_forecast()`: Start a fresh pipeline. YOU MUST call this tool immediately if the user asks to run, start, or generate a forecast.
        - `get_historical_runs(limit)`: Browse past performance.
        - `load_historical_run(run_id)`: Bring a past run into context.
        - `analyze_data(complex_query)`: HAND OFF to the Analyst for ANY numeric, SQL, or simulation questions. DO NOT speculate on data values yourself.

        Instructions:
        1. If the user asks to start/run a forecast, you MUST call the `start_new_forecast()` tool. Do NOT just say you will do it.
        2. If a run is loaded, ALWAYS use `analyze_data` to get real numbers - never guess or estimate.
        3. Be specific with numbers - don't say "many" when you can say "247".
        4. When presenting insights, explain WHY they matter.
        5. End responses with a clear suggestion or question to keep the conversation moving.
        """

        # Format message history for GenAI SDK
        formatted_history = []
        for msg in messages[:-1]: # exclude the very last user message
            role = "user" if msg["role"] == "user" else "model"
            formatted_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        latest_user_query = messages[-1]["content"]

        try:
            # Create session without automatic tool execution
            chat_session = self.client.chats.create(
                model=self.supervisor_model,
                history=formatted_history,
                config=types.GenerateContentConfig(
                    system_instruction=supervisor_system,
                    temperature=0.3,
                )
            )
            
            tools_map = {
                "start_new_forecast": self.start_new_forecast,
                "get_historical_runs": self.get_historical_runs,
                "load_historical_run": self.load_historical_run,
                "analyze_data": self.analyze_data
            }
            
            # Send message with tools attached but automatic execution disabled by default behavior when we intercept it
            response = self.client.models.generate_content(
                model=self.supervisor_model,
                contents=formatted_history + [types.Content(role="user", parts=[types.Part.from_text(text=latest_user_query)])],
                config=types.GenerateContentConfig(
                    system_instruction=supervisor_system,
                    tools=[self.start_new_forecast, self.get_historical_runs, self.load_historical_run, self.analyze_data],
                    temperature=0.3,
                )
            )

            if response.usage_metadata:
                self.trace.append({
                    "type": "info",
                    "agent": "supervisor",
                    "message": "Supervisor reasoned next steps.",
                    "tokens": {
                        "input": response.usage_metadata.prompt_token_count,
                        "output": response.usage_metadata.candidates_token_count
                    }
                })
            
            # Manual function call loop
            while response.function_calls:
                for fn in response.function_calls:
                    fn_name = fn.name
                    fn_args = fn.args
                    
                    self.trace.append({
                        "type": "tool_call",
                        "agent": "supervisor",
                        "name": fn_name,
                        "args": {k: v for k, v in fn_args.items()} if fn_args else {}
                    })
                    
                    # Execute
                    if fn_name in tools_map:
                        try:
                            # GenAI SDK unrolls dict directly to kwargs
                            result = tools_map[fn_name](**fn_args) if fn_args else tools_map[fn_name]()
                            
                            self.trace.append({
                                "type": "tool_result",
                                "agent": "supervisor",
                                "name": fn_name,
                                "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                            })
                            
                            # Append result back to conversation
                            formatted_history.append(response.candidates[0].content)
                            formatted_history.append(
                                types.Content(
                                    role="user",
                                    parts=[types.Part.from_function_response(name=fn_name, response={"result": result})]
                                )
                            )
                        except Exception as e:
                            self.trace.append({"type": "error", "agent": "supervisor", "name": fn_name, "message": str(e)})
                            formatted_history.append(response.candidates[0].content)
                            formatted_history.append(
                                types.Content(
                                    role="user",
                                    parts=[types.Part.from_function_response(name=fn_name, response={"error": str(e)})]
                                )
                            )
                    else:
                        break # unknown tool
                
                # Send the function response back to the model
                response = self.client.models.generate_content(
                    model=self.supervisor_model,
                    contents=formatted_history,
                    config=types.GenerateContentConfig(
                        system_instruction=supervisor_system,
                        tools=[self.start_new_forecast, self.get_historical_runs, self.load_historical_run, self.analyze_data],
                        temperature=0.3,
                    )
                )

                if response.usage_metadata:
                    self.trace.append({
                        "type": "info",
                        "agent": "supervisor",
                        "message": "Supervisor processed tool results.",
                        "tokens": {
                            "input": response.usage_metadata.prompt_token_count,
                            "output": response.usage_metadata.candidates_token_count
                        }
                    })

            return response.text, self.pending_action, self.pending_payload, self.trace
            
        except Exception as e:
            self.trace.append({"type": "error", "agent": "system", "message": f"Critical Error: {str(e)}"})
            return f"System Error: {str(e)}", None, None, self.trace
