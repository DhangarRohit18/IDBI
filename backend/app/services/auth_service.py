"""
FinTwin AI — Authentication Service
Handles login, MFA, token management, password operations.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from fastapi import BackgroundTasks
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    AccountLockedError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_field,
    encrypt_field,
    generate_totp_provisioning_uri,
    generate_totp_secret,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_totp,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import MFASetupResponse, TokenResponse
from app.schemas.user import UserResponse
from app.utils.cache import RedisCache

logger = structlog.get_logger(__name__)

# Temporary MFA challenge storage key pattern
MFA_CHALLENGE_KEY = "mfa_challenge:{token}"
MFA_CHALLENGE_TTL = 300  # 5 minutes


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._challenge_cache = RedisCache(namespace="mfa", default_ttl=MFA_CHALLENGE_TTL)

    async def login(
        self,
        email: str,
        password: str,
        device_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> TokenResponse | dict:
        """Authenticate user with email/password. Returns tokens or MFA challenge."""
        user = await self._get_user_by_email(email)

        # Check account lock
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            minutes_remaining = int(
                (user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60
            ) + 1
            raise AccountLockedError(minutes_remaining)

        # Verify password
        if not verify_password(password, user.password_hash):
            await self._increment_failed_attempts(user)
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # Reset failed attempts on success
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address
        await self.db.flush()

        # Log authentication event
        await self._log_auth_event(user, "LOGIN", ip_address, user_agent)

        if user.mfa_enabled and user.mfa_secret:
            # Issue MFA challenge
            challenge_token = secrets.token_urlsafe(32)
            await self._challenge_cache.set(
                f"mfa_challenge:{challenge_token}",
                {
                    "user_id": str(user.id),
                    "tenant_id": str(user.tenant_id),
                    "device_id": device_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                },
                ttl=MFA_CHALLENGE_TTL,
            )
            return {"mfa_required": True, "challenge_token": challenge_token}

        return await self._issue_tokens(user, device_id, ip_address, user_agent)

    async def verify_mfa(
        self,
        challenge_token: str,
        totp_code: str,
    ) -> TokenResponse:
        """Verify TOTP code and issue tokens."""
        challenge_data = await self._challenge_cache.get(
            f"mfa_challenge:{challenge_token}"
        )
        if not challenge_data:
            raise AuthenticationError("Invalid or expired MFA challenge")

        user_id = challenge_data["user_id"]
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.mfa_secret:
            raise AuthenticationError("User not found")

        # Decrypt TOTP secret and verify
        decrypted_secret = decrypt_field(user.mfa_secret)
        if not verify_totp(decrypted_secret, totp_code):
            raise AuthenticationError("Invalid TOTP code")

        # Invalidate challenge
        await self._challenge_cache.delete(f"mfa_challenge:{challenge_token}")

        return await self._issue_tokens(
            user,
            challenge_data.get("device_id"),
            challenge_data.get("ip_address"),
            challenge_data.get("user_agent"),
        )

    async def refresh_token(self, raw_refresh_token: str) -> TokenResponse:
        """Issue new access token using valid refresh token."""
        token_hash = hash_refresh_token(raw_refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise AuthenticationError("Invalid or expired refresh token")

        # Load user
        result = await self.db.execute(
            select(User).where(User.id == token_record.user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or deactivated")

        # Rotate refresh token (revoke old, issue new)
        token_record.is_revoked = True
        await self.db.flush()

        return await self._issue_tokens(
            user,
            token_record.device_id,
            token_record.ip_address,
            token_record.user_agent,
        )

    async def logout(self, user_id: str, raw_refresh_token: str) -> None:
        """Revoke a specific refresh token."""
        token_hash = hash_refresh_token(raw_refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.user_id == user_id,
                )
            )
        )
        token = result.scalar_one_or_none()
        if token:
            token.is_revoked = True
            await self.db.flush()

    async def logout_all_devices(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        from sqlalchemy import update
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> None:
        """Change user password with current password verification."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def request_password_reset(self, email: str) -> None:
        """Send password reset email if email exists (no user enumeration)."""
        try:
            user = await self._get_user_by_email(email)
        except AuthenticationError:
            return  # Silently fail to prevent enumeration

        reset_token = secrets.token_urlsafe(32)
        cache = RedisCache(namespace="password_reset")
        await cache.set(
            f"reset:{reset_token}",
            {"user_id": str(user.id)},
            ttl=3600,  # 1 hour
        )

        # Send email (import here to avoid circular dependency)
        from app.integrations.sendgrid_client import SendGridClient
        client = SendGridClient()
        await client.send_password_reset_email(user.email, user.first_name, reset_token)

    async def reset_password(self, token: str, new_password: str) -> None:
        """Complete password reset with token verification."""
        cache = RedisCache(namespace="password_reset")
        data = await cache.get(f"reset:{token}")
        if not data:
            raise AuthenticationError("Invalid or expired reset token")

        result = await self.db.execute(select(User).where(User.id == data["user_id"]))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.db.flush()
        await cache.delete(f"reset:{token}")

    async def setup_mfa(self, user_id: str, email: str) -> MFASetupResponse:
        """Generate TOTP secret and provisioning URI for MFA setup."""
        secret = generate_totp_secret()
        provisioning_uri = generate_totp_provisioning_uri(secret, email)

        # Temporarily store secret (not saved until enabled)
        cache = RedisCache(namespace="mfa_setup")
        await cache.set(f"pending:{user_id}", {"secret": secret}, ttl=600)

        # Generate QR code URL (using external service or local generation)
        import urllib.parse
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={urllib.parse.quote(provisioning_uri)}&size=200x200"

        return MFASetupResponse(
            secret=secret,
            provisioning_uri=provisioning_uri,
            qr_code_url=qr_url,
        )

    async def enable_mfa(self, user_id: str, totp_code: str) -> None:
        """Enable MFA after verifying the first code."""
        cache = RedisCache(namespace="mfa_setup")
        data = await cache.get(f"pending:{user_id}")
        if not data:
            raise ValidationError("MFA setup session expired. Please restart setup.")

        secret = data["secret"]
        if not verify_totp(secret, totp_code):
            raise ValidationError("Invalid TOTP code")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        user.mfa_enabled = True
        user.mfa_secret = encrypt_field(secret)
        await self.db.flush()
        await cache.delete(f"pending:{user_id}")

    async def disable_mfa(self, user_id: str, password: str) -> None:
        """Disable MFA with password confirmation."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid password")

        user.mfa_enabled = False
        user.mfa_secret = None
        await self.db.flush()

    # ---- Private helpers ----

    async def _get_user_by_email(self, email: str) -> User:
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        user = result.scalar_one_or_none()
        if not user:
            raise AuthenticationError("Invalid email or password")
        return user

    async def _increment_failed_attempts(self, user: User) -> None:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            logger.warning("Account locked", user_id=str(user.id), email=user.email)
        await self.db.flush()

    async def _issue_tokens(
        self,
        user: User,
        device_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Create access + refresh tokens and store refresh token hash."""
        access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
            region=user.region,
        )
        raw_refresh, refresh_hash = create_refresh_token()

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(refresh_record)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def _log_auth_event(
        self,
        user: User,
        action: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        from app.models.audit_log import AuditLog
        log = AuditLog(
            tenant_id=user.tenant_id,
            user_id=user.id,
            entity_type="USER",
            entity_id=user.id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"User {action.lower()} event",
        )
        self.db.add(log)
        await self.db.flush()
