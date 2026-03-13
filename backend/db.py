import duckdb
import os
import json
import pandas as pd

DB_PATH = "backend/data/forecasts.duckdb"

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return duckdb.connect(DB_PATH)

def init_db():
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
        CREATE TABLE IF NOT EXISTS results (
            run_id VARCHAR,
            store_id VARCHAR,
            sku_id VARCHAR,
            combo_id VARCHAR,
            forecast_week_start TIMESTAMP,
            horizon INTEGER,
            point_forecast DOUBLE,
            lower_80 DOUBLE,
            upper_80 DOUBLE,
            model_used VARCHAR,
            demand_segment VARCHAR,
            is_zero_forecast INTEGER,
            wmape DOUBLE,
            mape DOUBLE
        )
    """)
    conn.close()

init_db()
