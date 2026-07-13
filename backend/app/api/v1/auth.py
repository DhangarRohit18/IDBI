"""
FinTwin AI — Authentication API Routes
Login, MFA, token refresh, logout, password management.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentActiveUser, DBSession, get_current_user
from app.schemas.auth import (
    LoginRequest,
    MFAEnableRequest,
    MFARequiredResponse,
    MFASetupResponse,
    MFAVerifyRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse | MFARequiredResponse, summary="Login")
async def login(
    request: Request,
    body: LoginRequest,
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> TokenResponse | MFARequiredResponse:
    """Authenticate with email and password. Returns JWT tokens or MFA challenge."""
    service = AuthService(db)
    return await service.login(
        email=body.email,
        password=body.password,
        device_id=body.device_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        background_tasks=background_tasks,
    )


@router.post("/mfa/verify", response_model=TokenResponse, summary="Verify MFA TOTP")
async def verify_mfa(
    body: MFAVerifyRequest,
    db: DBSession,
) -> TokenResponse:
    """Verify TOTP code for MFA-enabled users and issue tokens."""
    service = AuthService(db)
    return await service.verify_mfa(body.challenge_token, body.totp_code)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Token")
async def refresh_token(
    body: RefreshTokenRequest,
    db: DBSession,
) -> TokenResponse:
    """Refresh access token using refresh token."""
    service = AuthService(db)
    return await service.refresh_token(body.refresh_token)


@router.post("/logout", response_model=SuccessResponse, summary="Logout")
async def logout(
    body: RefreshTokenRequest,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> SuccessResponse:
    """Invalidate refresh token and log user out."""
    service = AuthService(db)
    await service.logout(current_user.id, body.refresh_token)
    return SuccessResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=SuccessResponse, summary="Logout All Devices")
async def logout_all(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> SuccessResponse:
    """Invalidate all refresh tokens for the user (logout from all devices)."""
    service = AuthService(db)
    await service.logout_all_devices(current_user.id)
    return SuccessResponse(message="Logged out from all devices")


@router.post("/password/change", response_model=SuccessResponse, summary="Change Password")
async def change_password(
    body: PasswordChangeRequest,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> SuccessResponse:
    """Change password for the authenticated user."""
    service = AuthService(db)
    await service.change_password(current_user.id, body.current_password, body.new_password)
    return SuccessResponse(message="Password changed successfully")


@router.post("/password/reset-request", response_model=SuccessResponse, summary="Request Password Reset")
async def request_password_reset(
    body: PasswordResetRequest,
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> SuccessResponse:
    """Send password reset email. Always returns success to prevent user enumeration."""
    service = AuthService(db)
    background_tasks.add_task(service.request_password_reset, body.email)
    return SuccessResponse(message="If the email exists, a reset link will be sent")


@router.post("/password/reset-confirm", response_model=SuccessResponse, summary="Confirm Password Reset")
async def confirm_password_reset(
    body: PasswordResetConfirm,
    db: DBSession,
) -> SuccessResponse:
    """Complete password reset with token and new password."""
    service = AuthService(db)
    await service.reset_password(body.token, body.new_password)
    return SuccessResponse(message="Password reset successfully")


@router.get("/mfa/setup", response_model=MFASetupResponse, summary="Setup MFA")
async def setup_mfa(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> MFASetupResponse:
    """Generate TOTP secret and QR code URI for MFA enrollment."""
    service = AuthService(db)
    return await service.setup_mfa(current_user.id, current_user.email)


@router.post("/mfa/enable", response_model=SuccessResponse, summary="Enable MFA")
async def enable_mfa(
    body: MFAEnableRequest,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> SuccessResponse:
    """Enable MFA after verifying the first TOTP code."""
    service = AuthService(db)
    await service.enable_mfa(current_user.id, body.totp_code)
    return SuccessResponse(message="MFA enabled successfully")


@router.delete("/mfa/disable", response_model=SuccessResponse, summary="Disable MFA")
async def disable_mfa(
    body: PasswordChangeRequest,
    current_user: CurrentActiveUser,
    db: DBSession,
) -> SuccessResponse:
    """Disable MFA (requires password confirmation)."""
    service = AuthService(db)
    await service.disable_mfa(current_user.id, body.current_password)
    return SuccessResponse(message="MFA disabled")
