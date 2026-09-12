import asyncio
from enum import Enum
from pydantic import BaseModel
import json

class ResearchStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class JobStatusResponse(BaseModel):
    status: ResearchStatus

resp = JobStatusResponse(status=ResearchStatus.FAILED)
print(resp.model_dump_json())
