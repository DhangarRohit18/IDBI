"""
FinTwin AI — MSME Management API Routes
CRUD for MSME profiles with search, filtering, and assignment.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.core.permissions import require_permission
from app.dependencies import CurrentActiveUser, DBSession
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.msme import MSMECreate, MSMEListResponse, MSMEResponse, MSMEUpdate
from app.services.msme_service import MSMEService

router = APIRouter()


@router.post("/", response_model=MSMEResponse, status_code=201, summary="Create MSME")
async def create_msme(
    body: MSMECreate,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("msme:create")),
) -> MSMEResponse:
    """Create a new MSME profile."""
    service = MSMEService(db)
    return await service.create(body, current_user)


@router.get("/", response_model=PaginatedResponse[MSMEListResponse], summary="List MSMEs")
async def list_msmes(
    current_user: CurrentActiveUser,
    db: DBSession,
    query: str | None = Query(default=None),
    industry_type: str | None = Query(default=None),
    state: str | None = Query(default=None),
    risk_tier: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: CurrentActiveUser = Depends(require_permission("msme:read")),
) -> PaginatedResponse[MSMEListResponse]:
    """Search and list MSMEs with filters."""
    service = MSMEService(db)
    return await service.search(
        tenant_id=current_user.tenant_id,
        current_user=current_user,
        query=query,
        industry_type=industry_type,
        state=state,
        risk_tier=risk_tier,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{msme_id}", response_model=MSMEResponse, summary="Get MSME Detail")
async def get_msme(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("msme:read")),
) -> MSMEResponse:
    """Get full MSME profile by ID."""
    service = MSMEService(db)
    return await service.get_by_id(msme_id, current_user.tenant_id)


@router.patch("/{msme_id}", response_model=MSMEResponse, summary="Update MSME")
async def update_msme(
    msme_id: UUID,
    body: MSMEUpdate,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("msme:update")),
) -> MSMEResponse:
    """Update MSME profile fields."""
    service = MSMEService(db)
    return await service.update(msme_id, body, current_user)


@router.delete("/{msme_id}", response_model=SuccessResponse, summary="Delete MSME")
async def delete_msme(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("msme:delete")),
) -> SuccessResponse:
    """Soft-delete an MSME (sets deleted_at timestamp)."""
    service = MSMEService(db)
    await service.soft_delete(msme_id, current_user)
    return SuccessResponse(message="MSME deleted successfully")


@router.get("/{msme_id}/completeness", summary="Get Data Completeness")
async def get_completeness(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> dict:
    """Get MSME data completeness score and missing data breakdown."""
    service = MSMEService(db)
    return await service.get_completeness_report(msme_id, current_user.tenant_id)


@router.get("/{msme_id}/timeline", summary="Get MSME Activity Timeline")
async def get_timeline(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    """Get chronological timeline of all activity for an MSME."""
    service = MSMEService(db)
    return await service.get_timeline(msme_id, current_user.tenant_id, limit)
