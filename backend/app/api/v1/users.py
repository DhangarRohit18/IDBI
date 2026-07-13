from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from app.core.permissions import require_permission, require_roles, UserRole
from app.dependencies import CurrentActiveUser, DBSession
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse, summary="Get Current User")
async def get_current_user_profile(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> UserResponse:
    service = UserService(db)
    return await service.get_by_id(current_user.id, current_user.tenant_id)


@router.patch("/me", response_model=UserResponse, summary="Update Profile")
async def update_profile(
    body: UserUpdate,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> UserResponse:
    service = UserService(db)
    return await service.update(current_user.id, body, current_user.tenant_id)


@router.get("/", response_model=list[UserResponse], summary="List Users")
async def list_users(
    current_user: CurrentActiveUser,
    db: DBSession,
    role: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    _: CurrentActiveUser = Depends(require_roles(UserRole.BANK_ADMIN)),
) -> list[UserResponse]:
    service = UserService(db)
    return await service.list_users(current_user.tenant_id, role, limit)


@router.post("/", response_model=UserResponse, status_code=201, summary="Create User")
async def create_user(
    body: UserCreate,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_roles(UserRole.BANK_ADMIN)),
) -> UserResponse:
    service = UserService(db)
    return await service.create(body, current_user.tenant_id, current_user.id)


@router.patch("/{user_id}/deactivate", response_model=SuccessResponse)
async def deactivate_user(
    user_id: UUID,
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_roles(UserRole.BANK_ADMIN)),
) -> SuccessResponse:
    service = UserService(db)
    await service.deactivate(user_id, current_user.tenant_id)
    return SuccessResponse(message="User deactivated")
