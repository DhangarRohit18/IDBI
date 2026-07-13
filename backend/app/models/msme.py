from __future__ import annotations
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_model import BaseModel


class MSME(BaseModel):
    __tablename__ = "msmes"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assigned_officer: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Business Identity
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gstin: Mapped[str] = mapped_column(String(15), nullable=False)  # Encrypted
    pan: Mapped[str] = mapped_column(String(10), nullable=False)  # Encrypted
    industry_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sub_industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(6), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Registration
    registration_date: Mapped[date] = mapped_column(Date, nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Contact
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Financial Classification
    msme_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    annual_turnover: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    # Status and Risk
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT", index=True)
    risk_tier: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    data_completeness: Mapped[int] = mapped_column(Integer, default=0)
    latest_twin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("digital_twins.id"), nullable=True
    )
    latest_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    latest_ews_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="msmes", lazy="noload")
    financial_data: Mapped[list] = relationship("FinancialData", back_populates="msme", lazy="noload")
    gst_data: Mapped[list] = relationship("GSTData", back_populates="msme", lazy="noload")
    credit_data: Mapped[list] = relationship("CreditData", back_populates="msme", lazy="noload")
    transactions: Mapped[list] = relationship("BankTransaction", back_populates="msme", lazy="noload")
    digital_twins: Mapped[list] = relationship(
        "DigitalTwin",
        back_populates="msme",
        foreign_keys="DigitalTwin.msme_id",
        lazy="noload"
    )
    loan_evaluations: Mapped[list] = relationship("LoanEvaluation", back_populates="msme", lazy="noload")
    ews_alerts: Mapped[list] = relationship("EWSAlert", back_populates="msme", lazy="noload")
    documents: Mapped[list] = relationship("Document", back_populates="msme", lazy="noload")
    simulations: Mapped[list] = relationship("ScenarioSimulation", back_populates="msme", lazy="noload")
