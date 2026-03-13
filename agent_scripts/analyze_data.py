"""Data analysis script to identify forecasting issues."""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("/Users/str/Datahat/forecasting_agent/data")

print("=" * 80)
print("LOADING DATA...")
print("=" * 80)

# Load all data
sales = pd.read_csv(DATA_DIR / "SALES_MASTER.xls")
stock = pd.read_csv(DATA_DIR / "SOH_MASTER.xls")
items = pd.read_csv(DATA_DIR / "ITEM_MASTER.xls")
stores = pd.read_csv(DATA_DIR / "STORE_MASTER.csv")

print(f"Sales: {len(sales):,} rows")
print(f"Stock: {len(stock):,} rows")
print(f"Items: {len(items):,} rows")
print(f"Stores: {len(stores):,} rows")

# Clean column names
sales.columns = sales.columns.str.strip()
stock.columns = stock.columns.str.strip()
items.columns = items.columns.str.strip()
stores.columns = stores.columns.str.strip()

print("\n" + "=" * 80)
print("SALES DATA OVERVIEW")
print("=" * 80)
print(sales.dtypes)
print("\nSample rows:")
print(sales.head(3))

# Create combo_id
sales['combo_id'] = sales['Store_ID'] + '|' + sales['SKU']
stock['combo_id'] = stock['LOC_ID'] + '|' + stock['SKU']

# Convert dates
sales['date'] = pd.to_datetime(sales['date'])
stock['date'] = pd.to_datetime(stock['date'])

print("\n" + "=" * 80)
print("1. SALES DISTRIBUTION ANALYSIS")
print("=" * 80)

# Aggregate to weekly
sales['week_start'] = sales['date'] - pd.to_timedelta(sales['date'].dt.dayofweek, unit='D')
weekly_sales = sales.groupby(['combo_id', 'week_start']).agg({
    'Quantity': 'sum',
    'Markdown': 'max'
}).reset_index()
weekly_sales.columns = ['combo_id', 'week_start', 'qty_sold', 'discount_pct']

print(f"\nTotal combo-weeks: {len(weekly_sales):,}")
print(f"Unique combos: {weekly_sales['combo_id'].nunique():,}")
print(f"Unique weeks: {weekly_sales['week_start'].nunique()}")

print(f"\nQuantity stats:")
print(weekly_sales['qty_sold'].describe())

print(f"\nZero sales weeks: {(weekly_sales['qty_sold'] == 0).sum():,} ({(weekly_sales['qty_sold'] == 0).mean()*100:.1f}%)")
print(f"Zero sales weeks (excluding first 4): {(weekly_sales[weekly_sales['week_start'] > weekly_sales['week_start'].min() + pd.Timedelta(weeks=4)]['qty_sold'] == 0).mean()*100:.1f}%")

# Distribution of qty_sold
print("\nQuantity distribution:")
print(f"  qty = 0: {(weekly_sales['qty_sold'] == 0).sum():,} ({((weekly_sales['qty_sold'] == 0).mean()*100):.1f}%)")
print(f"  qty = 1: {((weekly_sales['qty_sold'] == 1).sum()):,} ({((weekly_sales['qty_sold'] == 1).mean()*100):.1f}%)")
print(f"  qty = 2: {((weekly_sales['qty_sold'] == 2).sum()):,} ({((weekly_sales['qty_sold'] == 2).mean()*100):.1f}%)")
qty_3_5 = ((weekly_sales['qty_sold'] >= 3) & (weekly_sales['qty_sold'] <= 5)).sum()
qty_3_5_pct = ((weekly_sales['qty_sold'] >= 3) & (weekly_sales['qty_sold'] <= 5)).mean() * 100
print(f"  qty = 3-5: {qty_3_5:,} ({qty_3_5_pct:.1f}%)")
qty_gt_5 = (weekly_sales['qty_sold'] > 5).sum()
qty_gt_5_pct = (weekly_sales['qty_sold'] > 5).mean() * 100
print(f"  qty > 5: {qty_gt_5:,} ({qty_gt_5_pct:.1f}%)")

print("\n" + "=" * 80)
print("2. PER-COMBO SALES ANALYSIS")
print("=" * 80)

combo_stats = weekly_sales.groupby('combo_id').agg({
    'qty_sold': ['mean', 'std', 'sum', 'count'],
}).reset_index()
combo_stats.columns = ['combo_id', 'mean_qty', 'std_qty', 'total_qty', 'weeks_active']
combo_stats['cv'] = combo_stats['std_qty'] / (combo_stats['mean_qty'] + 0.001)
combo_stats['zero_pct'] = 1 - (combo_stats['weeks_active'] / weekly_sales['week_start'].nunique())

