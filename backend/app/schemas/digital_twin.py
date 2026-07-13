from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema, IDMixin


class DigitalTwinResponse(IDMixin):
    msme_id: UUID
    version: int
    health_score: Decimal | None
    growth_trend_index: Decimal | None
    risk_index: Decimal | None
    liquidity_score: Decimal | None
    profitability_score: Decimal | None
    solvency_score: Decimal | None
    compliance_score: Decimal | None
    cashflow_3m: dict | None
    cashflow_6m: dict | None
    cashflow_12m: dict | None
    industry_benchmark: dict | None
    narrative_summary: str | None
    data_coverage_months: int | None
    confidence_level: str | None
    status: str
    generated_at: datetime
    expires_at: datetime | None
    generation_duration_ms: int | None
    model_version: str | None


class DigitalTwinDiff(BaseSchema):
    """Comparison between two twin versions."""
    twin_a_id: UUID
    twin_b_id: UUID
    twin_a_version: int
    twin_b_version: int
    health_score_delta: Decimal | None
    risk_index_delta: Decimal | None
    growth_trend_delta: Decimal | None
    metrics_comparison: dict


class GenerateTwinRequest(BaseSchema):
    force_regenerate: bool = Field(default=False)
