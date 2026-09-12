from dotenv import load_dotenv
import os
from tavily import TavilyClient

load_dotenv(dotenv_path="/home/heisenberg/Documents/projects/A.L.I.E./backend/.env")

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

try:
    response = client.search("What are two topics about AI?", max_results=2)
    print("Response:", response)
except Exception as e:
    print("Error:", repr(e))
