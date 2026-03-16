# Forecasting Agent Improvement: Deterministic Pipeline with Caching

**Date:** 2026-03-16
**Status:** Approved

## Problem Statement

Current issues:
- LLM generates different code each run → non-deterministic results
- Same input data produces different outputs
- Slow (LLM calls take time)
- Expensive (repeated API calls for same data)

## Goals

1. **Deterministic** - Same input data always produces same output
2. **Accuracy** - Improve forecast quality through better features + validation
3. **Balance complexity** - Add caching without over-engineering

---

## Solution: Deterministic Pipeline with Caching

### Architecture Overview

```
Data Files → Compute Hash → Check Cache
                              │
                    ┌─────────┴─────────┐
                    │                   │
               Cache Hit          Cache Miss
                    │                   │
                    ▼                   ▼
              Load Cached       Run Pipeline
              Results           + Save Cache
```

### Component 1: Cache Manager (new file: `backend/cache.py`)

```python
class CacheManager:
    def compute_data_hash(data_dir: str) -> str:
        """Compute SHA256 hash of all data files in directory."""
        
    def get_cached_run(cache_key: str) -> Optional[dict]:
        """Check if cached results exist for given key."""
        
    def save_cached_run(cache_key: str, phase: str, results: dict):
        """Save results to cache with hash + phase."""
        
    def clear_cache():
        """Clear all cached results."""
```

**Storage:** DuckDB table `run_cache`
- Columns: `cache_key`, `phase`, `results_json`, `data_hash`, `created_at`

### Component 2: Modified Orchestrator

**Constructor changes:**
```python
def __init__(self, run_id, progress_callback, cache_manager=None):
    self.cache_manager = cache_manager
    self.data_hash = cache_manager.compute_data_hash(self.data_dir) if cache_manager else None
```

**Phase execution with caching:**
```python
# Phase 1: Explorer
cache_key = f"{self.data_hash}:explorer"
cached = self.cache_manager.get_cached_run(cache_key)
if cached:
    self.analysis_report = cached['report']
else:
    self.analysis_report = self._call_agent(...)
    self.cache_manager.save_cached_run(cache_key, 'explorer', 
        {'report': self.analysis_report})
```

### Component 3: Deterministic ML

**Fixed random seeds:**
```python
# LightGBM
lgb_model = lgb.LGBMRegressor(random_state=42, force_colwise=True)

# XGBoost
xgb_model = xgb.XGBRegressor(random_state=42)

# Sklearn
ridge = Ridge(random_state=42)
```

**Standardized features (always included):**
- Lags: [1, 2, 3, 4]
- Rolling mean: [4, 8, 12]
- Week-of-year
- Day-of-week
- Is_month_start, is_month_end

**Fixed model selection logic:**
```python
def select_model(wmape):
    if wmape < 0.1:
        return 'lightgbm'
    elif wmape < 0.3:
        return 'ridge'
    else:
        return 'seasonal_naive'
```

### Component 4: Proper Validation

**Time-series split:**
```python
# Last 4 weeks as test set
test_weeks = 4
train = df[df['week_start'] < cutoff_date]
test = df[df['week_start'] >= cutoff_date]
```

---

## Implementation Plan

### Phase 1: Cache System (Priority: High)
1. Create `backend/cache.py` with CacheManager class
2. Add cache table to DuckDB storage
3. Integrate cache into orchestrator
4. Test cache hit/miss flow

### Phase 2: Deterministic ML (Priority: High)
1. Add fixed random seeds to all ML models
2. Standardize feature engineering
3. Add fixed model selection logic
4. Implement proper time-series validation

### Phase 3: Accuracy Improvements (Priority: Medium)
1. Add week-of-year seasonality features
2. Add day-of-week features
3. Implement ensemble averaging
4. Add WMAPE-based model selection

### Phase 4: Testing & Validation (Priority: Medium)
1. Run same data multiple times → verify identical results
2. Compare accuracy before/after improvements
3. Document benchmark results

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/cache.py` | New - CacheManager class |
| `backend/storage.py` | Add cache table init |
| `backend/orchestrator.py` | Add caching, deterministic ML |
| `backend/main.py` | Integrate cache manager |

---

## Success Criteria

- [ ] Same data → same forecast results (deterministic)
- [ ] Cache hit → <1 second for full pipeline
- [ ] Cache miss → improved accuracy vs before
- [ ] Weekly seasonality properly captured
