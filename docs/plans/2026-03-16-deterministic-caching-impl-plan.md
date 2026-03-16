# Deterministic Caching Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add deterministic caching to forecasting_agent so same input data produces identical results, with faster re-runs via caching.

**Architecture:** Compute SHA256 hash of data files. Check cache before each pipeline phase. If cache hit, skip phase. If cache miss, run phase and save to cache. Add fixed random seeds to ML models for determinism.

**Tech Stack:** Python, SHA256 (hashlib), DuckDB, LightGBM, XGBoost, scikit-learn

---

## Phase 1: Cache System

### Task 1: Create CacheManager class

**Files:**
- Create: `backend/cache.py`

**Step 1: Create the file**

```python
import hashlib
import os
import json
import duckdb
from typing import Optional, Dict, Any
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "forecasts.duckdb")

class CacheManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_cache_table()
    
    def _init_cache_table(self):
        """Initialize cache table in DuckDB."""
        conn = duckdb.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS run_cache (
                cache_key VARCHAR PRIMARY KEY,
                data_hash VARCHAR,
                phase VARCHAR,
                results_json VARCHAR,
                created_at VARCHAR
            )
        """)
        conn.close()
    
    def compute_data_hash(self, data_dir: str) -> str:
        """Compute SHA256 hash of all data files in directory."""
        hash_obj = hashlib.sha256()
        
        # Sort files for deterministic order
        files = sorted([
            f for f in os.listdir(data_dir)
            if os.path.isfile(os.path.join(data_dir, f))
            and not f.startswith('.')
            and not f.endswith('.db')
            and not f.endswith('.joblib')
        ])
        
        for filename in files:
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'rb') as f:
                # Read in chunks to handle large files
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def get_cached_run(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if cached results exist for given key."""
        conn = duckdb.connect(self.db_path)
        try:
            result = conn.execute(
                "SELECT results_json FROM run_cache WHERE cache_key = ?",
                [cache_key]
            ).fetchone()
            
            if result:
                return json.loads(result[0])
            return None
        finally:
            conn.close()
    
    def save_cached_run(self, cache_key: str, data_hash: str, phase: str, results: Dict[str, Any]):
        """Save results to cache with hash + phase."""
        conn = duckdb.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO run_cache 
                VALUES (?, ?, ?, ?, ?)
            """, [
                cache_key,
                data_hash,
                phase,
                json.dumps(results),
                datetime.now().isoformat()
            ])
        finally:
            conn.close()
    
    def clear_cache(self):
        """Clear all cached results."""
        conn = duckdb.connect(self.db_path)
        try:
            conn.execute("DELETE FROM run_cache")
        finally:
            conn.close()
```

**Step 2: Test import**

Run: `cd /Users/str/Datahat/forecasting_agent && source venv/bin/activate && python -c "from backend.cache import CacheManager; print('OK')"`

Expected: OK

**Step 3: Commit**

```bash
git add backend/cache.py
git commit -m "feat: add CacheManager class for deterministic caching"
```

---

### Task 2: Integrate CacheManager into main.py

**Files:**
- Modify: `backend/main.py`

**Step 1: Add import and initialize**

Add after other imports:
```python
from .cache import CacheManager
```

After `runs_lock` initialization:
```python
# Initialize cache manager
cache_manager = CacheManager()
```

**Step 2: Pass cache_manager to orchestrator**

In `run_forecast_thread()`:
```python
forecast_pipeline = AutonomousForecaster(
    run_id,
    progress_callback=lambda p, s, m, t=None: _update_progress(run_id, p, s, m, t),
    cache_manager=cache_manager
)
```

**Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: integrate CacheManager into main.py"
```

---

### Task 3: Modify Orchestrator for Caching

**Files:**
- Modify: `backend/orchestrator.py`

**Step 1: Update constructor**

Add `cache_manager` parameter:
```python
def __init__(self, run_id: str, progress_callback, cache_manager=None):
    # ... existing code ...
    self.cache_manager = cache_manager
    self.data_hash = None
    
    if cache_manager:
        try:
            self.data_hash = cache_manager.compute_data_hash(self.data_dir)
        except Exception as e:
            print(f"Warning: Could not compute data hash: {e}")
```

**Step 2: Add cache checking to each phase**

For Phase 1 (Explorer):
```python
# Phase 1: Explorer - Check cache
if self.cache_manager and self.data_hash:
    cache_key = f"{self.data_hash}:explorer"
    cached = self.cache_manager.get_cached_run(cache_key)
    if cached and 'report' in cached:
        self.analysis_report = cached['report']
        self._update(25, "exploring", "✅ Data exploration (cached).")
    else:
        # ... existing exploration code ...
        # After exploration completes:
        if self.cache_manager:
            self.cache_manager.save_cached_run(
                cache_key, self.data_hash, 'explorer',
                {'report': self.analysis_report}
            )
```

Similar pattern for Phase 2 (Transformer) and Phase 3 (Modeler).

**Step 3: Commit**

```bash
git add backend/orchestrator.py
git commit -m "feat: add caching to orchestrator phases"
```

---

## Phase 2: Deterministic ML

### Task 4: Add Fixed Random Seeds

**Files:**
- Modify: `backend/orchestrator.py` (in the agent prompts)

**Step 1: Update model training prompts**

Add to the model_sys prompt:
```
IMPORTANT - Use fixed random seeds for reproducibility:
- LightGBM: random_state=42, force_colwise=True
- XGBoost: random_state=42  
- Ridge/Linear: random_state=42
- Always set random_state=42 for any stochastic operation
```

**Step 2: Commit**

```bash
git commit -m "feat: add random seed requirements to ML prompts"
```

---

### Task 5: Standardize Feature Engineering

**Files:**
- Modify: `backend/orchestrator.py` (in ETL prompt)

**Step 1: Update ETL prompt to always include standard features**

Add to etl_sys prompt:
```
REQUIRED features (always include these):
- lag_1, lag_2, lag_3, lag_4: Sales from 1-4 weeks ago
- rolling_mean_4, rolling_mean_8, rolling_mean_12: Rolling averages
- rolling_std_4: Rolling standard deviation
- week_of_year: 1-52 (for seasonality)
- day_of_week: 0-6 (for weekly patterns)
- is_month_start, is_month_end: Month boundary flags
- qty_sold_lag1_ratio: ratio of lag1 to rolling_mean_4
```

**Step 2: Commit**

```bash
git commit -m "feat: standardize feature engineering"
```

---

### Task 6: Fixed Model Selection Logic

**Files:**
- Modify: `backend/orchestrator.py` (model prompt)

**Step 1: Add model selection logic**

Add to model_sys prompt:
```
MODEL SELECTION (use this logic, NOT random):
- If validation WMAPE < 0.1: Use LightGBM
- If validation WMAPE 0.1-0.3: Use Ridge Regression
- If validation WMAPE > 0.3 or insufficient data: Use Seasonal Naive (last year's same week)

ENSEMBLE: Average LightGBM + Ridge predictions, weighted by inverse WMAPE
```

**Step 2: Commit**

```bash
git commit -m "feat: add fixed model selection logic"
```

---

## Phase 3: Accuracy Improvements

### Task 7: Add Weekly Seasonality

**Files:**
- Modify: `backend/orchestrator.py` (ETL prompt)

**Step 1: Enhance seasonality features**

Update the week_of_year requirement:
```
- week_of_year: 1-52 (cyclical encoding: sin(2*pi*week/52), cos(2*pi*week/52))
- year_over_year: Same week last year's sales (if available)
- week_trend: Linear trend coefficient over last 8 weeks
```

**Step 2: Commit**

```bash
git commit -m "feat: enhance seasonality features"
```

---

### Task 8: Proper Time-Series Validation

**Files:**
- Modify: `backend/orchestrator.py` (model prompt)

**Step 1: Add validation strategy**

Add to model_sys prompt:
```
VALIDATION STRATEGY:
- Use time-series split: last 4 weeks = test set
- NO random shuffle splits
- Calculate WMAPE on test set only
- Report both train and test WMAPE
```

**Step 2: Commit**

```bash
git commit -m "feat: add time-series validation"
```

---

## Phase 4: Testing

### Task 9: Verify Determinism

**Step 1: Run forecast twice with same data**

```bash
# First run
curl -X POST http://localhost:8000/api/forecast/run
# Note the run_id and results

# Second run  
curl -X POST http://localhost:8000/api/forecast/run
# Compare results - should be identical
```

**Step 2: Verify via API**

```python
import requests
r1 = requests.get('http://localhost:8000/api/forecast/results/<run1_id>')
r2 = requests.get('http://localhost:8000/api/forecast/results/<run2_id>')
assert r1.json()['rows'] == r2.json()['rows'], "Results should be identical!"
```

**Step 3: Commit**

```bash
git commit -m "test: verify deterministic results"
```

---

### Task 10: Test Cache Performance

**Step 1: Time first run (cache miss)**

```bash
time curl -X POST http://localhost:8000/api/forecast/run
# Note the time (e.g., ~5 minutes)
```

**Step 2: Time second run (cache hit)**

```bash
time curl -X POST http://localhost:8000/api/forecast/run  
# Should be <10 seconds
```

**Step 3: Commit**

```bash
git commit -m "test: verify cache performance improvement"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Create CacheManager | backend/cache.py (new) |
| 2 | Integrate into main.py | backend/main.py |
| 3 | Add caching to orchestrator | backend/orchestrator.py |
| 4 | Fixed random seeds | backend/orchestrator.py |
| 5 | Standardize features | backend/orchestrator.py |
| 6 | Fixed model selection | backend/orchestrator.py |
| 7 | Seasonality features | backend/orchestrator.py |
| 8 | Time-series validation | backend/orchestrator.py |
| 9 | Test determinism | Manual testing |
| 10 | Test cache performance | Manual testing |

---

**Plan complete and saved to `docs/plans/2026-03-16-deterministic-caching-impl-plan.md`**

---

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
