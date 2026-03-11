import numpy as np
from backend.data_loader import DataLoader
from backend.forecast_pipeline import ForecastPipeline
dl = DataLoader()
fp = ForecastPipeline(dl)
data = dl.load_all()
sales_weekly, stock_weekly = fp._aggregate_to_weekly(data["sales"], data["stock"])
sales_weekly = fp._apply_false_zero_correction(sales_weekly, stock_weekly)
sales_weekly = fp._segment_demand(sales_weekly)
combo_features = fp._compute_features(sales_weekly)
print("Any inf:", np.isinf(combo_features.select_dtypes(include=np.number)).any().to_dict())
print("Any NaN:", combo_features.isna().any().to_dict())
print("Max values:\n", combo_features.select_dtypes(include=np.number).max())
