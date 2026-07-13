"""
FinTwin AI — Risk Prediction Ensemble
Orchestrates multiple ML models and produces ensemble prediction.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import numpy as np
import structlog

from ai_modules.risk_prediction.model_registry import ModelRegistry
from ai_modules.risk_prediction.feature_pipeline import FeaturePipeline
from ai_modules.explainability.shap_explainer import SHAPExplainer
from ai_modules.explainability.lime_explainer import LIMEExplainer

logger = structlog.get_logger(__name__)

# Risk tier thresholds (risk score 0-1000)
RISK_TIER_THRESHOLDS = {
    "VERY_LOW": (0, 300),
    "LOW": (300, 500),
    "MEDIUM": (500, 650),
    "HIGH": (650, 800),
    "VERY_HIGH": (800, 1001),
}

# Ensemble model weights
MODEL_WEIGHTS = {
    "lightgbm": 0.30,
    "xgboost": 0.25,
    "catboost": 0.20,
    "random_forest": 0.15,
    "neural_network": 0.10,
}


class RiskPredictor:
    """Ensemble risk predictor combining multiple ML models."""

    def __init__(self) -> None:
        self.registry = ModelRegistry.instance()
        self.feature_pipeline = FeaturePipeline()
        self.shap_explainer = SHAPExplainer()
        self.lime_explainer = LIMEExplainer()

    async def predict(
        self,
        features: dict[str, float],
        msme_id: str | None = None,
    ) -> dict:
        """
        Run ensemble prediction on feature dict.
        
        Returns:
            dict with risk_score, probability_of_default, risk_tier,
            model_scores, shap_values, top_risk_factors
        """
        start = time.perf_counter()
        logger.info("Starting risk prediction", msme_id=msme_id)

        # Convert features to model input array
        feature_array = self.feature_pipeline.transform(features)

        # Get predictions from all available models
        model_scores: dict[str, float] = {}
        models = self.registry.get_all_models()

        for model_name, model in models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(feature_array.reshape(1, -1))[0]
                    pd_score = float(proba[1]) if len(proba) > 1 else float(proba[0])
                else:
                    pd_score = float(model.predict(feature_array.reshape(1, -1))[0])
                model_scores[model_name] = round(np.clip(pd_score, 0, 1), 4)
            except Exception as e:
                logger.warning(f"Model {model_name} prediction failed", error=str(e))
                model_scores[model_name] = None

        # Weighted ensemble PD
        pd = self._compute_ensemble_pd(model_scores)

        # Risk score (0-1000)
        risk_score = pd * 1000

        # Risk tier
        risk_tier = self._get_risk_tier(risk_score)

        # Recovery probability (heuristic: inverse of PD adjusted for collateral)
        recovery_prob = max(0, min(1, (1 - pd) * 0.85))

        # Confidence score (std dev of model scores → lower std = higher confidence)
        valid_scores = [v for v in model_scores.values() if v is not None]
        if len(valid_scores) > 1:
            std_dev = float(np.std(valid_scores))
            confidence = max(0, min(1, 1 - std_dev * 5))
        else:
            confidence = 0.5

        # SHAP explanation
        shap_output = None
        feature_importance = None
        top_risk_factors = None
        try:
            primary_model = self.registry.get_primary_model()
            if primary_model:
                shap_output = await self.shap_explainer.explain(
                    primary_model, feature_array, features
                )
                feature_importance = shap_output.get("feature_importance")
                top_risk_factors = shap_output.get("top_factors")
        except Exception as e:
            logger.warning("SHAP explanation failed", error=str(e))

        # LIME explanation
        lime_output = None
        try:
            primary_model = self.registry.get_primary_model()
            if primary_model:
                lime_output = await self.lime_explainer.explain(
                    primary_model, feature_array, features
                )
        except Exception as e:
            logger.warning("LIME explanation failed", error=str(e))

        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "Risk prediction complete",
            risk_score=round(risk_score, 2),
            pd=round(pd, 4),
            risk_tier=risk_tier,
            duration_ms=duration_ms,
        )

        return {
            "risk_score": round(risk_score, 2),
            "probability_of_default": round(pd, 4),
            "recovery_probability": round(recovery_prob, 4),
            "confidence_score": round(confidence, 4),
            "risk_tier": risk_tier,
            "lgbm_score": model_scores.get("lightgbm"),
            "xgb_score": model_scores.get("xgboost"),
            "catboost_score": model_scores.get("catboost"),
            "rf_score": model_scores.get("random_forest"),
            "nn_score": model_scores.get("neural_network"),
            "feature_importance": feature_importance,
            "shap_values": shap_output,
            "lime_explanation": lime_output,
            "top_risk_factors": top_risk_factors,
            "model_version": self.registry.get_version(),
            "features_used": len(features),
            "predicted_at": datetime.now(timezone.utc).isoformat(),
        }

    def _compute_ensemble_pd(
        self, model_scores: dict[str, float | None]
    ) -> float:
        """Weighted average of model PDs."""
        total_weight = 0.0
        weighted_sum = 0.0
        for model_name, score in model_scores.items():
            if score is not None:
                weight = MODEL_WEIGHTS.get(model_name, 0.1)
                weighted_sum += score * weight
                total_weight += weight
        if total_weight == 0:
            return 0.5  # Default when no models available
        return weighted_sum / total_weight

    def _get_risk_tier(self, risk_score: float) -> str:
        for tier, (low, high) in RISK_TIER_THRESHOLDS.items():
            if low <= risk_score < high:
                return tier
        return "VERY_HIGH"
