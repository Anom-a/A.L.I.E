from dotenv import load_dotenv
import os
from openai import OpenAI
import json

load_dotenv(dotenv_path="/home/heisenberg/Documents/projects/A.L.I.E./backend/.env")

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"]
)

schema = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

try:
    response = client.chat.completions.create(
        model=os.environ["OPENAI_MODEL_PLANNER"],
        messages=[{"role": "user", "content": "What are two topics about AI?"}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "test_schema", "schema": schema},
        },
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", repr(e))

