from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_model import BaseModel


class EWSAlert(BaseModel):
    __tablename__ = "ews_alerts"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Alert Content
    alert_code: Mapped[str] = mapped_column(String(50), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ews_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_data: Mapped[dict | None] = mapped_column(JSONB)
    recommended_action: Mapped[str | None] = mapped_column(Text)

    # Forecast
    default_probability_30d: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    default_probability_60d: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    default_probability_90d: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    # Resolution
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledgement_note: Mapped[str | None] = mapped_column(Text)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="ews_alerts", lazy="noload")
