from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_model import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_values: Mapped[dict | None] = mapped_column(JSONB)
    new_values: Mapped[dict | None] = mapped_column(JSONB)
    diff: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    description: Mapped[str | None] = mapped_column(Text)


class Document(BaseModel):
    __tablename__ = "documents"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="UPLOADED", nullable=False)
    extracted_data: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    fiscal_year: Mapped[int | None] = mapped_column()
    is_malware_clean: Mapped[bool | None] = mapped_column()
    processed_by: Mapped[str | None] = mapped_column(String(50))

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="documents", lazy="noload")


class ScenarioSimulation(BaseModel):
    __tablename__ = "scenario_simulations"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_evaluations.id")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Configuration
    scenario_name: Mapped[str | None] = mapped_column(String(200))
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity_percent: Mapped[float] = mapped_column(nullable=False)
    duration_months: Mapped[int] = mapped_column(nullable=False)
    probability: Mapped[float] = mapped_column(default=1.0)
    compound_scenarios: Mapped[dict | None] = mapped_column(JSONB)

    # Baseline
    baseline_risk_score: Mapped[float | None] = mapped_column()
    baseline_pd: Mapped[float | None] = mapped_column()
    baseline_health_score: Mapped[float | None] = mapped_column()
    baseline_cashflow: Mapped[dict | None] = mapped_column(JSONB)

    # Stressed State
    stressed_risk_score: Mapped[float | None] = mapped_column()
    stressed_pd: Mapped[float | None] = mapped_column()
    stressed_health_score: Mapped[float | None] = mapped_column()
    stressed_cashflow: Mapped[dict | None] = mapped_column(JSONB)

    # Results
    delta_risk_score: Mapped[float | None] = mapped_column()
    delta_pd: Mapped[float | None] = mapped_column()
    stress_test_passed: Mapped[bool | None] = mapped_column()
    cashflow_comparison: Mapped[dict | None] = mapped_column(JSONB)
    full_simulation_output: Mapped[dict | None] = mapped_column(JSONB)
    duration_ms: Mapped[int | None] = mapped_column()

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="simulations", lazy="noload")


class Report(BaseModel):
    __tablename__ = "reports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str | None] = mapped_column(String(300))
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    storage_key: Mapped[str | None] = mapped_column(Text)
    file_size: Mapped[int | None] = mapped_column()
    error_message: Mapped[str | None] = mapped_column(Text)
