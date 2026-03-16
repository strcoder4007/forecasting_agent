import duckdb
import os
import joblib
import pandas as pd
import threading
import json
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "forecasts.duckdb")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "data", "models")

# We use a global lock for DuckDB writes just to be safe with concurrent API requests
db_lock = threading.Lock()

# Global DuckDB connection
_conn: Optional[duckdb.DuckDBPyConnection] = None

def get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        _conn = duckdb.connect(DB_PATH)
    return _conn

def init_storage() -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with db_lock:
        conn = get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id VARCHAR PRIMARY KEY,
                timestamp VARCHAR,
                status VARCHAR,
                progress DOUBLE,
                stage VARCHAR,
                message VARCHAR,
                total_combos INTEGER,
                avg_wmape DOUBLE,
                avg_mape DOUBLE,
                error VARCHAR,
                analysis_report VARCHAR
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS run_logs (
                run_id VARCHAR,
                log_message VARCHAR
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS run_traces (
                run_id VARCHAR,
                trace_json VARCHAR
            )
        """)

def save_run(run_dict: Dict[str, Any]) -> None:
    """Saves run metadata, logs, and optionally heavy data if completed."""
    with db_lock:
        conn = get_conn()
        try:
            # upsert run metadata
            conn.execute("""
                INSERT INTO runs 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (run_id) DO UPDATE SET
                    status=EXCLUDED.status,
                    progress=EXCLUDED.progress,
                    stage=EXCLUDED.stage,
                    message=EXCLUDED.message,
                    total_combos=EXCLUDED.total_combos,
                    avg_wmape=EXCLUDED.avg_wmape,
                    avg_mape=EXCLUDED.avg_mape,
                    error=EXCLUDED.error,
                    analysis_report=EXCLUDED.analysis_report
            """, [
                run_dict["run_id"], run_dict["timestamp"], run_dict["status"],
                run_dict["progress"], run_dict["stage"], run_dict["message"],
                run_dict.get("total_combos", 0), run_dict.get("avg_wmape", 0.0),
                run_dict.get("avg_mape", 0.0), run_dict.get("error", None),
                run_dict.get("analysis_report", None)
            ])
            
            # Save logs (simplest way is delete and re-insert)
            conn.execute("DELETE FROM run_logs WHERE run_id=?", [run_dict["run_id"]])
            for log in run_dict.get("logs", []):
                conn.execute("INSERT INTO run_logs VALUES (?, ?)", [run_dict["run_id"], log])
                
            # Save traces
            conn.execute("DELETE FROM run_traces WHERE run_id=?", [run_dict["run_id"]])
            traces = run_dict.get("traces", [])
            logger.info(f"[STORAGE] Saving {len(traces)} traces for run {run_dict['run_id'][:8]}")
            for trace in traces:
                try:
                    conn.execute("INSERT INTO run_traces VALUES (?, ?)", [run_dict["run_id"], json.dumps(trace)])
                except Exception as e:
                    logger.error(f"[STORAGE] Error saving trace: {e}")
                    logger.error(f"[STORAGE] Trace: {trace}")
                
            # If completed, save heavy data
            if run_dict["status"] == "completed":
                if run_dict.get("results"):
                    results_df = pd.DataFrame(run_dict["results"])
                    table_name = f"results_{run_dict['run_id'].replace('-', '_')}"
                    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM results_df")
                    
                if run_dict.get("features") is not None:
                    features_df = run_dict["features"]
                    table_name = f"features_{run_dict['run_id'].replace('-', '_')}"
                    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM features_df")
                    
                if run_dict.get("model_outputs"):
                    joblib.dump(run_dict["model_outputs"], os.path.join(MODELS_DIR, f"{run_dict['run_id']}.joblib"))
        except Exception as e:
            logger.error(f"[STORAGE] Error saving run: {e}")

def load_all_runs_metadata() -> Dict[str, Any]:
    """Loads all run metadata and logs from DuckDB into memory."""
    runs = {}
    with db_lock:
        if not os.path.exists(DB_PATH):
            return runs
            
        conn = get_conn()
        try:
            # Check if table exists
            has_table = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='runs'").fetchone()[0] > 0
            if not has_table:
                return runs
                
            df = conn.execute("SELECT * FROM runs").df()
            for _, row in df.iterrows():
                run_id = row["run_id"]
                runs[run_id] = row.to_dict()
                
                # Deal with pandas nan to None
                for k, v in runs[run_id].items():
                    if pd.isna(v):
                        runs[run_id][k] = None
                
                # Load logs
                logs_df = conn.execute("SELECT log_message FROM run_logs WHERE run_id=?", [run_id]).df()
                runs[run_id]["logs"] = logs_df["log_message"].tolist()
                
                # Load traces
                traces_df = conn.execute("SELECT trace_json FROM run_traces WHERE run_id=?", [run_id]).df()
                traces = [json.loads(t) for t in traces_df["trace_json"].tolist()] if len(traces_df) > 0 else []
                runs[run_id]["traces"] = traces
                if traces:
                    logger.info(f"[STORAGE] Loaded {len(traces)} traces for run {run_id[:8]}")
        except Exception as e:
            logger.error(f"[STORAGE] Error loading runs metadata: {e}")
            
    return runs

def load_run_data(run_id: str) -> Tuple[List[Dict[str, Any]], Optional[pd.DataFrame], Dict[str, Any]]:
    """Loads heavy DataFrames and Models on demand."""
    results = []
    features = None
    model_outputs = {}
    
    with db_lock:
        conn = get_conn()
        try:
            res_table = f"results_{run_id.replace('-', '_')}"
            if conn.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name='{res_table}'").fetchone()[0] > 0:
                results = conn.execute(f"SELECT * FROM {res_table}").df().to_dict('records')
                
            feat_table = f"features_{run_id.replace('-', '_')}"
            if conn.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name='{feat_table}'").fetchone()[0] > 0:
                features = conn.execute(f"SELECT * FROM {feat_table}").df()
                
            model_path = os.path.join(MODELS_DIR, f"{run_id}.joblib")
            if os.path.exists(model_path):
                model_outputs = joblib.load(model_path)
        except Exception as e:
            logger.error(f"[STORAGE] Error loading data for run {run_id}: {e}")
            
    return results, features, model_outputs

def load_run_traces(run_id: str) -> List[Dict[str, Any]]:
    """Load traces for a specific run from DuckDB."""
    traces = []
    with db_lock:
        conn = get_conn()
        try:
            traces_df = conn.execute("SELECT trace_json FROM run_traces WHERE run_id=?", [run_id]).df()
            if len(traces_df) > 0:
                traces = [json.loads(t) for t in traces_df["trace_json"].tolist()]
        except Exception as e:
            logger.error(f"[STORAGE] Error loading traces for run {run_id}: {e}")
            
    return traces

def delete_run_data(run_id: str) -> None:
    """Deletes all data associated with a run."""
    with db_lock:
        conn = get_conn()
        try:
            conn.execute("DELETE FROM runs WHERE run_id=?", [run_id])
            conn.execute("DELETE FROM run_logs WHERE run_id=?", [run_id])
            conn.execute("DELETE FROM run_traces WHERE run_id=?", [run_id])
            res_table = f"results_{run_id.replace('-', '_')}"
            feat_table = f"features_{run_id.replace('-', '_')}"
            conn.execute(f"DROP TABLE IF EXISTS {res_table}")
            conn.execute(f"DROP TABLE IF EXISTS {feat_table}")
        except Exception as e:
            logger.error(f"[STORAGE] Error deleting run data for {run_id}: {e}")

    model_path = os.path.join(MODELS_DIR, f"{run_id}.joblib")
    if os.path.exists(model_path):
        os.remove(model_path)
