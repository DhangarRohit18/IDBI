"""
FinTwin AI — Custom Exception Classes
All exceptions extend FinTwinException for consistent error handling.
"""

from __future__ import annotations

from typing import Any

from fastapi import status


class FinTwinException(Exception):
    """Base exception for all FinTwin AI application errors."""

    def __init__(
        self,
        detail: str,
        code: str = "ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        field_errors: dict[str, Any] | None = None,
    ) -> None:
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.field_errors = field_errors or {}
        super().__init__(detail)


class AuthenticationError(FinTwinException):
    """Raised for invalid credentials or expired tokens."""

    def __init__(self, detail: str = "Authentication failed") -> None:
        super().__init__(
            detail=detail,
            code="AUTHENTICATION_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(FinTwinException):
    """Raised when user lacks permission to perform an action."""

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(
            detail=detail,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(FinTwinException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", identifier: str | None = None) -> None:
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} '{identifier}' not found"
        super().__init__(
            detail=detail,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(FinTwinException):
    """Raised when a resource already exists (duplicate)."""

    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(
            detail=detail,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


class ValidationError(FinTwinException):
    """Raised when input data fails business validation."""

    def __init__(
        self,
        detail: str = "Validation failed",
        field_errors: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            detail=detail,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            field_errors=field_errors,
        )


class DataInsufficientError(FinTwinException):
    """Raised when MSME data is insufficient for AI analysis."""

    def __init__(self, completeness: int, required: int = 70) -> None:
        super().__init__(
            detail=f"MSME data completeness is {completeness}% — minimum {required}% required for evaluation.",
            code="DATA_INSUFFICIENT",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class RateLimitError(FinTwinException):
    """Raised when rate limit is exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded. Please try again later.") -> None:
        super().__init__(
            detail=detail,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class AccountLockedError(FinTwinException):
    """Raised when user account is locked due to failed attempts."""

    def __init__(self, minutes: int = 30) -> None:
        super().__init__(
            detail=f"Account locked due to too many failed attempts. Try again in {minutes} minutes.",
            code="ACCOUNT_LOCKED",
            status_code=status.HTTP_423_LOCKED,
        )


class AIProcessingError(FinTwinException):
    """Raised when AI pipeline fails unexpectedly."""

    def __init__(self, detail: str = "AI processing failed", stage: str | None = None) -> None:
        msg = detail
        if stage:
            msg = f"AI processing failed at stage '{stage}': {detail}"
        super().__init__(
            detail=msg,
            code="AI_PROCESSING_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class EvaluationLockedError(FinTwinException):
    """Raised when trying to modify a locked evaluation."""

    def __init__(self) -> None:
        super().__init__(
            detail="This evaluation is locked and cannot be modified after 7 days.",
            code="EVALUATION_LOCKED",
            status_code=status.HTTP_423_LOCKED,
        )


class TenantIsolationError(FinTwinException):
    """Raised when cross-tenant access is attempted."""

    def __init__(self) -> None:
        super().__init__(
            detail="Access denied — cross-tenant access is not permitted.",
            code="TENANT_ISOLATION_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )
