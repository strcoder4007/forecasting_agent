# forecasting_agent

Guidelines and conventions for the Demand Forecasting Agent project.

## Project Overview

A machine learning-powered demand forecasting system built with FastAPI and Vue.js. Processes sales and stock data to generate accurate demand forecasts using ensemble modeling techniques.

## Code Organization

```
forecasting_agent/
├── backend/           # FastAPI application and ML pipeline
├── frontend/          # Vue.js 3 frontend
├── tests/             # Test scripts (pytest)
├── design-system/     # UI/UX design system
├── requirements.txt   # Python dependencies
└── README.md
```

## Conventions

### Test Scripts

**All test scripts must be stored in the `tests/` folder.**

- Use `pytest` for testing
- Test files should follow naming convention: `test_*.py`
- Run tests with: `pytest tests/`

Example:
```bash
# Wrong
python test_agent.py

# Correct
pytest tests/test_agent.py
```

### Python Environment

- Use `venv` for virtual environment (already set up as `venv/`)
- Install dependencies: `pip install -r requirements.txt`

### Frontend

- Framework: Vue.js 3 with Vite
- Run dev server: `npm run dev` (from `frontend/` directory)

### Backend

- Run server: `uvicorn backend.main:app --reload --port 8000`
- API runs on `http://localhost:8000`
- Frontend proxies to backend in dev mode

## Git Workflow

1. Make changes in a feature branch
2. Commit with descriptive messages
3. Push to remote

```bash
git checkout -b feature/my-feature
git add -A
git commit -m "Description of changes"
git push -u origin feature/my-feature
```

## Data Files

Place data files in `backend/data/`:
- `SALES_MASTER.xls` - Sales transaction data
- `SOH_MASTER.xls` - Stock on hand data
- `ITEM_MASTER.xls` - Item/SKU master data
- `STORE_MASTER.csv` - Store master data
