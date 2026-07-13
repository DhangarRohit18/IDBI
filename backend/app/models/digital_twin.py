from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_model import BaseModel


class DigitalTwin(BaseModel):
    __tablename__ = "digital_twins"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Composite Scores
    health_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    growth_trend_index: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    risk_index: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    liquidity_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    profitability_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    solvency_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    compliance_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))

    # Projections
    cashflow_3m: Mapped[dict | None] = mapped_column(JSONB)
    cashflow_6m: Mapped[dict | None] = mapped_column(JSONB)
    cashflow_12m: Mapped[dict | None] = mapped_column(JSONB)

    # Benchmarks
    industry_benchmark: Mapped[dict | None] = mapped_column(JSONB)
    peer_group_id: Mapped[str | None] = mapped_column(String(100))

    # ML Features
    feature_vector: Mapped[dict | None] = mapped_column(JSONB)
    qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Metadata
    narrative_summary: Mapped[str | None] = mapped_column(Text)
    data_coverage_months: Mapped[int | None] = mapped_column(Integer)
    confidence_level: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="GENERATING", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_duration_ms: Mapped[int | None] = mapped_column(Integer)
    model_version: Mapped[str | None] = mapped_column(String(50))

    # Relationships
    msme: Mapped["MSME"] = relationship(
        "MSME", back_populates="digital_twins",
        foreign_keys=[msme_id], lazy="noload"
    )
    risk_predictions: Mapped[list] = relationship(
        "RiskPrediction", back_populates="twin", lazy="noload"
    )
