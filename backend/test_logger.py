import logging
logger = logging.getLogger("application")
try:
    raise ValueError("Test error")
except Exception as exc:
    print("Before logger")
    logger.exception("Research job failed due to an unexpected error", extra={"job_id": "test"})
    print("After logger")
