import requests
import time

# Send a query that will fail at the router level by passing an empty topic
# Wait, empty topic fails at pydantic validation.
# Let's mock a failure in the router by injecting a bad API key for tavily? No, that just causes a retry.

# Instead, let's just create a small router modification that raises Exception immediately
with open("infrastructure/api/main.py", "a") as f:
    f.write("\n@app.post('/test_fail')\ndef test_fail(background_tasks: __import__('fastapi').BackgroundTasks, use_case=__import__('fastapi').Depends(__import__('adapters.controllers.research_controller', fromlist=['get_run_research_use_case']).get_run_research_use_case), repo=__import__('fastapi').Depends(__import__('adapters.controllers.research_controller', fromlist=['get_job_repository']).get_job_repository)):\n")
    f.write("    query = __import__('domain.entities.research_query', fromlist=['ResearchQuery']).ResearchQuery(topic='test_crash')\n")
    f.write("    repo.add(query)\n")
    f.write("    def crash(qid):\n")
    f.write("        try:\n")
    f.write("            raise RuntimeError('Crash')\n")
    f.write("        except Exception as exc:\n")
    f.write("            repo.save_error(qid, 'Crash')\n")
    f.write("            repo.update_status(qid, __import__('domain.entities.research_query', fromlist=['ResearchStatus']).ResearchStatus.FAILED)\n")
    f.write("    background_tasks.add_task(crash, query.id)\n")
    f.write("    return {'job_id': str(query.id)}\n")
