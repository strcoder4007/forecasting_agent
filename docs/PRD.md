# Forecasting Agent PRD

## 1. Project Overview

**Project Name:** Demand Forecasting Agent
**Type:** Web Application (Frontend + Backend)
**Core Functionality:** Predict SKU-store demand using historical sales data with automated feature engineering, model selection, and forecasting.
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
| **Dashboard** | Overview: recent forecasts, key metrics, run status |
| **Run Forecast** | Upload data, configure, trigger forecast run |
| **Results** | View forecast results, export data |
| **History** | Past runs and their metrics |

### 3.2 Visual Design

- **Color Palette:**
  - Primary: `#2563EB` (Blue)
  - Secondary: `#64748B` (Slate)
  - Accent: `#10B981` (Green for success)
  - Error: `#EF4444` (Red)
  - Background: `#F8FAFC`
  - Card: `#FFFFFF`

- **Typography:**
  - Font: Inter or system-ui
  - Headings: 24px (h1), 20px (h2), 16px (h3)
  - Body: 14px

- **Spacing:** 8px base unit (8, 16, 24, 32px)

### 3.3 Components

| Component |
|-----------|--------|-------------|
| Button | States | Description | default, hover, loading, disabled | Primary actions |
| FileUpload | idle, dragging, uploading, done | CSV/Parquet upload |
| StatusBadge | running, success, failed | Forecast run status |
| DataTable | loading, empty, populated | Results display |
| ProgressBar | indeterminate, percentage | Run progress |
| Alert | info, warning, error | Notifications |

---

## 4. Functionality Specification

### 4.1 Core Features

#### Backend (Python/FastAPI)

| Feature | Description |
|---------|-------------|
| **Data Ingestion** | Accept CSV uploads (sales, stock, promotions, store metadata). Validate schema. |
| **Weekly Aggregation** | Aggregate daily data to weekly (Monday start). |
| **False-Zero Correction** | Flag items with zero stock and zero sales, impute with category median. |
| **Demand Segmentation** | Classify combos as smooth, intermittent, or lumpy based on CV and zero %. |
| **Feature Engineering** | Compute 12 features including real pricing, promotional signals (discount_pct), and Categorical Target Encoding. |
| **Model Training** | Two-round walk-forward validation. Route predictions to the lowest WMAPE model per segment. |
| **Inference** | Generate forecasts utilizing segment-routed best models with post-processing (bias correction + ROS blend). |
| **CI Estimation** | 80% confidence intervals from validation residuals. |
| **Results Export** | Return forecasts as JSON/CSV. |

#### Frontend (Vue.js)

| Feature | Description |
|---------|-------------|
| **Dashboard** | Show last run status, summary metrics (total combos, avg WMAPE). Show data file validation status. |
| **Run Trigger** | Button to start forecast. Show progress bar and detailed execution logs during run. |
| **Results View** | Table with forecast data. Sortable columns. Cached locally using IndexedDB for fast loading. |
| **Export** | Generate and download results as CSV purely client-side from IndexedDB. |
| **History** | List of past runs with timestamps, status, and validation WMAPE. |

### 4.2 Data Flow

```
1. Backend reads data files from /data folder (pre-loaded)
2. User clicks "Run Forecast"
3. Backend processes in stages:
   - Aggregate → Features → Train → Predict → Post-process
4. Frontend polls for status updates
5. Results displayed in table
6. User exports CSV
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

### 4.4 Data Schema Mapping

Based on data analysis, map source files to required schema:

| Required Column | Source File | Source Column |
|-----------------|-------------|---------------|
| store_id | SALES_MASTER | Store_ID |
| sku_id | SALES_MASTER | SKU |
| date | SALES_MASTER | date |
| qty_sold | SALES_MASTER | Quantity |
| stock_qty | SOH_MASTER | SOH |
| discount_pct | SALES_MASTER | Markdown |
| cluster_label | STORE_MASTER | Store Grade |
| region | STORE_MASTER | County |
| price_elasticity_score | - | Not available (skip) |

### 4.5 Input Files (Pre-loaded in /data folder)

> **Note:** Files are read from local `/data/` folder — no upload required.
> Files have `.xls` extension but are actually CSV format.

**Source files (auto-detected):**
- `data/SALES_MASTER.xls` (actually CSV) — Sales transactions
- `data/SOH_MASTER.xls` (actually CSV) — Stock on hand
- `data/ITEM_MASTER.xls` (actually CSV) — Item catalog
- `data/STORE_MASTER.csv` — Store metadata

**Mapping to required schema:**
- Use `Markdown` column from SALES_MASTER as promotion indicator (discount_pct)
- Use `Store Grade` from STORE_MASTER as cluster_label
- Use `County` from STORE_MASTER as region
- `price_elasticity_score` not available — will use default/constant

### 4.6 Output Schema

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
