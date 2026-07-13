"""
FinTwin AI — LIME Explainer
Local Interpretable Model-Agnostic Explanations.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import structlog

from ai_modules.digital_twin.feature_engineer import FeatureEngineer

logger = structlog.get_logger(__name__)


class LIMEExplainer:
    """Generates LIME local explanations for individual predictions."""

    def __init__(self) -> None:
        self.feature_names = FeatureEngineer.FEATURE_NAMES

    async def explain(
        self,
        model: Any,
        feature_array: np.ndarray,
        features: dict[str, float],
        num_samples: int = 100,
    ) -> dict:
        """Generate LIME explanation for a single prediction."""
        try:
            import lime
            import lime.lime_tabular

            # Create background data (simulate distribution)
            background = np.random.normal(
                loc=feature_array,
                scale=0.1,
                size=(100, len(self.feature_names)),
            )

            explainer = lime.lime_tabular.LimeTabularExplainer(
                background,
                feature_names=self.feature_names,
                class_names=["Non-Default", "Default"],
                mode="classification",
                discretize_continuous=True,
            )

            explanation = explainer.explain_instance(
                feature_array,
                model.predict_proba,
                num_features=10,
                num_samples=num_samples,
            )

            exp_list = explanation.as_list()
            return {
                "explanation": [
                    {
                        "feature_condition": item[0],
                        "weight": round(float(item[1]), 6),
                        "direction": "increases_risk" if item[1] > 0 else "decreases_risk",
                    }
                    for item in exp_list
                ],
                "intercept": round(float(explanation.intercept[1]), 6),
                "local_pred": round(float(explanation.local_pred[1]), 6),
            }
        except Exception as e:
            logger.warning("LIME explanation failed", error=str(e))
            return {"explanation": [], "error": "LIME unavailable"}
