# Data Analysis Report

## Overview

| File | Format | Size | Rows |
|------|--------|------|------|
| SALES_MASTER.xls | CSV (wrong extension) | 773 MB | 5,000,000 |
| SOH_MASTER.xls | CSV (wrong extension) | 533 MB | 4,000,000 |
| ITEM_MASTER.xls | CSV (wrong extension) | 500 KB | 3,200 |
| STORE_MASTER.csv | CSV | 1.3 KB | 15 |

**Date Range:** 2025-01-01 to 2025-12-31 (1 year)

---

## 1. SALES_MASTER.xls

### Schema
| Column | Type | Description |
|--------|------|-------------|
| Store_ID | string | Store identifier |
| date | string | Transaction date (YYYY-MM-DD) |
| Group | string | Group (Adult Men, Adult Women) |
| Department | string | Department (Tops, Bottoms) |
| Class | string | Product class |
| Subclass | string | Product subclass |
| Style | string | Style name |
| Colour | string | Color |
| Size | string | Size (S, M, L, XL) |
| SKU | string | Full SKU (pipe-separated composite key) |
| Quantity | int | Units sold |
| COGS | int | Cost of goods sold |
| Gross Selling Price | int | List price |
| Gross_Sales | int | Gross sales amount |
| Markdown | float | Discount percentage (0 = no discount) |
| Net_Sales | float | Net sales (after markdown) |

### Statistics
- **Unique stores:** 15
- **Unique SKUs:** 3,200
- **Total store-SKU combos:** 48,000
- **Quantity per transaction:** min=1, max=7, mean=1.84
- **Promotions:** 30% of rows have Markdown > 0 (discounts range from ~9% to ~31%)

### Key Observations
- SKU is a composite key: `Group | Department | Class | Subclass | Style | Colour | Size`
- Markdown column can serve as promotion indicator
- 15 stores across NYC (NY-101 to NY-115)

---

## 2. SOH_MASTER.xls (Stock on Hand)

### Schema
| Column | Type | Description |
|--------|------|-------------|
| LOC_ID | string | Location/store ID |
| date | string | Date (YYYY-MM-DD) |
| LOCATION_TYPE | string | Location type (STR = Store) |
| Group | string | Group |
| Department | string | Department |
| Class | string | Class |
| Subclass | string | Subclass |
| Style | string | Style |
| Colour | string | Colour |
| Size | string | Size |
| SKU | string | Full SKU |
| SOH | int | Stock on hand quantity |

### Statistics
- **Unique locations:** 16 (15 stores +可能有warehouse)
- **Unique SKUs:** 3,200
- **Date range:** 2025-01-01 to 2025-12-31
- **SOH stats:** min=0, max=3, mean=0.55
- **Zero stock rows:** 1,959,918 (49.0%) — nearly half!

### Key Observations
- 49% of records have zero stock — significant for demand forecasting
- LOC_ID column holds store IDs (e.g., NY-111)
- LOCATION_TYPE = "STR" for all records (stores only)

---

## 3. ITEM_MASTER.xls

### Schema
| Column | Type | Description |
|--------|------|-------------|
| Group | string | Group (Adult Men, Adult Women) |
| Department | string | Department |
| Class | string | Class |
| Subclass | string | Subclass |
| Style | string | Style |
| Colour | string | Colour |
| Size | string | Size |
| SKU | string | Full SKU (primary key) |
| Season | string | Season code (SS-25 = Spring Summer 2025) |
| COGS | int | Cost of goods sold |
| Gross Selling Price | int | Retail price |
| Vendor | string | Vendor name |
| Item launch Date | int | Excel date serial number |
| Item Type | string | Item type (AIS) |
| UOM | string | Unit of measure (PCS) |

### Statistics
- **Total rows:** 3,200 (unique SKUs)
- **Groups:** Adult Men (1,600), Adult Women (1,600)
- **Departments:** Tops (1,920), Bottoms (1,280)
- **Classes:** 7 unique
- **Subclasses:** 17 unique
- **Season:** SS-25 (only one season)

### Hierarchy
```
Group
└── Department
    └── Class
        └── Subclass
            └── Style
                └── Colour
                    └── Size
                        = SKU
```

---

## 4. STORE_MASTER.csv

### Schema
| Column | Type | Description |
|--------|------|-------------|
| Opening Date | string | Store opening date (DD-MM-YYYY) |
| Store Id | string | Store ID |
| Store Grade | string | Grade (A+, A, B, C) |
| Store Size Sqft | int | Store size in square feet |
| Address | string | Full address |
| County | string | County/Borough |
| State | State | State (NY) |
| Country | string | Country (USA) |
| Store Type | string | Type (BNM) |

### Statistics
- **Total stores:** 15
- **Store grades:** A+ (3), A (4), B (4), C (4)
- **Store types:** BNM (all)
- **States:** NY only
- **Counties:** New York, Brooklyn, Queens, Bronx, Staten Island, Flushing