print(f"\nCombo mean quantity stats:")
print(combo_stats['mean_qty'].describe())

print(f"\nCombo CV (coefficient of variation) stats:")
print(combo_stats['cv'].describe())

print(f"\nTop 10 combos by total sales:")
print(combo_stats.nlargest(10, 'total_qty')[['combo_id', 'mean_qty', 'std_qty', 'total_qty', 'cv']])

print(f"\nBottom 10 combos by total sales:")
print(combo_stats.nsmallest(10, 'total_qty')[['combo_id', 'mean_qty', 'std_qty', 'total_qty', 'cv']])

print("\n" + "=" * 80)
print("3. DEMAND SEGMENTATION")
print("=" * 80)

def get_segment(row):
    if row['zero_pct'] > 0.5:
        return 'intermittent'
    elif row['cv'] > 1:
        return 'lumpy'
    else:
        return 'smooth'

combo_stats['segment'] = combo_stats.apply(get_segment, axis=1)

print(f"\nSegment distribution:")
print(combo_stats['segment'].value_counts())
print(f"\nSegment percentages:")
print(combo_stats['segment'].value_counts(normalize=True) * 100)

print(f"\nSegment stats:")
for seg in ['smooth', 'intermittent', 'lumpy']:
    seg_data = combo_stats[combo_stats['segment'] == seg]
    print(f"\n{seg.upper()}:")
    print(f"  Count: {len(seg_data):,}")
    print(f"  Mean qty: {seg_data['mean_qty'].mean():.2f}")
    print(f"  Median qty: {seg_data['mean_qty'].median():.2f}")
    print(f"  CV: {seg_data['cv'].mean():.2f}")

print("\n" + "=" * 80)
print("4. STOCK ON HAND ANALYSIS")
print("=" * 80)

stock_weekly = stock.groupby(['combo_id', 'week_start'])['SOH'].max().reset_index()
stock_weekly.columns = ['combo_id', 'week_start', 'stock_qty']

print(f"\nStock stats:")
print(stock_weekly['stock_qty'].describe())

print(f"\nZero stock weeks: {(stock_weekly['stock_qty'] == 0).sum():,} ({(stock_weekly['stock_qty'] == 0).mean()*100:.1f}%)")

# Merge stock with sales
merged = weekly_sales.merge(stock_weekly, on=['combo_id', 'week_start'], how='left')
merged['stock_qty'] = merged['stock_qty'].fillna(0)

print(f"\nSales vs Stock analysis:")
print(f"  Total rows: {len(merged):,}")
print(f"  Zero sales & Zero stock: {((merged['qty_sold'] == 0) & (merged['stock_qty'] == 0)).sum():,}")
print(f"  Zero sales & Stock > 0: {((merged['qty_sold'] == 0) & (merged['stock_qty'] > 0)).sum():,}")
print(f"  Sales > 0 & Zero stock: {((merged['qty_sold'] > 0) & (merged['stock_qty'] == 0)).sum():,}")
print(f"  Sales > 0 & Stock > 0: {((merged['qty_sold'] > 0) & (merged['stock_qty'] > 0)).sum():,}")

print("\n" + "=" * 80)
print("5. PROMOTION ANALYSIS")
print("=" * 80)

print(f"\nPromotion (Markdown) stats:")
print(sales['Markdown'].describe())

print(f"\nWeeks with promotion (> 0): {(sales['Markdown'] > 0).mean()*100:.1f}%")

weekly_promo = sales.groupby(['combo_id', 'week_start'])['Markdown'].max().reset_index()
weekly_promo.columns = ['combo_id', 'week_start', 'has_promo']
weekly_promo['has_promo'] = (weekly_promo['has_promo'] > 0).astype(int)

print(f"\nPromotional weeks per combo:")
print(weekly_promo.groupby('combo_id')['has_promo'].sum().describe())

print("\n" + "=" * 80)
print("6. STORE ANALYSIS")
print("=" * 80)

store_sales = sales.groupby('Store_ID')['Quantity'].sum().reset_index()
store_sales.columns = ['store_id', 'total_sales']
print("\nSales by store:")
print(store_sales.sort_values('total_sales', ascending=False))

print("\n" + "=" * 80)
print("7. ITEM/SKU ANALYSIS")
print("=" * 80)

