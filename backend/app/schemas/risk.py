from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.schemas.common import BaseSchema, IDMixin


class RiskPredictionResponse(IDMixin):
    msme_id: UUID
    twin_id: UUID | None
    risk_score: Decimal
    probability_of_default: Decimal
    recovery_probability: Decimal | None
    confidence_score: Decimal | None
    risk_tier: str
    lgbm_score: Decimal | None
    xgb_score: Decimal | None
    catboost_score: Decimal | None
    rf_score: Decimal | None
    nn_score: Decimal | None
    feature_importance: dict | None
    shap_values: dict | None
    lime_explanation: dict | None
    top_risk_factors: dict | None
    model_version: str
    predicted_at: datetime


class SHAPExplanation(BaseSchema):
    """SHAP waterfall and force plot data."""
    base_value: float
    output_value: float
    features: list[dict]  # [{name, value, shap_value, contribution_pct}]
    waterfall_data: dict
    force_plot_data: dict
    plain_language_summary: str


class RiskPredictRequest(BaseSchema):
    force_repredict: bool = False
