import os
import json
import traceback
import pandas as pd
from google import genai
from google.genai import types
from .sandbox import execute_python

class AutonomousForecaster:
    def __init__(self, run_id: str, progress_callback):
        self.run_id = run_id
        self.progress_callback = progress_callback
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))
        self.lite_model = "gemini-3.1-flash-lite-preview"
        self.pro_model = "gemini-3.1-pro-preview"
        self.data_dir = "backend/data"
        self.tmp_dir = "backend/data/tmp"
        os.makedirs(self.tmp_dir, exist_ok=True)
        self.analysis_report = ""
        self.features_path = f"{self.tmp_dir}/features_{run_id}.parquet"
        self.results_path = f"{self.tmp_dir}/results_{run_id}.csv"
        
        self.current_progress = 0
        self.current_stage = "starting"
        
    def _update(self, progress, stage, msg, trace_event=None):
        self.current_progress = progress
        self.current_stage = stage
        self.progress_callback(progress, stage, msg, trace_event)

    def _call_agent(self, prompt, sys_instruction, model, max_turns=5):
        history = []
        
        for turn in range(max_turns):
            try:
                # Add prompt to history if it's the first turn, or a continuation message
                user_msg = prompt if turn == 0 else "Proceed. If you have finished your task, please return the final text summary of what you did and do not call tools."
                
                response = self.client.models.generate_content(
                    model=model,
                    contents=history + [types.Content(role="user", parts=[types.Part.from_text(text=user_msg)])],
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instruction,
                        tools=[execute_python],
                        temperature=0.1,
                    )
                )
                
                if not response.function_calls:
                    return response.text
                
                history.append(response.candidates[0].content)
                
                function_responses = []
                for fn in response.function_calls:
                    if fn.name == "execute_python":
                        code = fn.args.get("code", "")
                        
                        trace_call = {
                            "type": "tool_call",
                            "agent": "pipeline",
                            "name": "execute_python",
                            "args": {"code": code}
                        }
                        self._update(self.current_progress, self.current_stage, f"Executing Python code ({len(code)} bytes)...", trace_event=trace_call)
                        
                        result = execute_python(code)
                        
                        trace_res = {
                            "type": "tool_result" if not result.startswith("System Error") else "error",
                            "agent": "pipeline",
                            "name": "execute_python",
                            "result": str(result)[:1000] + "..." if len(str(result)) > 1000 else str(result),
                            "message": str(result)[:1000] + "..." if result.startswith("System Error") else ""
                        }
                        self._update(self.current_progress, self.current_stage, f"Python execution completed.", trace_event=trace_res)
                        
                        function_responses.append(
                            types.Part.from_function_response(name=fn.name, response={"result": str(result)[:5000]})
                        )
                        
                if function_responses:
                    history.append(
                        types.Content(
                            role="user", 
                            parts=function_responses
                        )
                    )
                        
            except Exception as e:
                self._update(self.current_progress, self.current_stage, f"Agent Error: {str(e)}")
                return f"Agent failed due to error: {str(e)}"
        
        return "Agent hit max turns without finishing."

    def run(self):
        try:
            # Phase 1: Explorer
            self._update(10, "exploring", "Exploring raw data files...")
            explorer_sys = "You are an Autonomous Data Explorer. You use execute_python to run pandas scripts on raw data. You find schemas, primary keys, and data issues. When finished, write a final markdown summary of the data and what must be done to clean it for forecasting."
            explorer_prompt = f"Look in the '{self.data_dir}' directory. Inspect the files. Figure out how they relate. Pay attention to negative quantities, dates, and string-formatted numeric columns. Return a final markdown report of your findings."
            self.analysis_report = self._call_agent(explorer_prompt, explorer_sys, self.lite_model, max_turns=6)
            self._update(25, "exploring", "Data exploration completed.")
            
            # Phase 2: Transformer
            self._update(30, "transforming", "Writing custom ETL scripts...")
            etl_sys = "You are an Autonomous ETL Engineer. You use execute_python to write pandas code that cleans and merges data into a single feature matrix."
            etl_prompt = f"Here is the data analysis:\n{self.analysis_report}\n\nWrite a Python script using execute_python to load data from '{self.data_dir}/', clean it, aggregate sales to a weekly level, engineer basic rolling features, and save the final pandas DataFrame to '{self.features_path}'. Ensure the final dataframe has combo_id, store_id, sku_id, week_start, qty_sold, and some features."
            etl_summary = self._call_agent(etl_prompt, etl_sys, self.pro_model, max_turns=6)
            self._update(50, "transforming", "ETL pipeline completed.")

            # Phase 3: Modeler
            self._update(60, "training", "Training models dynamically...")
            model_sys = "You are an Autonomous AutoML Agent. You use execute_python to train machine learning models and save forecasts."
            model_prompt = f"Load '{self.features_path}'. Train at least one model (e.g., LightGBM) to forecast next week's sales per combo_id. \nYou MUST save the final predictions to '{self.results_path}' as a CSV with these EXACT columns: store_id, sku_id, combo_id, forecast_week_start, horizon, point_forecast, lower_80, upper_80, model_used, demand_segment, is_zero_forecast, wmape, mape. Use dummy/heuristic values if necessary for metrics (e.g. demand_segment='smooth', wmape=0.5) but the column names must match EXACTLY."
            model_summary = self._call_agent(model_prompt, model_sys, self.pro_model, max_turns=6)
            self._update(85, "training", "Model training completed.")

            # Load results
            self._update(90, "synthesizing", "Synthesizing output...")
            
            if os.path.exists(self.results_path):
                results_df = pd.read_csv(self.results_path)
                results = results_df.to_dict(orient="records")
            else:
                raise Exception(f"Agent failed to save results to {self.results_path}. Modeler summary: {model_summary}")
            
            features = pd.read_parquet(self.features_path) if os.path.exists(self.features_path) else None
            
            self._update(100, "done", "Forecast complete!")
            return results, {"feature_cols": list(features.columns) if features is not None else []}, features

        except Exception as e:
            self._update(self.current_progress, "failed", f"Orchestration failed: {str(e)}")
            raise e
