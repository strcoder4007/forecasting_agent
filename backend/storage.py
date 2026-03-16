import duckdb
import os
import joblib
import pandas as pd
import threading
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "forecasts.duckdb")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "data", "models")

# We use a global lock for DuckDB writes just to be safe with concurrent API requests
db_lock = threading.Lock()

def init_storage():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with db_lock:
        conn = duckdb.connect(DB_PATH)
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
                error VARCHAR
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
        conn.close()

def save_run(run_dict):
    """Saves run metadata, logs, and optionally heavy data if completed."""
    with db_lock:
        conn = duckdb.connect(DB_PATH)
        try:
            # upsert run metadata
            conn.execute("""
                INSERT INTO runs 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (run_id) DO UPDATE SET
                    status=EXCLUDED.status,
                    progress=EXCLUDED.progress,
                    stage=EXCLUDED.stage,
                    message=EXCLUDED.message,
                    total_combos=EXCLUDED.total_combos,
                    avg_wmape=EXCLUDED.avg_wmape,
                    avg_mape=EXCLUDED.avg_mape,
                    error=EXCLUDED.error
            """, [
                run_dict["run_id"], run_dict["timestamp"], run_dict["status"],
                run_dict["progress"], run_dict["stage"], run_dict["message"],
                run_dict.get("total_combos", 0), run_dict.get("avg_wmape", 0.0),
                run_dict.get("avg_mape", 0.0), run_dict.get("error", None)
            ])
            
            # Save logs (simplest way is delete and re-insert)
            conn.execute("DELETE FROM run_logs WHERE run_id=?", [run_dict["run_id"]])
            for log in run_dict.get("logs", []):
                conn.execute("INSERT INTO run_logs VALUES (?, ?)", [run_dict["run_id"], log])
                
            # Save traces
            conn.execute("DELETE FROM run_traces WHERE run_id=?", [run_dict["run_id"]])
            for trace in run_dict.get("traces", []):
                conn.execute("INSERT INTO run_traces VALUES (?, ?)", [run_dict["run_id"], json.dumps(trace)])
                
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
        finally:
            conn.close()

def load_all_runs_metadata():
    """Loads all run metadata and logs from DuckDB into memory."""
    runs = {}
    with db_lock:
        if not os.path.exists(DB_PATH):
            return runs
            
        conn = duckdb.connect(DB_PATH)
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
                runs[run_id]["traces"] = [json.loads(t) for t in traces_df["trace_json"].tolist()]
        finally:
            conn.close()
    return runs

def load_run_data(run_id):
    """Loads heavy DataFrames and Models on demand."""
    results = []
    features = None
    model_outputs = {}
    
    with db_lock:
        conn = duckdb.connect(DB_PATH)
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
        finally:
            conn.close()
            
    return results, features, model_outputs

def delete_run_data(run_id):
    """Deletes all data associated with a run."""
    with db_lock:
        conn = duckdb.connect(DB_PATH)
        try:
            conn.execute("DELETE FROM runs WHERE run_id=?", [run_id])
            conn.execute("DELETE FROM run_logs WHERE run_id=?", [run_id])
            conn.execute("DELETE FROM run_traces WHERE run_id=?", [run_id])
            res_table = f"results_{run_id.replace('-', '_')}"
            feat_table = f"features_{run_id.replace('-', '_')}"
            conn.execute(f"DROP TABLE IF EXISTS {res_table}")
            conn.execute(f"DROP TABLE IF EXISTS {feat_table}")
        finally:
            conn.close()
        
        model_path = os.path.join(MODELS_DIR, f"{run_id}.joblib")
        if os.path.exists(model_path):
            os.remove(model_path)