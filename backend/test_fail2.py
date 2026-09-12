import asyncio
import uuid
import time
import requests
import threading

def run_test():
    # Start a job
    r = requests.post("http://127.0.0.1:8000/research", json={"topic": "Test fail"})
    job_id = r.json()["job_id"]
    print("Started job:", job_id)
    
    # We will poll it 
    for _ in range(5):
        time.sleep(1)
        r2 = requests.get(f"http://127.0.0.1:8000/research/{job_id}")
        print("Status:", r2.json())

t = threading.Thread(target=run_test)
t.start()
t.join()
