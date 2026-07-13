from __future__ import annotations
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema, IDMixin


class SimulationRequest(BaseSchema):
    scenario_type: str
    severity_percent: float = Field(ge=1, le=100)
    duration_months: int = Field(ge=1, le=60)
    probability: float = Field(default=1.0, ge=0, le=1)
    scenario_name: str | None = None
    compound_scenarios: list[dict] | None = None


class SimulationResponse(IDMixin):
    msme_id: UUID
    scenario_type: str
    scenario_name: str | None
    severity_percent: float
    duration_months: int
    baseline_risk_score: float | None
    stressed_risk_score: float | None
    baseline_pd: float | None
    stressed_pd: float | None
    baseline_health_score: float | None
    stressed_health_score: float | None
    delta_risk_score: float | None
    delta_pd: float | None
    stress_test_passed: bool | None
    cashflow_comparison: dict | None
    full_simulation_output: dict | None
    duration_ms: int | None


class AgentAnalysisRequest(BaseSchema):
    force_rerun: bool = False


class AgentAnalysisResponse(IDMixin):
    evaluation_id: UUID
    run_id: str
    pipeline_status: str
    fraud_score: float | None
    fraud_flags: list | None
    compliance_score: float | None
    risk_agent_output: dict | None
    fraud_agent_output: dict | None
    financial_agent_output: dict | None
    market_agent_output: dict | None
    compliance_agent_output: dict | None
    recommendation_output: dict | None
    explainability_output: dict | None
    coordinator_output: dict | None
    duration_seconds: int | None
    agents_completed: list | None
    agents_failed: list | None


class EvaluationCreate(BaseSchema):
    loan_amount_requested: float = Field(gt=0)
    loan_tenure_months: int = Field(ge=1, le=300)
    interest_rate: float | None = Field(default=None, ge=1, le=36)
    loan_purpose: str = Field(min_length=3, max_length=200)
    loan_type: str | None = None
    collateral_value: float = Field(default=0, ge=0)
    collateral_type: str | None = None
    collateral_description: str | None = None


class EvaluationDecision(BaseSchema):
    final_decision: str
    decision_notes: str | None = None
    is_override: bool = False
    override_reason_code: str | None = None
    override_reason_text: str | None = Field(default=None, min_length=100)
