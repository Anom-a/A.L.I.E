import uuid
from domain.entities.research_query import ResearchQuery, ResearchStatus
from adapters.repositories.in_memory_job_repository import InMemoryJobRepository

repo = InMemoryJobRepository()
query = ResearchQuery(topic="test")
repo.add(query)

print("Initial status:", repo.get(query.id).status.value)

repo.update_status(query.id, ResearchStatus.RUNNING)
print("After running:", repo.get(query.id).status.value)

repo.update_status(query.id, ResearchStatus.FAILED)
print("After failed:", repo.get(query.id).status.value)
