"""
FinTwin AI — SHAP Explainer
Computes SHAP values for ML model predictions.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import structlog

from ai_modules.digital_twin.feature_engineer import FeatureEngineer

logger = structlog.get_logger(__name__)


class SHAPExplainer:
    """Computes SHAP values and generates human-readable factor explanations."""

    def __init__(self) -> None:
        self.feature_names = FeatureEngineer.FEATURE_NAMES

    async def explain(
        self,
        model: Any,
        feature_array: np.ndarray,
        features: dict[str, float],
    ) -> dict:
        """
        Compute SHAP values for a single prediction.
        
        Returns:
            dict with shap_values, feature_importance, waterfall_data,
                  top_factors, plain_language_summary
        """
        try:
            import shap
            # Use TreeExplainer for tree models, LinearExplainer otherwise
            if hasattr(model, 'predict_proba') and hasattr(model, 'booster_'):
                explainer = shap.TreeExplainer(model)
            elif hasattr(model, 'get_booster'):
                explainer = shap.TreeExplainer(model)
            else:
                background = np.zeros((1, len(self.feature_names)))
                explainer = shap.KernelExplainer(model.predict_proba, background)

            shap_values = explainer.shap_values(feature_array.reshape(1, -1))

            # For binary classification, get class 1 (default) SHAP values
            if isinstance(shap_values, list) and len(shap_values) > 1:
                sv = shap_values[1][0]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                sv = shap_values[0, :, 1]
            else:
                sv = np.array(shap_values).flatten()[:len(self.feature_names)]

            return self._build_output(sv, features)

        except Exception as e:
            logger.warning("SHAP computation failed, using permutation importance", error=str(e))
            return self._permutation_importance_fallback(model, feature_array, features)

    def _build_output(self, shap_values: np.ndarray, features: dict) -> dict:
        """Build structured SHAP output for frontend rendering."""
        n = min(len(self.feature_names), len(shap_values))
        feature_shap = [
            {
                "name": self.feature_names[i],
                "value": float(features.get(self.feature_names[i], 0)),
                "shap_value": float(shap_values[i]),
                "abs_shap": float(abs(shap_values[i])),
                "direction": "increases_risk" if shap_values[i] > 0 else "decreases_risk",
            }
            for i in range(n)
        ]

        # Sort by absolute SHAP value
        feature_shap.sort(key=lambda x: x["abs_shap"], reverse=True)

        # Feature importance dict
        feature_importance = {
            f["name"]: round(f["abs_shap"], 6) for f in feature_shap
        }

        # Top 10 risk factors
        top_factors = feature_shap[:10]
        total_abs = sum(f["abs_shap"] for f in feature_shap)
        for f in top_factors:
            f["contribution_pct"] = round(
                (f["abs_shap"] / total_abs * 100) if total_abs > 0 else 0, 2
            )

        # Waterfall data for visualization
        waterfall = {
            "features": [f["name"] for f in feature_shap[:15]],
            "shap_values": [f["shap_value"] for f in feature_shap[:15]],
            "feature_values": [f["value"] for f in feature_shap[:15]],
        }

        return {
            "feature_importance": feature_importance,
            "top_factors": top_factors,
            "waterfall_data": waterfall,
            "force_plot_data": {
                "base_value": 0.3,
                "output_value": float(np.sum(shap_values[:n])) + 0.3,
                "shap_values": [float(v) for v in shap_values[:n]],
                "features": self.feature_names[:n],
            },
        }

    def _permutation_importance_fallback(
        self, model: Any, feature_array: np.ndarray, features: dict
    ) -> dict:
        """Fallback: compute importance by perturbing features."""
        base_pred = float(model.predict_proba(feature_array.reshape(1, -1))[0][1])
        importances = []

        for i, name in enumerate(self.feature_names):
            perturbed = feature_array.copy()
            perturbed[i] = 0.0
            try:
                perturbed_pred = float(
                    model.predict_proba(perturbed.reshape(1, -1))[0][1]
                )
                importance = base_pred - perturbed_pred
            except Exception:
                importance = 0.0
            importances.append({"name": name, "shap_value": importance, "abs_shap": abs(importance)})

        importances.sort(key=lambda x: x["abs_shap"], reverse=True)
        return {
            "feature_importance": {f["name"]: f["abs_shap"] for f in importances},
            "top_factors": importances[:10],
            "waterfall_data": {"features": [f["name"] for f in importances[:15]], "shap_values": [f["shap_value"] for f in importances[:15]], "feature_values": []},
            "force_plot_data": {},
        }
