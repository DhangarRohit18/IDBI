from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_model import BaseModel


class LoanEvaluation(BaseModel):
    __tablename__ = "loan_evaluations"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    twin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("digital_twins.id"))
    risk_prediction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_predictions.id")
    )
    agent_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_analyses.id")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Loan Application
    loan_amount_requested: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    loan_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    loan_purpose: Mapped[str] = mapped_column(String(200), nullable=False)
    loan_type: Mapped[str | None] = mapped_column(String(100))
    collateral_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    collateral_type: Mapped[str | None] = mapped_column(String(100))
    collateral_description: Mapped[str | None] = mapped_column(Text)

    # AI Decision
    ai_recommendation: Mapped[str | None] = mapped_column(String(30))
    recommended_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    recommended_tenure: Mapped[int | None] = mapped_column(Integer)
    ai_interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    ai_confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    ai_decision_summary: Mapped[str | None] = mapped_column(Text)
    emi_schedule: Mapped[dict | None] = mapped_column(JSONB)

    # Final Decision
    final_decision: Mapped[str | None] = mapped_column(String(30))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    decision_notes: Mapped[str | None] = mapped_column(Text)
    is_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_reason_code: Mapped[str | None] = mapped_column(String(50))
    override_reason_text: Mapped[str | None] = mapped_column(Text)

    # Status and Timestamps
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="loan_evaluations", lazy="noload")
    risk_prediction: Mapped["RiskPrediction"] = relationship("RiskPrediction", lazy="noload")
    agent_analysis: Mapped["AgentAnalysis"] = relationship(
        "AgentAnalysis", back_populates="evaluation", lazy="noload"
    )


class AgentAnalysis(BaseModel):
    __tablename__ = "agent_analyses"

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_evaluations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Agent Outputs
    risk_agent_output: Mapped[dict | None] = mapped_column(JSONB)
    fraud_agent_output: Mapped[dict | None] = mapped_column(JSONB)
    financial_agent_output: Mapped[dict | None] = mapped_column(JSONB)
    market_agent_output: Mapped[dict | None] = mapped_column(JSONB)
    compliance_agent_output: Mapped[dict | None] = mapped_column(JSONB)
    recommendation_output: Mapped[dict | None] = mapped_column(JSONB)
    explainability_output: Mapped[dict | None] = mapped_column(JSONB)
    coordinator_output: Mapped[dict | None] = mapped_column(JSONB)

    # Scores
    fraud_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    compliance_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    # Pipeline Status
    pipeline_status: Mapped[str] = mapped_column(String(30), default="QUEUED", nullable=False)
    agents_completed: Mapped[list | None] = mapped_column(JSONB)
    agents_failed: Mapped[list | None] = mapped_column(JSONB)
    fraud_flags: Mapped[list | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Performance
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    token_usage: Mapped[int | None] = mapped_column(Integer)
    llm_model_used: Mapped[str | None] = mapped_column(String(100))

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    evaluation: Mapped["LoanEvaluation"] = relationship(
        "LoanEvaluation", back_populates="agent_analysis", lazy="noload"
    )
