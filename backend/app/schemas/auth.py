from __future__ import annotations
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema
from app.schemas.user import UserResponse


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=1)
    device_id: str | None = None


class MFAVerifyRequest(BaseSchema):
    challenge_token: str
    totp_code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$')


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class MFARequiredResponse(BaseSchema):
    mfa_required: bool = True
    challenge_token: str


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class PasswordChangeRequest(BaseSchema):
    current_password: str
    new_password: str = Field(min_length=8)


class PasswordResetRequest(BaseSchema):
    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    token: str
    new_password: str = Field(min_length=8)


class MFASetupResponse(BaseSchema):
    secret: str
    provisioning_uri: str
    qr_code_url: str


class MFAEnableRequest(BaseSchema):
    totp_code: str = Field(min_length=6, max_length=6)
