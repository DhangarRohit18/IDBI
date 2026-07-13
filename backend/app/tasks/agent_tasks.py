"""
FinTwin AI — Multi-Agent AI Celery Tasks
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.agent_tasks.run_agent_pipeline",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=180,
    queue="ml_queue",
)
def run_agent_pipeline(
    self,
    evaluation_id: str,
    tenant_id: str,
    triggered_by: str,
) -> dict:
    """Run the full LangGraph Multi-Agent AI pipeline for a loan evaluation."""
    return asyncio.get_event_loop().run_until_complete(
        _async_run_agent_pipeline(evaluation_id, tenant_id, triggered_by)
    )


async def _async_run_agent_pipeline(
    evaluation_id: str,
    tenant_id: str,
    triggered_by: str,
) -> dict:
    from app.db.base import AsyncSessionLocal
    from app.services.agent_service import AgentService

    async with AsyncSessionLocal() as db:
        service = AgentService(db)
        analysis = await service.run_pipeline(
            evaluation_id=UUID(evaluation_id),
            tenant_id=tenant_id,
            triggered_by=triggered_by,
        )
        return {
            "analysis_id": str(analysis.id),
            "status": analysis.pipeline_status,
            "fraud_score": float(analysis.fraud_score) if analysis.fraud_score else None,
        }
