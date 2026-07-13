from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from app.core.permissions import require_permission
from app.dependencies import CurrentActiveUser, DBSession
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", summary="List Audit Logs")
async def list_audit_logs(
    current_user: CurrentActiveUser,
    db: DBSession,
    entity_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: CurrentActiveUser = Depends(require_permission("audit:read")),
) -> dict:
    service = AuditService(db)
    return await service.list_logs(
        tenant_id=current_user.tenant_id,
        entity_type=entity_type,
        action=action,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
