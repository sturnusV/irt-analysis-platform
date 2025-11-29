from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "irt_analysis",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.analysis_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)