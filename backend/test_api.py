import requests
import time

# Start a job
r = requests.post("http://127.0.0.1:8000/research", json={"topic": "Test failure"})
job_id = r.json()["job_id"]
print("Started job:", job_id)

# Poll it
for _ in range(10):
    time.sleep(1)
    status = requests.get(f"http://127.0.0.1:8000/research/{job_id}").json()
    print(status)
    if status["status"] in ("done", "failed"):
        break
