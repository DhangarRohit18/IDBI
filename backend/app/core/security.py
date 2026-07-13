"""
FinTwin AI — Security Utilities
JWT token creation/validation, password hashing, TOTP MFA, API key management.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pyotp
structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

import structlog

logger = structlog.get_logger(__name__)

# Password hashing context — bcrypt with cost factor 12
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Token type constants
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


# ============================================================
# PASSWORD UTILITIES
# ============================================================

def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# JWT TOKEN UTILITIES
# ============================================================

def create_access_token(
    user_id: str,
    tenant_id: str,
    role: str,
    region: str | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived JWT access token with user claims."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    if region:
        payload["region"] = region
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    """Generate a cryptographically secure refresh token. Returns (raw_token, token_hash)."""
    raw_token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    Raises JWTError if invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise JWTError("Invalid token type")
    return payload


def hash_refresh_token(raw_token: str) -> str:
    """Hash a refresh token for secure database storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ============================================================
# TOTP / MFA UTILITIES
# ============================================================

def generate_totp_secret() -> str:
    """Generate a new base32 TOTP secret for MFA setup."""
    return pyotp.random_base32()


def generate_totp_provisioning_uri(secret: str, email: str) -> str:
    """Generate the TOTP provisioning URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.APP_NAME)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code with ±1 window for clock drift tolerance."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# ============================================================
# ENCRYPTION UTILITIES (AES-256 for PII fields)
# ============================================================

def _get_fernet():
    """Return Fernet cipher instance for field-level encryption."""
    from cryptography.fernet import Fernet
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    )
    return Fernet(key)


def encrypt_field(plaintext: str) -> str:
    """Encrypt a sensitive field value (e.g., GSTIN, PAN) for database storage."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a previously encrypted field value."""
    if not ciphertext:
        return ciphertext
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


# ============================================================
# API KEY UTILITIES
# ============================================================

def generate_api_key() -> tuple[str, str]:
    """Generate a new API key. Returns (raw_key, key_hash)."""
    raw_key = f"ft_{secrets.token_urlsafe(40)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())
