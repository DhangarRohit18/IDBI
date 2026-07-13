"""
FinTwin AI — Risk Prediction API Routes
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions import require_permission
from app.dependencies import CurrentActiveUser, DBSession
from app.schemas.common import TaskResponse
from app.schemas.risk import RiskPredictRequest, RiskPredictionResponse, SHAPExplanation
from app.services.risk_service import RiskService

router = APIRouter()


@router.post(
    "/{msme_id}/predict",
    response_model=TaskResponse,
    status_code=202,
    summary="Run Risk Prediction",
)
async def predict_risk(
    msme_id: UUID,
    body: RiskPredictRequest,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("risk:predict")),
) -> TaskResponse:
    """Queue ML risk prediction pipeline for an MSME."""
    service = RiskService(db)
    task_id = await service.queue_prediction(
        msme_id=msme_id,
        tenant_id=current_user.tenant_id,
        triggered_by=current_user.id,
        force=body.force_repredict,
    )
    return TaskResponse(task_id=task_id, message="Risk prediction queued")


@router.get(
    "/{msme_id}/latest",
    response_model=RiskPredictionResponse,
    summary="Get Latest Risk Prediction",
)
async def get_latest_prediction(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("risk:read")),
) -> RiskPredictionResponse:
    """Get the most recent risk prediction for an MSME."""
    service = RiskService(db)
    return await service.get_latest(msme_id, current_user.tenant_id)


@router.get(
    "/{msme_id}/history",
    response_model=list[RiskPredictionResponse],
    summary="Get Risk Prediction History",
)
async def get_prediction_history(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> list[RiskPredictionResponse]:
    """Get all risk predictions for an MSME."""
    service = RiskService(db)
    return await service.get_history(msme_id, current_user.tenant_id)


@router.get(
    "/prediction/{prediction_id}/explanation",
    response_model=SHAPExplanation,
    summary="Get AI Explanation",
)
async def get_explanation(
    prediction_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("xai:read")),
) -> SHAPExplanation:
    """Get SHAP + LIME explainability output for a risk prediction."""
    service = RiskService(db)
    return await service.get_explanation(prediction_id, current_user.tenant_id)
