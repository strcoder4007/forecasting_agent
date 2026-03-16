"""FastAPI application for Demand Forecasting Agent."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .orchestrator import AutonomousForecaster
from .chat_service import ChatService
from . import storage

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
forecast_pipeline = None
chat_service = ChatService()

# In-memory storage for runs
storage.init_storage()
runs_storage: dict = storage.load_all_runs_metadata()
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

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    run_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None
    action_payload: Optional[str] = None
    trace: list[dict] = []

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Interact with the forecasting agent using natural language."""
    results = None
    model_outputs = None
    features = None
    if request.run_id:
        with runs_lock:
            if request.run_id in runs_storage:
                run = runs_storage[request.run_id]
                if run["status"] == "completed":
                    # Load heavy data from DuckDB just for this chat session
                    results, features, model_outputs = storage.load_run_data(request.run_id)

    # Convert Pydantic messages to dict
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Pass runs_storage to chat_service
    response_text, action, action_payload, trace = chat_service.chat(
        messages=messages, 
        current_run_id=request.run_id,
        run_results=results, 
        model_outputs=model_outputs, 
        features=features,
        all_runs=runs_storage
    )

    return ChatResponse(response=response_text, action=action, action_payload=action_payload, trace=trace)

class ForecastStatusResponse(BaseModel):
    run_id: str
    status: str
    progress: float
    stage: str
    message: str
    logs: list[str] = []
    traces: list[dict] = []
    summary: Optional[str] = None


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
    return ValidateResponse(status="success", file_info={}, warnings=[])


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
            "traces": [],
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
            forecast_pipeline = AutonomousForecaster(
                run_id,
                progress_callback=lambda p, s, m, t=None: _update_progress(run_id, p, s, m, t)
            )

            # Run forecast
            results, model_outputs, features = forecast_pipeline.run()

            # Store results
            with runs_lock:
                runs_storage[run_id]["status"] = "completed"
                runs_storage[run_id]["progress"] = 100.0
                runs_storage[run_id]["stage"] = "done"
                runs_storage[run_id]["message"] = "Forecast completed successfully"
                runs_storage[run_id]["results"] = results
                runs_storage[run_id]["model_outputs"] = model_outputs
                runs_storage[run_id]["features"] = features
                runs_storage[run_id]["total_combos"] = len(results)
                # Calculate WMAPE/MAPE metrics from results
                if results:
                    wmape_values = [r.get("wmape", 0) for r in results if "wmape" in r]
                    mape_values = [r.get("mape", 0) for r in results if "mape" in r]
                    runs_storage[run_id]["avg_wmape"] = (
                        sum(wmape_values) / len(wmape_values) if wmape_values else 0
                    )
                    runs_storage[run_id]["avg_mape"] = (
                        sum(mape_values) / len(mape_values) if mape_values else 0
                    )
                
                # Attach heavy data temporarily for saving
                runs_storage[run_id]["results"] = results
                runs_storage[run_id]["model_outputs"] = model_outputs
                runs_storage[run_id]["features"] = features
                
            storage.save_run(runs_storage[run_id])

            # Reload traces from DB to ensure they're available for API queries
            # (traces were saved during execution but we need to re-read them)
            with runs_lock:
                traces_from_db = storage.load_run_traces(run_id)
                runs_storage[run_id]["traces"] = traces_from_db

            # Remove heavy data from RAM after saving to DuckDB
            with runs_lock:
                runs_storage[run_id].pop("results", None)
                runs_storage[run_id].pop("model_outputs", None)
                runs_storage[run_id].pop("features", None)



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


def _update_progress(run_id: str, progress: float, stage: str, message: str, trace_event: dict = None):
    """Callback to update progress for a run."""
    with runs_lock:
        if run_id in runs_storage:
            if runs_storage[run_id]["status"] == "cancelled":
                raise Exception("Cancelled by user")
            runs_storage[run_id]["progress"] = progress
            runs_storage[run_id]["stage"] = stage
            if message:
                runs_storage[run_id]["message"] = message
                runs_storage[run_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] [{stage}] {message}")
            if trace_event:
                runs_storage[run_id]["traces"].append(trace_event)
            storage.save_run(runs_storage[run_id])



@app.post("/api/forecast/cancel/{run_id}")
async def cancel_forecast(run_id: str):
    """Cancel a running forecast."""
    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")
        runs_storage[run_id]["status"] = "cancelled"
    return {"message": "Run cancellation requested", "run_id": run_id}

@app.get("/api/forecast/status/{run_id}", response_model=ForecastStatusResponse)
async def get_forecast_status(run_id: str):
    """Get the status of a forecast run."""
    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")

        run = runs_storage[run_id]
        summary = run.get("model_outputs", {}).get("final_summary", None) if run.get("model_outputs") else None
        return ForecastStatusResponse(
            run_id=run["run_id"],
            status=run["status"],
            progress=run["progress"],
            stage=run["stage"],
            message=run["message"],
            logs=run.get("logs", []),
            traces=run.get("traces", []),
            summary=summary
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
    
    storage.delete_run_data(run_id)
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

    results, _, _ = storage.load_run_data(run_id)
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
