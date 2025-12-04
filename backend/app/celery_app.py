from celery import Celery
from app.core.config import settings
import os

# Initialize Celery
celery_app = Celery(
    "finguia",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    beat_schedule={
        'check-budget-alerts-daily': {
            'task': 'check_budget_alerts',
            'schedule': 86400.0,  # Run daily at midnight UTC
        },
        'check-upcoming-payments-daily': {
            'task': 'check_upcoming_payments',
            'schedule': 86400.0,  # Run daily at midnight UTC
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])

