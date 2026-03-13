# Demand Forecasting Agent

A machine learning-powered demand forecasting system built with FastAPI and Vue.js, featuring an integrated autonomous Two-Tier AI Chatbot. The system processes sales and stock data to generate accurate demand forecasts and allows users to query, analyze, and simulate data entirely through natural language.

## Features

- **Autonomous AI Chatbot (Two-Tier Architecture)**:
  - **Tier 1 (Supervisor)**: Fast conversational intent router that manages memory, context, and automates starting/loading runs.
  - **Tier 2 (Data Analyst)**: Advanced AI agent that writes DuckDB SQL queries against the pipeline's memory and simulates promotional scenarios on the fly.
- **Data Validation**: Validates sales, stock, item, and store master data files
- **Multi-Stage Pipeline**: Weekly aggregation, false-zero correction, demand segmentation
- **Advanced Feature Engineering**: Includes Categorical Target Encoding, Poisson-optimized models, and real promotional signals (`is_promotional`, `promo_depth`).
- **Segment-Based Model Routing**: Dynamically evaluates and routes predictions between Seasonal Naive, Ridge Regression, XGBoost, and LightGBM based on the lowest WMAPE per demand segment.
- **REST API**: Full REST API for running forecasts, querying chat, and retrieving results.
- **Real-Time Execution Logs**: Granular progress tracking rendered natively as message bubbles inside the chat interface.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python 3.12 |
| ML/Data | pandas, numpy, scikit-learn, LightGBM, XGBoost, scipy, DuckDB |
| LLM | Google GenAI SDK (`gemini-3.1-flash-lite-preview`, `gemini-3.1-pro-preview`) |
| Frontend | Vue.js 3, Vite |
| Database | IndexedDB (Client-side cache), DuckDB (In-memory SQL) |

## Project Structure

```
forecasting_agent/
├── backend/
│   ├── main.py              # FastAPI application & API endpoints
│   ├── chat_service.py      # Two-Tier Agent logic & tool calling
│   ├── data_loader.py       # Data loading and validation
│   ├── forecast_pipeline.py # Core forecasting ML logic
│   └── data/               # Data files (CSV/Excel)
├── frontend/               # Vue.js frontend
├── requirements.txt        # Python dependencies
└── README.md
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- A Google Gemini API Key

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Export your API Key and run the backend server:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   uvicorn backend.main:app --reload --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## The Chat Interface

The primary way to interact with the application is through the **AI Chat Agent** on the main page.

### Questions It Can Answer

**1. Direct Demand & Inventory Planning**
- "What is the forecasted demand for SKU X in Store Y next week?"
- "Which 10 stores are expected to sell the most of SKU X next week?"
- "What is the worst-case scenario for SKU X in the North region?"

**2. Stockout & Overstock Risk**
- "Which products have a forecast of 0 next week because they've been out of stock for too long?"
- "Show me items where the forecasted demand is significantly higher than our current stock-on-hand."

**3. "What-If" Promotional Simulations**
- "If I discount SKU X by 20% in Store Y next week, what is the new forecast?"

**4. Supply Chain & Pattern Analysis**
- "Break down our total forecasted sales for next week by Store Grade."
- "Which region has the highest concentration of 'lumpy' demand products?"

## License

MIT
