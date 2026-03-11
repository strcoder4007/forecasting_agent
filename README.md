# Demand Forecasting Agent

A machine learning-powered demand forecasting system built with FastAPI and Vue.js. The system processes sales and stock data to generate accurate demand forecasts using ensemble modeling techniques.

## Features

- **Data Validation**: Validates sales, stock, item, and store master data files
- **Multi-Stage Pipeline**: Weekly aggregation, false-zero correction, demand segmentation
- **Advanced Feature Engineering**: Includes Categorical Target Encoding on `combo_id` to memorize baseline volume and utilizes actual pricing and promotional markdown (`discount_pct`) signals.
- **Segment-Based Model Routing**: Dynamically evaluates and routes predictions between Seasonal Naive, Ridge Regression (lsqr), and LightGBM based on the lowest WMAPE per demand segment (Smooth, Intermittent, Lumpy).
- **Confidence Intervals**: Provides 80% confidence bounds for forecasts.
- **REST API**: Full REST API for running forecasts and retrieving results.
- **Real-Time Execution Logs**: Granular progress tracking and detailed execution logs streamed to the UI.
- **Offline Storage & Export**: Forecast results are cached locally in the browser using IndexedDB for lightning-fast reads and purely client-side CSV exports.

## Tech Stack

- **Backend**: FastAPI, Python 3.12
- **ML/Data**: pandas, numpy, scikit-learn, LightGBM, scipy
- **Frontend**: Vue.js 3, Vite
- **API**: RESTful endpoints

## Project Structure

```
forecasting_agent/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── data_loader.py    # Data loading and validation
│   ├── forecast_pipeline.py  # Core forecasting logic
│   └── data/             # Data files (CSV/Excel)
├── frontend/             # Vue.js frontend
├── requirements.txt      # Python dependencies
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

1. **Data Loading** (5%): Load and validate data files
2. **Weekly Aggregation** (15%): Aggregate daily data to weekly (Monday start)
3. **False-Zero Correction** (25%): Identify and correct stock-outs mislabeled as zero demand
4. **Demand Segmentation** (35%): Classify demand patterns (smooth, intermittent, lumpy)
5. **Feature Engineering** (45%): Compute 12 features per combo-week including actual prices, discount percentages, and Categorical Target Encoding.
6. **Model Training** (60%): Train Ridge and LightGBM models with walk-forward validation
7. **Inference & Routing** (80%): Evaluate WMAPE per segment and dynamically route to the best model (Naive, Ridge, or LGBM).
8. **Finalization** (100%): Apply post-processing (zero-forecast gate, ROS blend)

## License

MIT
