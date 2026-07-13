"""
FinTwin AI — Digital Twin API Routes
Generate, retrieve, and compare AI Digital Twins.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.permissions import require_permission
from app.dependencies import CurrentActiveUser, DBSession
from app.schemas.common import TaskResponse
from app.schemas.digital_twin import DigitalTwinDiff, DigitalTwinResponse, GenerateTwinRequest
from app.services.digital_twin_service import DigitalTwinService

router = APIRouter()


@router.post(
    "/{msme_id}/generate",
    response_model=TaskResponse,
    status_code=202,
    summary="Generate Digital Twin",
)
async def generate_twin(
    msme_id: UUID,
    body: GenerateTwinRequest,
    current_user: CurrentActiveUser,
    db: DBSession,
    background_tasks: BackgroundTasks,
    _: CurrentActiveUser = Depends(require_permission("digital_twin:generate")),
) -> TaskResponse:
    """Queue Digital Twin generation for an MSME. Returns immediately with task ID."""
    service = DigitalTwinService(db)
    task_id = await service.queue_generation(
        msme_id=msme_id,
        tenant_id=current_user.tenant_id,
        force_regenerate=body.force_regenerate,
        triggered_by=current_user.id,
    )
    return TaskResponse(task_id=task_id, message="Digital Twin generation queued")


@router.get(
    "/{msme_id}",
    response_model=DigitalTwinResponse,
    summary="Get Latest Digital Twin",
)
async def get_twin(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("digital_twin:read")),
) -> DigitalTwinResponse:
    """Get the latest active Digital Twin for an MSME."""
    service = DigitalTwinService(db)
    return await service.get_latest(msme_id, current_user.tenant_id)


@router.get(
    "/{msme_id}/history",
    response_model=list[DigitalTwinResponse],
    summary="Get Twin Version History",
)
async def get_twin_history(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> list[DigitalTwinResponse]:
    """Get all historical Digital Twin versions for an MSME."""
    service = DigitalTwinService(db)
    return await service.get_history(msme_id, current_user.tenant_id)


@router.get(
    "/{msme_id}/compare",
    response_model=DigitalTwinDiff,
    summary="Compare Two Twin Versions",
)
async def compare_twins(
    msme_id: UUID,
    twin_a_id: UUID,
    twin_b_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> DigitalTwinDiff:
    """Compare two Digital Twin versions side-by-side."""
    service = DigitalTwinService(db)
    return await service.compare_versions(msme_id, twin_a_id, twin_b_id, current_user.tenant_id)


@router.get(
    "/{msme_id}/similar",
    summary="Find Similar MSMEs",
)
async def find_similar(
    msme_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    top_k: int = 5,
) -> list[dict]:
    """Find MSMEs with similar financial profiles using vector similarity search."""
    service = DigitalTwinService(db)
    return await service.find_similar_msmdes(
        msme_id=msme_id,
        tenant_id=current_user.tenant_id,
        top_k=top_k,
    )
