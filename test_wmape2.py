from backend.data_loader import DataLoader
from backend.forecast_pipeline import ForecastPipeline

def run():
    dl = DataLoader()
    fp = ForecastPipeline(dl)
    def log(p, s, m):
        if s in ["training", "predicting"]:
            print(f"[{s}] {m}")
    fp.run(progress_callback=log)

run()
