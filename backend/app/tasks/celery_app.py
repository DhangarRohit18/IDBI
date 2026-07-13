"""
FinTwin AI — Celery Application Configuration
Configures Celery with Redis broker, specialized queues, and scheduled tasks.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Initialize Celery app
celery_app = Celery(
    "fintwin",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.digital_twin_tasks",
        "app.tasks.risk_tasks",
        "app.tasks.agent_tasks",
        "app.tasks.ews_tasks",
        "app.tasks.report_tasks",
        "app.tasks.ingestion_tasks",
        "app.tasks.notification_tasks",
    ],
)

# Configuration
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.digital_twin_tasks.*": {"queue": "digital_twin_queue"},
        "app.tasks.risk_tasks.*": {"queue": "ml_queue"},
        "app.tasks.agent_tasks.*": {"queue": "ml_queue"},
        "app.tasks.ews_tasks.*": {"queue": "ews_queue"},
        "app.tasks.report_tasks.*": {"queue": "report_queue"},
        "app.tasks.ingestion_tasks.*": {"queue": "ingestion_queue"},
        "app.tasks.notification_tasks.*": {"queue": "notification_queue"},
    },
    beat_schedule={
        # EWS scan: daily at 00:30 IST (19:00 UTC previous day)
        "daily-ews-scan": {
            "task": "app.tasks.ews_tasks.run_all_tenant_ews_scans",
            "schedule": crontab(hour=19, minute=0),
        },
        # Digital Twin staleness check: every 6 hours
        "twin-staleness-check": {
            "task": "app.tasks.digital_twin_tasks.mark_stale_twins",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        # Portfolio metrics cache refresh: every 10 minutes
        "portfolio-cache-refresh": {
            "task": "app.tasks.report_tasks.refresh_portfolio_cache",
            "schedule": crontab(minute="*/10"),
        },
    },
)


# Context manager for async tasks that need a DB session
async def get_async_session():
    """Get async DB session for use in Celery tasks."""
    from app.db.base import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