### Store Distribution
| Grade | Count | Stores |
|-------|-------|--------|
| A+ | 3 | NY-101, NY-102, NY-103 |
| A | 4 | NY-105, NY-106, NY-107, NY-108 |
| B | 4 | NY-109, NY-110, NY-111, NY-112 |
| C | 4 | NY-113, NY-114, NY-115 |

---

## Data Mapping to Documentation

| Documentation Requirement | Available Data | Notes |
|--------------------------|----------------|-------|
| Sales: store_id, sku_id, date, qty_sold | Store_ID, SKU, date, Quantity | ✓ Exact match |
| Stock: store_id, sku_id, date, stock_qty | LOC_ID, SKU, date, SOH | ✓ Match (LOC_ID = store_id) |
| Promotions: store_id, sku_id, start_date, end_date, discount_pct | Partial — Markdown column exists but no explicit promo calendar | Can derive from Markdown > 0 |
| Store metadata: store_id, cluster_label, price_elasticity_score, region | STORE_MASTER.csv has Store Id, Store Grade, Store Size Sqft, County | Partial — no elasticity score |

---

## Gaps & Recommendations

1. **No explicit promotions calendar** — Markdown column exists but lacks start/end dates
2. **No price elasticity score** — Store metadata missing elasticity
3. **Only 1 season (SS-25)** — Limited seasonal variation in data
4. **Zero stock is high (49%)** — Will need false-zero correction per documentation
5. **File extensions** — .xls files are actually CSV, will need to handle in code

---

## GAP ANALYSIS: Required vs Available Data for Forecasting Agent

### Required Data Sources

| # | Data Source | Required Fields | Status in Available Data |
|---|-------------|-----------------|--------------------------|
| 1 | **Sales** | store_id, sku_id, date, qty_sold | ✅ AVAILABLE - SALES_MASTER.xls has Store_ID, SKU, date, Quantity |
| 2 | **Stock on Hand** | store_id, sku_id, date, stock_qty | ✅ AVAILABLE - SOH_MASTER.xls has LOC_ID, SKU, date, SOH |
| 3 | **Promotions Calendar** | store_id, sku_id, start_date, end_date, discount_pct | ⚠️ PARTIAL - Markdown column exists but NO start/end dates |
| 4 | **Store Metadata** | store_id, cluster_label, price_elasticity_score, region | ⚠️ PARTIAL - Store Grade and County available, price_elasticity_score MISSING |
| 5 | **Holidays Table** | date, holiday_name | ❌ NOT AVAILABLE - Need to use Python holidays library |

### Detailed Gap Analysis

#### 1. Promotions Calendar - PARTIAL GAP
- **Available:** `Markdown` column in SALES_MASTER.xls (discount percentage)
- **Missing:** Promotion start_date and end_date
- **Impact:** Cannot determine promotion duration or create promotional features
- **Workaround:** Treat any week with Markdown > 0 as "promotional week"

#### 2. Price Elasticity Score - MISSING
- **Required:** `price_elasticity_score` per store
- **Available:** None
- **Impact:** Cannot use elasticity-based features
- **Workaround:** Use constant/default value (e.g., 1.0)

#### 3. Holidays Table - NOT AVAILABLE
- **Required:** date, holiday_name
- **Available:** None
- **Impact:** Cannot create holiday-specific features
- **Workaround:** Use Python `holidays` library for US holidays

### Required Features vs Available Data

| Feature | Required Data | Available |
|---------|--------------|-----------|
| n_stores | SKU → store count | ✅ Can compute from SALES_MASTER |
| rolling_cv_4 | qty_sold time series | ✅ Available |
| rolling_std_4 | qty_sold time series | ✅ Available |
| avg_rsp | price per combo | ❌ NOT directly available - could derive from Gross Selling Price in ITEM_MASTER |
| season_to_date_qty | season + qty | ⚠️ Only 1 season (SS-25) |
| qty_vs_rolling_mean | qty + rolling mean | ✅ Available |
| pattern_type_std_cat | CV + zero % | ✅ Can compute |
| ewma_4 | qty time series | ✅ Available |
| qty_lag_3 | qty lag 3 | ✅ Available |
| qty_lag_2 | qty lag 2 | ✅ Available |

### Recommendations to Fill Gaps

1. **For promotions:** Derive promotion flags from Markdown > 0 (treat entire week as promotional)
2. **For price_elasticity_score:** Use store-level constant (e.g., 1.0) or omit this feature
3. **For holidays:** Use `pip install holidays` and import US holidays for 2025
4. **For avg_rsp:** Join ITEM_MASTER to get Gross Selling Price per SKU, aggregate to combo level

---

## Summary for Forecasting Agent

- **15 stores** × **3,200 SKUs** = **48,000 combos** to forecast
- **1 year** of daily data (2025) → aggregate to weekly (Monday start)
- **30%** of sales have promotions (Markdown > 0)
- **49%** zero stock → apply false-zero correction
- Store grades available: A+, A, B, C (can use as cluster_label)
- County/Region available from store data
