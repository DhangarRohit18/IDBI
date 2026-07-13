"""
FinTwin AI — RBAC Permission System
Defines roles, permissions matrix, and FastAPI dependency functions.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable

from fastapi import Depends

from app.core.exceptions import AuthorizationError
from app.dependencies import get_current_user
from app.schemas.user import CurrentUser


class UserRole(str, Enum):
    BANK_ADMIN = "BANK_ADMIN"
    LOAN_OFFICER = "LOAN_OFFICER"
    RISK_MANAGER = "RISK_MANAGER"
    CREDIT_ANALYST = "CREDIT_ANALYST"
    REGIONAL_MANAGER = "REGIONAL_MANAGER"


# Permission matrix: role → set of allowed actions
ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.BANK_ADMIN: {
        # User management
        "users:create", "users:read", "users:update", "users:delete",
        # MSME
        "msme:create", "msme:read", "msme:update", "msme:delete",
        "msme:assign",
        # Evaluations
        "evaluation:create", "evaluation:read", "evaluation:decide",
        "evaluation:override",
        # AI Features
        "digital_twin:read", "digital_twin:generate",
        "risk:predict", "risk:read",
        "simulation:run", "simulation:read",
        "agents:run", "agents:read",
        "xai:read",
        # Portfolio
        "portfolio:read",
        # EWS
        "ews:read", "ews:configure", "ews:acknowledge",
        # Reports
        "reports:generate", "reports:read",
        # Audit
        "audit:read",
        # Settings
        "settings:read", "settings:update",
        # Notifications
        "notifications:read",
    },
    UserRole.LOAN_OFFICER: {
        "msme:create", "msme:read", "msme:update",
        "evaluation:create", "evaluation:read", "evaluation:decide",
        "digital_twin:read",
        "risk:predict", "risk:read",
        "simulation:run", "simulation:read",
        "agents:run", "agents:read",
        "xai:read",
        "reports:generate", "reports:read",
        "ews:read", "ews:acknowledge",
        "notifications:read",
    },
    UserRole.RISK_MANAGER: {
        "msme:read", "msme:update",
        "evaluation:read", "evaluation:decide", "evaluation:override",
        "digital_twin:read", "digital_twin:generate",
        "risk:predict", "risk:read",
        "simulation:run", "simulation:read",
        "agents:run", "agents:read",
        "xai:read",
        "portfolio:read",
        "ews:read", "ews:configure", "ews:acknowledge",
        "reports:generate", "reports:read",
        "audit:read",
        "notifications:read",
    },
    UserRole.CREDIT_ANALYST: {
        "msme:read",
        "evaluation:read",
        "digital_twin:read", "digital_twin:generate",
        "risk:predict", "risk:read",
        "simulation:run", "simulation:read",
        "agents:run", "agents:read",
        "xai:read",
        "ews:read",
        "reports:generate", "reports:read",
        "notifications:read",
    },
    UserRole.REGIONAL_MANAGER: {
        "msme:read",
        "evaluation:read",
        "digital_twin:read",
        "risk:read",
        "simulation:read",
        "agents:read",
        "xai:read",
        "portfolio:read",
        "ews:read",
        "reports:generate", "reports:read",
        "notifications:read",
    },
}


def require_permission(permission: str) -> Callable:
    """FastAPI dependency factory: verifies user has the required permission."""
    async def check_permission(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        user_role = UserRole(current_user.role)
        allowed = ROLE_PERMISSIONS.get(user_role, set())
        if permission not in allowed:
            raise AuthorizationError(
                f"Role '{current_user.role}' does not have permission: {permission}"
            )
        return current_user
    return check_permission


def require_roles(*roles: UserRole) -> Callable:
    """FastAPI dependency factory: verifies user has one of the specified roles."""
    async def check_role(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if UserRole(current_user.role) not in roles:
            raise AuthorizationError(
                f"This action requires one of the following roles: {[r.value for r in roles]}"
            )
        return current_user
    return check_role


def has_permission(user_role: str, permission: str) -> bool:
    """Utility function to check permission without raising exception."""
    role = UserRole(user_role)
    return permission in ROLE_PERMISSIONS.get(role, set())
