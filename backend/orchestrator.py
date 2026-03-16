import os
import pandas as pd
import logging
from google import genai
from google.genai import types
from .sandbox import execute_python

logger = logging.getLogger(__name__)

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
        # Conversation history - must follow: user, model, user, model...
        contents = []
        
        def log_progress(message: str) -> str:
            """Logs a progress or status message directly to the user's trace panel."""
            trace_call = {
                "type": "info",
                "agent": "system",
                "name": "Update",
                "message": message
            }
            self._update(self.current_progress, self.current_stage, message, trace_event=trace_call)
            return "Logged successfully."

        def execute_and_respond(fn):
            """Execute a function and return the result."""
            if fn.name == "execute_python":
                code = fn.args.get("code", "")
                result = execute_python(code)
                return "execute_python", str(result)[:5000]
            elif fn.name == "log_progress":
                message = fn.args.get("message", "")
                result = log_progress(message)
                return "log_progress", result
            else:
                return fn.name, "Unknown function"

        def handle_error_and_retry(code, max_retries=3):
            """Self-healing: retry on error up to max_retries times."""
            for retry in range(max_retries):
                trace_call = {
                    "type": "tool_call",
                    "agent": "system",
                    "name": "execute_python",
                    "args": {"code": code}
                }
                retry_msg = f"Executing Python code ({len(code)} bytes)..." + (f" (retry {retry+1})" if retry > 0 else "")
                self._update(self.current_progress, self.current_stage, retry_msg, trace_event=trace_call)
                
                import time
                start_time = time.time()
                result = execute_python(code)
                duration = time.time() - start_time
                
                is_error = result.startswith("System Error") or result.startswith("Error:") or "Traceback" in result
                
                trace_res = {
                    "type": "tool_result" if not is_error else "error",
                    "agent": "system",
                    "name": "execute_python",
                    "result": str(result)[:1000] + ("..." if len(str(result)) > 1000 else ""),
                    "message": str(result)[:1000] + ("..." if is_error else "")
                }
                status_msg = f"Python execution completed in {duration:.1f}s."
                if is_error and retry < max_retries - 1:
                    status_msg += " Retrying with fixed code..."
                self._update(self.current_progress, self.current_stage, status_msg, trace_event=trace_res)
                
                if not is_error:
                    return result
                
                if retry < max_retries - 1:
                    # Error - ask model to fix
                    error_msg = f"Error detected: {result[:1500]}\n\nFix the code and retry."
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=error_msg)]
                    ))
                    
                    fix_response = self.client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=sys_instruction,
                            tools=[execute_python, log_progress],
                            temperature=0.1,
                        )
                    )
                    
                    if fix_response.function_calls:
                        contents.append(fix_response.candidates[0].content)
                        code = fix_response.function_calls[0].args.get("code", "")
                    else:
                        break
            
            return result if 'result' in locals() else "Max retries exceeded"

        # Main loop
        for turn in range(max_turns):
            try:
                # Build message - always start with user role
                if turn == 0:
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)]
                    ))
                else:
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part.from_text(text="Proceed. If finished, return summary.")]
                    ))

                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instruction,
                        tools=[execute_python, log_progress],
                        temperature=0.1,
                    )
                )

                if response.usage_metadata:
                    self._update(self.current_progress, self.current_stage, "Agent generated response.", trace_event={
                        "type": "info",
                        "agent": "system",
                        "message": "Pipeline model execution completed.",
                        "tokens": {
                            "input": response.usage_metadata.prompt_token_count,
                            "output": response.usage_metadata.candidates_token_count
                        }
                    })

                if not response.function_calls:
                    return response.text

                # Process ONE function call at a time
                fn = response.function_calls[0]
                
                # Add model's function call to contents (must alternate: user -> model -> user)
                contents.append(response.candidates[0].content)
                
                # Execute function
                fn_name, fn_result = execute_and_respond(fn)
                
                # Send function result back as user role
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(name=fn_name, response={"result": fn_result})]
                ))

            except Exception as e:
                self._update(self.current_progress, self.current_stage, f"Agent Error: {str(e)}")
                return f"Agent failed due to error: {str(e)}"

        return "Agent hit max turns without finishing."

    def run(self):
        try:
            # Phase 1: Explorer
            self._update(5, "exploring", "🔍 PHASE 1: Starting data exploration...")
            self._update(10, "exploring", "Exploring raw data files...")
            explorer_sys = """You are an Autonomous Data Explorer. Your job is to explore the data directory and understand the data structure.

IMPORTANT - You MUST use the log_progress tool to log every step of your work:
- Before running ANY execute_python call, call log_progress with a descriptive message like "Discovering CSV files in data directory..."
- After each major finding, call log_progress like "Found 3 CSV files: sales.csv, inventory.csv, store_master.csv"
- When you discover something important, call log_progress like "Detected negative quantities in sales data - need to handle these"

Always use execute_python to run pandas scripts. Always call log_progress before execute_python."""
            explorer_prompt = f"""Look in the '{self.data_dir}' directory. 

Your tasks:
1. List all files in the directory
2. Read each file and understand its structure
3. Identify key columns (dates, quantities, IDs)
4. Note any data quality issues (negative values, missing data, etc.)

Use execute_python to explore. Use log_progress to keep the user informed at every step. Return a detailed markdown report of your findings."""
            self.analysis_report = self._call_agent(explorer_prompt, explorer_sys, self.lite_model, max_turns=6)
            
            # Check if agent failed
            if "Agent failed" in self.analysis_report or "Error" in self.analysis_report:
                raise Exception(f"Data Explorer Agent failed: {self.analysis_report}")
            
            self._update(25, "exploring", "✅ Data exploration completed.")
            
            # Phase 2: Transformer
            self._update(30, "transforming", "🔧 PHASE 2: Starting ETL pipeline...")
            self._update(35, "transforming", "Writing custom ETL scripts...")
            etl_sys = """You are an Autonomous ETL Engineer. Your job is to clean, transform, and prepare data for modeling.

IMPORTANT - You MUST use the log_progress tool to log every step:
- Before loading data: "Loading sales data from CSV..."
- Before transformations: "Applying data cleaning: handling negative quantities..."
- Before aggregations: "Aggregating daily sales to weekly level..."
- Before feature engineering: "Creating rolling window features (7-day, 14-day, 28-day)..."
- Before saving: "Saving processed features to parquet file..."

Always call log_progress before execute_python. Be descriptive about what you're doing."""
            etl_prompt = f"""Here is the data analysis:\n{self.analysis_report}\n\nWrite a Python script using execute_python to:
1. Load data from '{self.data_dir}/'
2. Clean the data (handle negatives, missing values, etc.)
3. Aggregate sales to weekly level
4. Engineer rolling features (lags, rolling means, etc.)
5. Save to '{self.features_path}'

Required output columns: combo_id, store_id, sku_id, week_start, qty_sold, and feature columns.

Use log_progress to describe each step. Save the final DataFrame to parquet format."""
            etl_summary = self._call_agent(etl_prompt, etl_sys, self.pro_model, max_turns=6)
            
            # Check if agent failed
            if "Agent failed" in str(etl_summary) or "Error" in str(etl_summary):
                raise Exception(f"ETL Agent failed: {etl_summary}")
            
            self._update(50, "transforming", "✅ ETL pipeline completed.")

            # Phase 3: Modeler
            self._update(55, "training", "🤖 PHASE 3: Starting model training...")
            self._update(60, "training", "Training models dynamically...")
            model_sys = """You are an Autonomous AutoML Agent. Your job is to train machine learning models and generate forecasts.

IMPORTANT - You MUST use log_progress to log every step:
- Before loading features: "Loading feature matrix from parquet..."
- Before training: "Training LightGBM model with X features..."
- During evaluation: "Evaluating model performance on validation set..."
- Before predictions: "Generating forecasts for next week..."
- Before saving: "Saving predictions to CSV..."

Always call log_progress before execute_python. Describe what model you're training and the metrics."""
            model_prompt = f"""Load '{self.features_path}'. Train at least one model (e.g., LightGBM) to forecast next week's sales per combo_id.

Required output columns: store_id, sku_id, combo_id, forecast_week_start, horizon, point_forecast, lower_80, upper_80, model_used, demand_segment, is_zero_forecast, wmape, mape.

Use log_progress to describe each step. Save predictions to '{self.results_path}'."""
            model_summary = self._call_agent(model_prompt, model_sys, self.pro_model, max_turns=6)
            
            # Check if agent failed
            if "Agent failed" in str(model_summary) or "Error" in str(model_summary):
                raise Exception(f"Model Agent failed: {model_summary}")
            
            self._update(85, "training", "✅ Model training completed.")

            # Phase 4: Data Finalization
            self._update(95, "finalizing", "Finalizing forecast data...")

            if os.path.exists(self.results_path):
                results_df = pd.read_csv(self.results_path)
                results = results_df.to_dict(orient="records")
            else:
                raise Exception(f"Agent failed to save results to {self.results_path}. Modeler summary: {model_summary}")

            features = pd.read_parquet(self.features_path) if os.path.exists(self.features_path) else None

            # Clean up temporary files
            try:
                if os.path.exists(self.results_path):
                    os.remove(self.results_path)
                if os.path.exists(self.features_path):
                    os.remove(self.features_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp files: {e}")

            self._update(100, "done", "Forecast complete!")
            return results, {"feature_cols": list(features.columns) if features is not None else [], "final_summary": "", "analysis_report": self.analysis_report}, features
        except Exception as e:
            self._update(self.current_progress, "failed", f"Orchestration failed: {str(e)}")
            raise e
