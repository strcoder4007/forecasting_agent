from backend.data_loader import DataLoader
from backend.forecast_pipeline import ForecastPipeline

dl = DataLoader()
fp = ForecastPipeline(dl)

def log(p, s, m):
    if s in ["training", "predicting"]:
        print(f"[{s}] {m}")

results = fp.run(progress_callback=log)
print("Results size:", len(results))
if results:
    print("Sample result forecast week:", results[0]["forecast_week_start"])
