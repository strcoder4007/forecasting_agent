from backend.data_loader import DataLoader
from backend.forecast_pipeline import ForecastPipeline

dl = DataLoader()
fp = ForecastPipeline(dl)
data = dl.load_all()

sales_weekly, stock_weekly = fp._aggregate_to_weekly(data["sales"], data["stock"])

print("Sales weekly rows:", len(sales_weekly))
print("Total possible weekly rows (48000 combos * 52 weeks):", 48000 * 52)

combo = sales_weekly["combo_id"].iloc[0]
combo_data = sales_weekly[sales_weekly["combo_id"] == combo].sort_values("week_start")
print("Combo sample weeks count:", len(combo_data))
print("Weeks difference:\n", combo_data["week_start"].diff().dt.days.value_counts())
