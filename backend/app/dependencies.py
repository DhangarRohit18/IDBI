"""
FinTwin AI — FastAPI Shared Dependencies
Injects current user, DB session, and other shared resources into route handlers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError, TenantIsolationError
from app.core.security import decode_access_token
from app.db.base import AsyncSessionLocal
from app.schemas.user import CurrentUser

logger = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency: provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    FastAPI dependency: validates JWT and returns the current authenticated user.
    Raises AuthenticationError if token is invalid or expired.
    """
    if not credentials:
        raise AuthenticationError("No authentication token provided")

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError as e:
        raise AuthenticationError(f"Invalid or expired token: {str(e)}")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    role = payload.get("role")

    if not all([user_id, tenant_id, role]):
        raise AuthenticationError("Malformed token payload")

    # Load user from database to verify still active
    from app.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User account not found")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    if str(user.tenant_id) != str(tenant_id):
        raise TenantIsolationError()

    return CurrentUser(
        id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        region=user.region,
    )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Alias for get_current_user — explicit naming for route documentation."""
    return current_user


# Typed dependency aliases for cleaner route signatures
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentActiveUser = Annotated[CurrentUser, Depends(get_current_user)]
