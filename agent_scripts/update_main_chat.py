import re

with open('backend/main.py', 'r') as f:
    content = f.read()

# Add imports
import_str = "from .forecast_pipeline import ForecastPipeline\nfrom .chat_service import ChatService"
content = content.replace("from .forecast_pipeline import ForecastPipeline", import_str)

# Initialize chat service
global_str = "forecast_pipeline: Optional[ForecastPipeline] = None\nchat_service = ChatService(data_loader)"
content = content.replace("forecast_pipeline: Optional[ForecastPipeline] = None", global_str)

# Add Pydantic Models
models_str = """class RunForecastResponse(BaseModel):
    run_id: str
    status: str

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
"""
content = content.replace("class RunForecastResponse(BaseModel):\n    run_id: str\n    status: str", models_str)

# Add route
route_str = """
@app.post("/api/chat/{run_id}", response_model=ChatResponse)
async def chat_with_agent(run_id: str, request: ChatRequest):
    \"\"\"Interact with the forecasting agent using natural language.\"\"\"
    with runs_lock:
        if run_id not in runs_storage:
            raise HTTPException(status_code=404, detail="Run not found")
        run = runs_storage[run_id]
        if run["status"] != "completed":
            raise HTTPException(status_code=400, detail="Run not completed yet.")
        results = run.get("results", [])
    
    response_text = chat_service.chat(request.query, results)
    return ChatResponse(response=response_text)

"""

if "@app.post(\"/api/chat/{run_id}\"" not in content:
    # Append route before if __name__ == "__main__":
    content = content.replace('if __name__ == "__main__":', route_str + '\nif __name__ == "__main__":')

with open('backend/main.py', 'w') as f:
    f.write(content)
