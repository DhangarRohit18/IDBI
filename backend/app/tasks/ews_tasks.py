"""
FinTwin AI — EWS Celery Tasks
Scheduled early warning system monitoring jobs.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.tasks.ews_tasks.run_all_tenant_ews_scans",
    queue="ews_queue",
)
def run_all_tenant_ews_scans() -> dict:
    """Run EWS scan for all active tenants. Triggered by Celery Beat daily."""
    return asyncio.get_event_loop().run_until_complete(_async_run_all_scans())


async def _async_run_all_scans() -> dict:
    from app.db.base import AsyncSessionLocal
    from app.models.tenant import Tenant
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Tenant).where(Tenant.is_active == True)
        )
        tenants = result.scalars().all()

    total_alerts = 0
    for tenant in tenants:
        alerts = await _run_tenant_ews_scan(str(tenant.id))
        total_alerts += alerts

    logger.info("All tenant EWS scans complete", total_alerts=total_alerts)
    return {"tenants_scanned": len(tenants), "total_alerts": total_alerts}


@celery_app.task(
    bind=True,
    name="app.tasks.ews_tasks.run_portfolio_ews_scan",
    max_retries=2,
    queue="ews_queue",
)
def run_portfolio_ews_scan(self, tenant_id: str) -> dict:
    """Run EWS scan for a specific tenant."""
    return asyncio.get_event_loop().run_until_complete(
        _run_tenant_ews_scan(tenant_id)
    )


async def _run_tenant_ews_scan(tenant_id: str) -> int:
    """Execute EWS scan logic for one tenant. Returns count of alerts generated."""
    from app.db.base import AsyncSessionLocal
    from app.services.ews_service import EWSService

    async with AsyncSessionLocal() as db:
        service = EWSService(db)
        result = await service.run_portfolio_scan(UUID(tenant_id))
        logger.info(
            "Tenant EWS scan complete",
            tenant_id=tenant_id,
            alerts=result.get("alerts_generated", 0),
        )
        return result.get("alerts_generated", 0)
