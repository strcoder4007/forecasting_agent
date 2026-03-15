# Forecasting Agent PRD

## 1. Project Overview

**Project Name:** Demand Forecasting Agent
**Type:** Web Application (Frontend + Backend)
**Core Functionality:** An Autonomous Data Scientist agent that dynamically explores raw files, writes custom Python ETL pipelines, trains ML models on the fly, and interacts via natural language.
**Target Users:** Business analysts, inventory managers, supply chain teams.

---

## 2. Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend     │     │    Backend      │
│   (Vue.js)     │────▶│   (FastAPI)     │
│   Port: 5173   │◀────│   Port: 8000    │
└─────────────────┘     └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Data Store    │
                       │   (CSV/Parquet) │
                       └─────────────────┘
```

---

## 3. UI/UX Specification

### 3.1 Pages

| Page | Purpose |
|------|---------|
| **Chat Agent (Main)** | Conversational UI to trigger forecasts, load history, and run data analyses |
| **History** | Past runs and their metrics |

### 3.2 Visual Design

- **Color Palette:**
  - Primary: `#1E3A8A` (Dark Blue)
  - Secondary: `#3B82F6` (Light Blue)
  - Accent: `#059669` (Green for success)
  - Error: `#EF4444` (Red)
  - Background: `#F8FAFC`
  - Card/Bubble: `#FFFFFF`

- **Typography:**
  - Font: Inter or system-ui
  - Headings: 24px (h1), 20px (h2), 16px (h3)
  - Body: 14px

### 3.3 Components

| Component | States | Description |
|-----------|--------|-------------|
| Chat Bubble | user, ai, system, loading | Displays chat conversation |
| ProgressBubble | running, success, failed | Native chat widget showing forecast run progress |

---

## 4. Functionality Specification

### 4.1 Core Features

#### Backend (Python/FastAPI)

| Feature | Description |
|---------|-------------|
| **Python Sandbox** | Secure environment executing generated Python code (`subprocess.run`). |
| **Explorer Agent** | Reads raw files, identifies schemas, and writes an analysis markdown report. |
| **Transformer Agent** | Autonomously writes pandas code to merge files, clean data, and engineer features. |
| **Modeler Agent** | Autonomously writes scikit-learn/xgboost/lightgbm code to train models and output predictions. |
| **DuckDB Storage** | Persists run metadata, logs, DataFrames, and ML Models across sessions. |
| **Agent: Supervisor** | `gemini-3.1-flash-lite-preview` maintains memory and routes user requests. |
| **Agent: Analyst** | `gemini-3.1-pro-preview` runs DuckDB SQL queries against memory and simulates promotional what-if scenarios. |

#### Frontend (Vue.js)

| Feature | Description |
|---------|-------------|
| **Chat Interface** | Main UI for interacting with the application via natural language. |
| **Live Progress** | Real-time execution logs streamed directly into a chat bubble during a forecast run. |
| **Context Loading** | Smoothly switches between historical runs when instructed by the AI or selected from History. |
| **History** | List of past runs with timestamps, status, WMAPE, and MAPE metrics. |

### 4.2 Data Flow

```
1. User types "Run a forecast" into the chat
2. Supervisor Agent delegates to Autonomous Orchestrator
3. Explorer Agent writes Python to read raw files and output a schema report
4. Transformer Agent writes Python to clean data and build a feature matrix
5. Modeler Agent writes Python to train ML models and save predictions
6. Real-time Python execution traces stream to the frontend Activity UI
7. Results are persisted to DuckDB
8. User asks data question ("What is the forecast for SKU X?")
9. Analyst Agent generates DuckDB SQL, queries the data, and returns markdown
```

**Data Files Location:** `/data/` folder (pre-loaded, no upload needed)

| File | Expected Path | Notes |
|------|---------------|-------|
| Sales | `data/SALES_MASTER.xls` | Actually CSV format |
| Stock | `data/SOH_MASTER.xls` | Actually CSV format |
| Items | `data/ITEM_MASTER.xls` | Actually CSV format |
| Stores | `data/STORE_MASTER.csv` | CSV format |

### 4.3 API Endpoints

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| GET | `/api/data/validate` | - | `{ status, file_info, warnings }` |
| POST | `/api/forecast/run` | - | `{ run_id, status }` |
| GET | `/api/forecast/status/{run_id}` | - | `{ status, progress, stage, message }` |
| GET | `/api/forecast/results/{run_id}` | - | `{ rows: [...] }` |
| GET | `/api/history` | - | `{ runs: [...] }` |
| GET | `/api/history/{run_id}` | - | `{ run details, metrics }` |
| GET | `/api/export/{run_id}` | - | CSV file |

### 4.4 Output Schema

```
store_id, sku_id, combo_id, forecast_week_start, horizon, point_forecast, lower_80, upper_80, model_used, demand_segment, is_zero_forecast
```

---

## 5. Technical Constraints

- **No neural models**

---

## 6. Acceptance Criteria

| # | Criterion |
|---|-----------|
| 1 | System auto-validates data files from /data folder on startup |
| 2 | User can trigger a forecast run |
| 3 | Progress is shown during run (stage-by-stage) |
| 4 | Results table displays all output columns |
| 5 | User can export results as CSV |
| 6 | History page shows past runs with status |
| 7 | Invalid data shows clear error messages |
| 8 | UI is responsive and simple |

---

## 7. Non-Goals (Out of Scope)

- User authentication (open access)
- File uploads (data pre-loaded in /data folder)
- Real-time streaming data
- Multi-tenant support
- Custom model configurations
- Advanced visualizations (charts)
- Weather API integration
- Database integration (file-based only for v1)

---

## 8. Future Considerations (v2)

- Database storage (PostgreSQL)
- Scheduled/automated runs (cron)
- Alerting on drift
- API key auth
- More export formats (Parquet, Excel)
