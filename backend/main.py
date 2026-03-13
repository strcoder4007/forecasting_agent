"""FastAPI application for Demand Forecasting Agent."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .data_loader import DataLoader, DataLoadError
from .forecast_pipeline import ForecastPipeline

# Initialize FastAPI app
app = FastAPI(title="Demand Forecasting Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
data_loader = DataLoader()
forecast_pipeline: Optional[ForecastPipeline] = None

# In-memory storage for runs
runs_storage: dict = {}
runs_lock = threading.Lock()

# Define data directory
DATA_DIR = Path(__file__).parent / "data"


# Pydantic models
class ValidateResponse(BaseModel):
    status: str
    file_info: dict
    warnings: list


class RunForecastResponse(BaseModel):
    run_id: str
    status: str


class ForecastStatusResponse(BaseModel):
    run_id: str
    status: str
    progress: float
    stage: str
    message: str
    logs: list[str] = []


class HistoryItem(BaseModel):
    run_id: str
    timestamp: str
    status: str
    total_combos: int
    avg_wmape: float
    avg_mape: float


class HistoryResponse(BaseModel):
    runs: list[HistoryItem]


@app.get("/")
async def root():
    return {"message": "Demand Forecasting Agent API", "version": "1.0.0"}


@app.get("/api/data/validate", response_model=ValidateResponse)
async def validate_data():
    """Validate data files from /data folder."""
    try:
        result = data_loader.validate_files()
        return ValidateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/forecast/run", response_model=RunForecastResponse)
async def run_forecast():
    """Trigger a new forecast run."""
    global forecast_pipeline, runs_storage

    run_id = str(uuid.uuid4())

    # Initialize run
    with runs_lock:
        runs_storage[run_id] = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "progress": 0.0,
            "stage": "initializing",
            "message": "Initializing forecast run",
            "total_combos": 0,
            "avg_wmape": 0.0,
            "avg_mape": 0.0,
            "results": None,
            "error": None,
            "logs": [],
        }

    # Start forecast in background thread
    def run_forecast_thread():
        global forecast_pipeline
        try:
            # Update status
            with runs_lock:
                runs_storage[run_id]["status"] = "running"
                runs_storage[run_id]["stage"] = "loading_data"
                runs_storage[run_id]["message"] = "Loading and validating data"

            # Initialize pipeline
            forecast_pipeline = ForecastPipeline(data_loader)

            # Run forecast
            results = forecast_pipeline.run(
                progress_callback=lambda p, s, m: _update_progress(run_id, p, s, m)
            )

            # Store results
            with runs_lock:
                runs_storage[run_id]["status"] = "completed"
                runs_storage[run_id]["progress"] = 100.0
                runs_storage[run_id]["stage"] = "done"
                runs_storage[run_id]["message"] = "Forecast completed successfully"
                runs_storage[run_id]["results"] = results
                runs_storage[run_id]["total_combos"] = len(results)
                if results:
                    wmape_values = [r.get("wmape", 0) for r in results if "wmape" in r]
                    mape_values = [r.get("mape", 0) for r in results if "mape" in r]
                    runs_storage[run_id]["avg_wmape"] = (
                        sum(wmape_values) / len(wmape_values) if wmape_values else 0
                    )
                    runs_storage[run_id]["avg_mape"] = (
                        sum(mape_values) / len(mape_values) if mape_values else 0
                    )

        except DataLoadError as e:
            with runs_lock:
                runs_storage[run_id]["status"] = "failed"
                runs_storage[run_id]["error"] = str(e)
                runs_storage[run_id]["message"] = f"Data error: {str(e)}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            with runs_lock:
                runs_storage[run_id]["status"] = "failed"
                runs_storage[run_id]["error"] = repr(e)
                runs_storage[run_id]["message"] = f"Unexpected error ({type(e).__name__}): {str(e)}"

    thread = threading.Thread(target=run_forecast_thread, daemon=True)
    thread.start()

    return RunForecastResponse(run_id=run_id, status="started")


def _update_progress(run_id: str, progress: float, stage: str, message: str):
    """Update progress for a run."""
    with runs_lock:
        if run_id in runs_storage:
            runs_storage[run_id]["progress"] = progress
            runs_storage[run_id]["stage"] = stage
            runs_storage[run_id]["message"] = message
            timestamp = datetime.now().strftime("%H:%M:%S")
            runs_storage[run_id]["logs"].append(f"[{timestamp}] [{stage}] {message}")


@app.get("/api/forecast/status/{run_id}", response_model=ForecastStatusResponse)
async def get_forecast_status(run_id: str):
    """Get the status of a forecast run."""
    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")

        run = runs_storage[run_id]
        return ForecastStatusResponse(
            run_id=run["run_id"],
            status=run["status"],
            progress=run["progress"],
            stage=run["stage"],
            message=run["message"],
            logs=run.get("logs", []),
        )


@app.get("/api/forecast/results/{run_id}")
async def get_forecast_results(run_id: str):
    """Get forecast results for a completed run."""
    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")

        run = runs_storage[run_id]
        if run["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Run not completed yet. Status: {run['status']}",
            )

        results = run.get("results", [])
        if not results:
            return {"rows": [], "count": 0}

        return {"rows": results, "count": len(results)}


@app.get("/api/history", response_model=HistoryResponse)
async def get_history():
    """Get history of all forecast runs."""
    with runs_lock:
        runs = [
            HistoryItem(
                run_id=r["run_id"],
                timestamp=r["timestamp"],
                status=r["status"],
                total_combos=r.get("total_combos", 0),
                avg_wmape=r.get("avg_wmape", 0.0),
                avg_mape=r.get("avg_mape", 0.0),
            )
            for r in runs_storage.values()
        ]
        # Sort by timestamp descending
        runs.sort(key=lambda x: x.timestamp, reverse=True)
        return HistoryResponse(runs=runs)


@app.get("/api/history/{run_id}")
async def get_history_item(run_id: str):
    """Get details of a specific run."""
    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")

        run = runs_storage[run_id]
        return {
            "run_id": run["run_id"],
            "timestamp": run["timestamp"],
            "status": run["status"],
            "stage": run["stage"],
            "message": run["message"],
            "total_combos": run.get("total_combos", 0),
            "avg_wmape": run.get("avg_wmape", 0.0),
            "avg_mape": run.get("avg_mape", 0.0),
            "error": run.get("error"),
        }


@app.delete("/api/history/{run_id}")
async def delete_run(run_id: str):
    """Delete a forecast run."""
    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")

        del runs_storage[run_id]
        return {"message": "Run deleted successfully", "run_id": run_id}


@app.get("/api/export/{run_id}")
async def export_forecast(run_id: str):
    """Export forecast results as CSV."""
    import csv
    from fastapi.responses import StreamingResponse

    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")

        run = runs_storage[run_id]
        if run["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Run not completed yet. Status: {run['status']}",
            )

        results = run.get("results", [])
        if not results:
            raise HTTPException(status_code=404, detail="No results to export")

    # Generate CSV
    def generate_csv():
        if results:
            # Header
            yield ",".join(results[0].keys()) + "\n"
            # Rows
            for row in results:
                yield ",".join(str(v) for v in row.values()) + "\n"

    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=forecast_{run_id}.csv"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
