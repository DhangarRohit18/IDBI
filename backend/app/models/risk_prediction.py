from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_model import BaseModel


class RiskPrediction(BaseModel):
    __tablename__ = "risk_predictions"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    twin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("digital_twins.id"), nullable=True
    )
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_evaluations.id"), nullable=True
    )

    # Outputs
    risk_score: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    probability_of_default: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    recovery_probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    risk_tier: Mapped[str] = mapped_column(String(20), nullable=False)

    # Individual Model Outputs
    lgbm_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    xgb_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    catboost_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    rf_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    nn_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    # Explainability
    feature_importance: Mapped[dict | None] = mapped_column(JSONB)
    shap_values: Mapped[dict | None] = mapped_column(JSONB)
    lime_explanation: Mapped[dict | None] = mapped_column(JSONB)
    top_risk_factors: Mapped[dict | None] = mapped_column(JSONB)

    # Metadata
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    features_used: Mapped[int | None] = mapped_column(Integer)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", lazy="noload")
    twin: Mapped["DigitalTwin"] = relationship("DigitalTwin", back_populates="risk_predictions", lazy="noload")
