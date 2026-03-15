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
        return f"System instructed to load run {run_id}."

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

        analyst_system = """
        You are an expert Data Analyst AI. Your job is to answer the user's question by querying data.
        
        Available Data (use execute_sql tool):
        - results_df: point_forecast, lower_80, upper_80, model_used, demand_segment, is_zero_forecast, wmape, mape, store_id, sku_id.
        - stores_df: store_id, cluster_label, region.
        - items_df: sku_id, category, price.
        
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
            
            return response.text
        except Exception as e:
            self.trace.append({"type": "error", "agent": "analyst", "name": "analyze_data", "message": str(e)})
            return f"Analyst Error: {str(e)}"

    def chat(self, messages: list, current_run_id: str = None, run_results: list = None, model_outputs: dict = None, features: pd.DataFrame = None, all_runs: dict = None) -> tuple[str, str, str, list]:
        self.pending_action = None
        self.pending_payload = None
        self.all_runs = all_runs or {}
        self.trace = []
        
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

        supervisor_system = f"""
        You are the Supervisor of a Supply Chain Forecasting Agent.
        
        Current Context:
        - Active Run Loaded: {"Yes (" + current_run_id + ")" if current_run_id else "No"}
        - Data Loaded: {"Yes" if self.current_results_df is hasattr(self, 'current_results_df') and self.current_results_df is not None else "No"}
        
        Your Capabilities (Use Tools!):
        - `start_new_forecast()`: Run this if the user wants to generate a new forecast.
        - `get_historical_runs(limit)`: Check memory to see past forecasts if the user asks about history.
        - `load_historical_run(run_id)`: Load a specific past forecast into context.
        - `analyze_data(complex_query)`: If the user asks a specific question about the data, trends, numbers, or a "what-if" scenario, YOU MUST hand it off by calling this tool with their question. Do NOT guess the answer.
        
        Instructions:
        1. Maintain conversation context based on history.
        2. If they are vague (e.g. "load previous"), use `get_historical_runs`, look at the IDs, and then ask them which one, or just load the most recent one autonomously.
        3. Once a tool returns, synthesize a friendly response. 
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

            return response.text, self.pending_action, self.pending_payload, self.trace
            
        except Exception as e:
            self.trace.append({"type": "error", "agent": "system", "message": f"Critical Error: {str(e)}"})
            return f"System Error: {str(e)}", None, None, self.trace
