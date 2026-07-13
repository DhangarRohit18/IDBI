from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import EmailStr, Field, field_validator
from app.schemas.common import BaseSchema, IDMixin, TimestampMixin
from app.utils.validators import validate_gstin, validate_pan, validate_mobile, validate_indian_state


class MSMECreate(BaseSchema):
    business_name: str = Field(min_length=2, max_length=200)
    gstin: str
    pan: str
    industry_type: str = Field(min_length=1, max_length=100)
    sub_industry: str | None = None
    business_description: str | None = None
    state: str
    district: str | None = None
    city: str | None = None
    pincode: str | None = None
    address: str | None = None
    registration_date: date
    registration_number: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    website: str | None = None
    msme_category: str | None = None
    annual_turnover: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None

    @field_validator("gstin")
    @classmethod
    def validate_gstin_field(cls, v):
        return validate_gstin(v)

    @field_validator("pan")
    @classmethod
    def validate_pan_field(cls, v):
        return validate_pan(v)

    @field_validator("state")
    @classmethod
    def validate_state_field(cls, v):
        return validate_indian_state(v)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone_field(cls, v):
        if v:
            return validate_mobile(v)
        return v

    @field_validator("registration_date")
    @classmethod
    def validate_registration_date(cls, v):
        from datetime import date
        if v > date.today():
            raise ValueError("Registration date cannot be in the future")
        if v.year < 1990:
            raise ValueError("Registration date cannot be before 1990")
        return v


class MSMEUpdate(BaseSchema):
    business_name: str | None = Field(default=None, min_length=2, max_length=200)
    industry_type: str | None = None
    sub_industry: str | None = None
    business_description: str | None = None
    district: str | None = None
    city: str | None = None
    pincode: str | None = None
    address: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    website: str | None = None
    annual_turnover: Decimal | None = None
    notes: str | None = None
    assigned_officer: UUID | None = None


class MSMEResponse(IDMixin, TimestampMixin):
    tenant_id: UUID
    business_name: str
    gstin: str
    pan: str
    industry_type: str
    sub_industry: str | None
    state: str
    district: str | None
    city: str | None
    pincode: str | None
    registration_date: date
    email: str | None
    phone: str | None
    msme_category: str | None
    annual_turnover: Decimal | None
    status: str
    risk_tier: str | None
    data_completeness: int
    latest_risk_score: Decimal | None
    latest_ews_score: Decimal | None
    created_by: UUID
    assigned_officer: UUID | None


class MSMEListResponse(IDMixin, TimestampMixin):
    """Lightweight response for list views."""
    business_name: str
    gstin: str
    industry_type: str
    state: str
    status: str
    risk_tier: str | None
    data_completeness: int
    latest_risk_score: Decimal | None
    latest_ews_score: Decimal | None


class MSMESearchParams(BaseSchema):
    query: str | None = None
    industry_type: str | None = None
    state: str | None = None
    risk_tier: str | None = None
    status: str | None = None
    assigned_officer: UUID | None = None
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
