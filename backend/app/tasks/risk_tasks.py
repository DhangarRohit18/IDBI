"""
FinTwin AI — Risk Prediction Celery Tasks
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.risk_tasks.predict_risk",
    max_retries=3,
    default_retry_delay=30,
    queue="ml_queue",
)
def predict_risk(
    self,
    msme_id: str,
    tenant_id: str,
    triggered_by: str,
    evaluation_id: str | None = None,
) -> dict:
    """Run ML risk prediction for an MSME."""
    return asyncio.get_event_loop().run_until_complete(
        _async_predict_risk(msme_id, tenant_id, triggered_by, evaluation_id)
    )


async def _async_predict_risk(
    msme_id: str,
    tenant_id: str,
    triggered_by: str,
    evaluation_id: str | None,
) -> dict:
    from app.db.base import AsyncSessionLocal
    from app.services.risk_service import RiskService

    async with AsyncSessionLocal() as db:
        service = RiskService(db)
        prediction = await service.run_prediction(
            msme_id=UUID(msme_id),
            tenant_id=tenant_id,
            evaluation_id=UUID(evaluation_id) if evaluation_id else None,
        )
        return {
            "prediction_id": str(prediction.id),
            "risk_score": float(prediction.risk_score),
            "risk_tier": prediction.risk_tier,
            "pd": float(prediction.probability_of_default),
        }
