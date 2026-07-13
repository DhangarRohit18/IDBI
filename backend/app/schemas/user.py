from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import EmailStr, Field, field_validator
from app.schemas.common import BaseSchema, IDMixin, TimestampMixin
from app.utils.validators import validate_mobile


class CurrentUser(BaseSchema):
    """Minimal user info stored in JWT claims and injected by dependencies."""
    id: str
    tenant_id: str
    email: str
    full_name: str
    role: str
    region: str | None = None


class UserCreate(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str
    phone: str | None = None
    employee_id: str | None = None
    department: str | None = None
    region: str | None = None

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v):
        if v:
            return validate_mobile(v)
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseSchema):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = None
    department: str | None = None
    region: str | None = None
    avatar_url: str | None = None


class UserResponse(IDMixin, TimestampMixin):
    tenant_id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    phone: str | None
    employee_id: str | None
    department: str | None
    region: str | None
    mfa_enabled: bool
    is_active: bool
    last_login_at: datetime | None
    avatar_url: str | None
