import requests
import time

res = requests.post("http://127.0.0.1:8000/api/forecast/run")
data = res.json()
run_id = data["run_id"]
print("Run ID:", run_id)

while True:
    time.sleep(1)
    status_res = requests.get(f"http://127.0.0.1:8000/api/forecast/status/{run_id}")
    status_data = status_res.json()
    print(status_data)
    if status_data["status"] in ("completed", "failed"):
        break
