from celery import Celery  # type: ignore
from celery.schedules import crontab  # type: ignore
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
        'check-savings-goals-reminders-daily': {
            'task': 'check_savings_goals_reminders',
            'schedule': 86400.0,  # Run daily at midnight UTC
        },
        'send-weekly-reports': {
            'task': 'send_weekly_reports',
            'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Run every Monday at 9:00 UTC (6:00 BRT)
        },
        'send-monthly-reports': {
            'task': 'send_monthly_reports',
            'schedule': crontab(hour=9, minute=0, day_of_month=1),  # Run on 1st of each month at 9:00 UTC (6:00 BRT)
        },
        'send-daily-reports': {
            'task': 'send_daily_reports',
            'schedule': crontab(hour=9, minute=0),  # Run daily at 9:00 UTC (6:00 BRT) - apenas para premium
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])