sku_sales = sales.groupby('SKU')['Quantity'].sum().reset_index()
sku_sales.columns = ['sku_id', 'total_sales']
print(f"\nSKU sales distribution:")
print(sku_sales['total_sales'].describe())

print(f"\nTop 10 SKUs by sales:")
print(sku_sales.nlargest(10, 'total_sales'))

print(f"\nBottom 10 SKUs by sales:")
print(sku_sales.nsmallest(10, 'total_sales'))

# Analyze by hierarchy
print("\nSales by Group:")
print(sales.groupby('Group')['Quantity'].sum())

print("\nSales by Department:")
print(sales.groupby('Department')['Quantity'].sum())

print("\n" + "=" * 80)
print("8. TIME PATTERN ANALYSIS")
print("=" * 80)

sales['week'] = sales['date'].dt.isocalendar().week
sales['month'] = sales['date'].dt.month
sales['dayofweek'] = sales['date'].dt.dayofweek

print("\nSales by month:")
print(sales.groupby('month')['Quantity'].sum())

print("\nSales by day of week (0=Mon, 6=Sun):")
print(sales.groupby('dayofweek')['Quantity'].sum())

print("\n" + "=" * 80)
print("9. POTENTIAL ISSUES IDENTIFICATION")
print("=" * 80)

# Issue 1: Very low average sales
avg_qty = weekly_sales['qty_sold'].mean()
print(f"\n1. LOW AVERAGE SALES: {avg_qty:.2f} units/week/combo")
if avg_qty < 1:
    print("   -> This is VERY LOW. Ridge regression may struggle with near-zero values.")

# Issue 2: High zero percentage
zero_pct = (weekly_sales['qty_sold'] == 0).mean()
print(f"\n2. HIGH ZERO PERCENTAGE: {zero_pct*100:.1f}%")
if zero_pct > 0.5:
    print("   -> Over 50% zeros. Consider using probabilistic models or HTS methods.")

# Issue 3: High CV
high_cv_count = (combo_stats['cv'] > 1).sum()
print(f"\n3. HIGH CV COMBOS: {high_cv_count:,} ({high_cv_count/len(combo_stats)*100:.1f}%)")
if high_cv_count / len(combo_stats) > 0.3:
    print("   -> Over 30% combos have CV > 1. These are 'lumpy' demand - hard to forecast.")

# Issue 4: Intermittency
intermittent_count = (combo_stats['segment'] == 'intermittent').sum()
print(f"\n4. INTERMITTENT DEMAND: {intermittent_count:,} ({intermittent_count/len(combo_stats)*100:.1f}%)")

# Issue 5: Stockouts causing zeros
stockout_zeros = ((merged['qty_sold'] == 0) & (merged['stock_qty'] > 0)).sum()
true_zeros = ((merged['qty_sold'] == 0) & (merged['stock_qty'] == 0)).sum()
print(f"\n5. FALSE ZEROS from stockouts: {stockout_zeros:,} ({stockout_zeros/len(merged)*100:.1f}%)")
print(f"   TRUE ZEROS (no stock, no sale): {true_zeros:,} ({true_zeros/len(merged)*100:.1f}%)")

print("\n" + "=" * 80)
print("10. RECOMMENDATIONS")
print("=" * 80)

print("""
Based on the analysis, here are the key issues and recommendations:

1. LOW VOLUME: Average sales is very low (~0.5 units/week)
   - Ridge regression assumes continuous targets
   - Consider: log-transform, Poisson regression, or categorical models
   
2. HIGH INTERMITTENCY: ~40%+ combos have >50% zero weeks
   - Croston's method, TSB, or similar for intermittent demand
   - Consider: Separate models for zero vs non-zero periods
   
3. HIGH VARIANCE: Many combos have CV > 1
   - Tree-based models (LightGBM, XGBoost) should handle this better
   - Current pipeline already uses these - check if they're being used correctly
   
4. STOCKOUTS: Many zeros are due to stockouts, not true demand
   - Current false-zero correction should help
   - Consider: Using only weeks with stock > 0 for training
   
5. FEATURE ENGINEERING: 
   - Consider: lag-52 for yearly seasonality (if data allows)
   - Consider: Store clustering based on sales patterns
   - Consider: SKU category embeddings

6. MODEL ROUTING:
   - Current routing by segment is good
   - Verify segment-specific WMAPE in logs
   - Consider: Different model hyperparameters per segment
""")

print("\nDONE.")
