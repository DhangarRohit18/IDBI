from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Query
from app.dependencies import CurrentActiveUser, DBSession
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", summary="List Notifications")
async def list_notifications(
    current_user: CurrentActiveUser,
    db: DBSession,
    is_read: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    service = NotificationService(db)
    return await service.list_notifications(
        user_id=current_user.id,
        is_read=is_read,
        limit=limit,
        offset=offset,
    )


@router.post("/{notification_id}/read", response_model=SuccessResponse)
async def mark_read(
    notification_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> SuccessResponse:
    service = NotificationService(db)
    await service.mark_read(notification_id, current_user.id)
    return SuccessResponse(message="Notification marked as read")


@router.post("/read-all", response_model=SuccessResponse)
async def mark_all_read(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> SuccessResponse:
    service = NotificationService(db)
    await service.mark_all_read(current_user.id)
    return SuccessResponse(message="All notifications marked as read")


@router.get("/unread-count", summary="Get Unread Count")
async def get_unread_count(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> dict:
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)
    return {"unread_count": count}
