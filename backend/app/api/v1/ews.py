"""
FinTwin AI — Early Warning System API Routes
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.permissions import require_permission
from app.dependencies import CurrentActiveUser, DBSession
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.services.ews_service import EWSService

router = APIRouter()


@router.get("/alerts", summary="List EWS Alerts")
async def list_alerts(
    current_user: CurrentActiveUser,
    db: DBSession,
    severity: str | None = Query(default=None),
    is_acknowledged: bool | None = Query(default=None),
    is_resolved: bool | None = Query(default=None),
    msme_id: UUID | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentActiveUser = Depends(require_permission("ews:read")),
) -> dict:
    """List EWS alerts with filters."""
    service = EWSService(db)
    return await service.list_alerts(
        tenant_id=current_user.tenant_id,
        severity=severity,
        is_acknowledged=is_acknowledged,
        is_resolved=is_resolved,
        msme_id=msme_id,
        limit=limit,
        offset=offset,
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=SuccessResponse)
async def acknowledge_alert(
    alert_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    note: str | None = None,
    _: CurrentActiveUser = Depends(require_permission("ews:acknowledge")),
) -> SuccessResponse:
    """Acknowledge an EWS alert."""
    service = EWSService(db)
    await service.acknowledge_alert(alert_id, current_user.id, current_user.tenant_id, note)
    return SuccessResponse(message="Alert acknowledged")


@router.post("/alerts/{alert_id}/resolve", response_model=SuccessResponse)
async def resolve_alert(
    alert_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    note: str | None = None,
) -> SuccessResponse:
    """Mark an EWS alert as resolved."""
    service = EWSService(db)
    await service.resolve_alert(alert_id, current_user.id, current_user.tenant_id, note)
    return SuccessResponse(message="Alert resolved")


@router.get("/{msme_id}/score", summary="Get MSME EWS Score")
async def get_ews_score(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> dict:
    """Get the current EWS score and signal breakdown for an MSME."""
    service = EWSService(db)
    return await service.get_msme_ews_score(msme_id, current_user.tenant_id)


@router.post("/scan", summary="Trigger EWS Scan", status_code=202)
async def trigger_scan(
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("ews:configure")),
) -> dict:
    """Manually trigger EWS portfolio scan for all active MSMEs."""
    from app.tasks.ews_tasks import run_portfolio_ews_scan
    task = run_portfolio_ews_scan.delay(current_user.tenant_id)
    return {"task_id": task.id, "message": "EWS portfolio scan queued"}
