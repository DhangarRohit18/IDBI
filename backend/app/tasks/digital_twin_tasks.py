"""
FinTwin AI — Digital Twin Celery Tasks
Async tasks for generating and maintaining Digital Twins.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.digital_twin_tasks.generate_digital_twin",
    max_retries=3,
    default_retry_delay=60,
    queue="digital_twin_queue",
)
def generate_digital_twin(
    self,
    msme_id: str,
    tenant_id: str,
    triggered_by: str,
    force: bool = False,
) -> dict:
    """Generate Digital Twin for an MSME. Runs in Celery worker."""
    return asyncio.get_event_loop().run_until_complete(
        _async_generate_digital_twin(msme_id, tenant_id, triggered_by, force)
    )


async def _async_generate_digital_twin(
    msme_id: str,
    tenant_id: str,
    triggered_by: str,
    force: bool,
) -> dict:
    from app.db.base import AsyncSessionLocal
    from app.services.digital_twin_service import DigitalTwinService

    async with AsyncSessionLocal() as db:
        service = DigitalTwinService(db)
        try:
            twin = await service.generate_twin(
                msme_id=UUID(msme_id),
                tenant_id=tenant_id,
                triggered_by=triggered_by,
                force=force,
            )
            logger.info(
                "Digital Twin generated",
                msme_id=msme_id,
                twin_id=str(twin.id),
            )
            return {"twin_id": str(twin.id), "status": "completed"}
        except Exception as exc:
            logger.exception("Digital Twin generation failed", msme_id=msme_id, error=str(exc))
            raise


@celery_app.task(
    name="app.tasks.digital_twin_tasks.mark_stale_twins",
    queue="digital_twin_queue",
)
def mark_stale_twins() -> dict:
    """Mark Digital Twins as STALE if older than configured expiry."""
    return asyncio.get_event_loop().run_until_complete(_async_mark_stale_twins())


async def _async_mark_stale_twins() -> dict:
    from app.db.base import AsyncSessionLocal
    from app.models.digital_twin import DigitalTwin
    from datetime import datetime, timezone
    from sqlalchemy import update, and_

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(DigitalTwin)
            .where(
                and_(
                    DigitalTwin.status == "ACTIVE",
                    DigitalTwin.expires_at < now,
                )
            )
            .values(status="STALE")
        )
        await db.commit()
        count = result.rowcount
        logger.info("Marked stale twins", count=count)
        return {"stale_twins_marked": count}
