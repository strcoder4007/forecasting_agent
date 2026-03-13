import pandas as pd
import numpy as np
from backend.data_loader import DataLoader
from backend.forecast_pipeline import ForecastPipeline

pipeline = ForecastPipeline(DataLoader())
data = pipeline.data_loader.load_all()
sales_weekly, stock_weekly = pipeline._aggregate_to_weekly(data["sales"], data["stock"])
sales_weekly = pipeline._apply_false_zero_correction(sales_weekly, stock_weekly)
sales_weekly = pipeline._segment_demand(sales_weekly)
features_df = pipeline._compute_features(sales_weekly)

print("Feature Types:")
print(features_df.dtypes)
print("\nFeature Max Values:")
print(features_df.select_dtypes(include='number').max())
