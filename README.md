# Demand Forecasting Agent

A machine learning-powered demand forecasting system built with FastAPI and Vue.js. The system processes sales and stock data to generate accurate demand forecasts using ensemble modeling techniques.

## Features

- **Data Validation**: Validates sales, stock, item, and store master data files
- **Multi-Stage Pipeline**: Weekly aggregation, false-zero correction, demand segmentation
- **Advanced Feature Engineering**: Includes Categorical Target Encoding on `combo_id` to memorize baseline volume and utilizes actual pricing and promotional markdown (`discount_pct`) signals
- **Segment-Based Model Routing**: Dynamically evaluates and routes predictions between Seasonal Naive, Ridge Regression (lsqr), and LightGBM based on the lowest WMAPE per demand segment (Smooth, Intermittent, Lumpy)
- **Confidence Intervals**: Provides 80% confidence bounds for forecasts
- **REST API**: Full REST API for running forecasts and retrieving results
- **Real-Time Execution Logs**: Granular progress tracking and detailed execution logs streamed to the UI
- **Offline Storage & Export**: Forecast results are cached locally in the browser using IndexedDB for lightning-fast reads and purely client-side CSV exports

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python 3.12 |
| ML/Data | pandas, numpy, scikit-learn, LightGBM, scipy |
| Frontend | Vue.js 3, Vite |
| API | RESTful endpoints |

## Project Structure

```
forecasting_agent/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── data_loader.py       # Data loading and validation
│   ├── forecast_pipeline.py # Core forecasting logic
│   └── data/               # Data files (CSV/Excel)
├── frontend/               # Vue.js frontend
├── requirements.txt        # Python dependencies
└── README.md
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+

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

3. Run the backend server:
   ```bash
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

## Data Files

The application expects the following data files in `backend/data/`:

| File | Description |
|------|-------------|
| `SALES_MASTER.xls` | Sales transaction data |
| `SOH_MASTER.xls` | Stock on hand data |
| `ITEM_MASTER.xls` | Item/SKU master data |
| `STORE_MASTER.csv` | Store master data |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API health check |
| `/api/data/validate` | GET | Validate data files |
| `/api/forecast/run` | POST | Start a new forecast run |
| `/api/forecast/status/{run_id}` | GET | Get forecast run status |
| `/api/forecast/results/{run_id}` | GET | Get forecast results |
| `/api/history` | GET | Get forecast run history |
| `/api/export/{run_id}` | GET | Export results as CSV |

## Forecasting Pipeline

The pipeline processes all ~48,000 SKU-store combinations without arbitrary limits and consists of 8 stages:

| Stage | Progress | Description |
|-------|----------|-------------|
| 1 | 5% | Data Loading - Load and validate data files |
| 2 | 15% | Weekly Aggregation - Aggregate daily data to weekly (Monday start) |
| 3 | 25% | False-Zero Correction - Identify and correct stock-outs mislabeled as zero demand |
| 4 | 35% | Demand Segmentation - Classify demand patterns (smooth, intermittent, lumpy) |
| 5 | 45% | Feature Engineering - Compute 12 features per combo-week including actual prices, discount percentages, and Categorical Target Encoding |
| 6 | 60% | Model Training - Train Ridge and LightGBM models with walk-forward validation |
| 7 | 80% | Inference & Routing - Evaluate WMAPE per segment and dynamically route to the best model (Naive, Ridge, or LGBM) |
| 8 | 100% | Finalization - Apply post-processing (zero-forecast gate, ROS blend) |

## Questions It Can Answer

### 1. Direct Demand & Inventory Planning

- "What is the forecasted demand for SKU X in Store Y next week?"
- "Which 10 stores are expected to sell the most of SKU X next week?"
- "Show me all SKUs in the 'Beverages' category that are forecasted to sell more than 100 units next week."
- "What is the worst-case scenario (lower 80% confidence interval) for SKU X in the North region?"

### 2. Stockout & Overstock Risk (The "Zero-Forecast" Gate)

Because we implemented the `is_zero_forecast` flag and false-zero correction based on SOH (Stock on Hand), the bot can identify inventory anomalies.

- "Which products have a forecast of 0 next week because they've been out of stock for too long?"
- "Show me items where the forecasted demand is significantly higher than our current stock-on-hand."
- "Are there any 'smooth' demand items that are currently out of stock?"

### 3. Pricing & Promotional Insights

Since we added the `is_promotional`, `promo_depth`, and `promo_lag1` features, the bot could analyze how discounts impact the forecast.

- "Which products saw the biggest sales spike during last week's 20% promotion?"
- "Show me the forecast for items that are currently on a 'high depth' discount."
- "Are there any lumpy demand items that only sell when they are on promotion?"

### 4. Supply Chain & Pattern Analysis

Using the demand_segment (smooth, lumpy, intermittent) and store metadata (cluster_label, region), analysts can query broader macro trends.

- "Break down our total forecasted sales for next week by Store Grade (cluster_label)."
- "What percentage of our catalog in the West region is classified as 'intermittent' demand?"
- "Which region has the highest concentration of 'lumpy' demand products?"

### 5. Model Explainability & Trust

Users often distrust AI forecasts if they don't understand them. The bot can use the metrics we added (`model_used`, `wmape`, `mape`) to build trust.

- "How accurate is the forecast for this category overall?" (Can quote the Validation WMAPE/MAPE)
- "Why did the system predict 0 for SKU X?" (Bot can explain: "It used the LightGBM model, but the Zero-Forecast gate triggered because the item has had 0 stock for 4 consecutive weeks.")
- "Which model was chosen for SKU X, and why?" (Bot can explain: "Ridge regression was chosen because SKU X has a 'smooth' demand pattern, and Ridge had the lowest WMAPE (46%) for smooth items during validation.")

## License

MIT
