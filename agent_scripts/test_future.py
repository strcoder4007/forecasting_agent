from backend.data_loader import DataLoader
from backend.forecast_pipeline import ForecastPipeline

dl = DataLoader()
fp = ForecastPipeline(dl)
data = dl.load_all()

sales_weekly, stock_weekly = fp._aggregate_to_weekly(data["sales"], data["stock"])
print("Max week:", sales_weekly["week_start"].max())
