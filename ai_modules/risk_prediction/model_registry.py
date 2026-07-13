"""
FinTwin AI — Model Registry
Manages ML model loading, versioning, and access.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "data" / "trained_models"
CURRENT_VERSION = "1.0.0"


class ModelRegistry:
    """Singleton registry for all trained ML models."""

    _instance: "ModelRegistry | None" = None
    _models: dict[str, Any] = {}
    _version: str = CURRENT_VERSION

    @classmethod
    def instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def load_all(self) -> None:
        """Load all trained models into memory."""
        model_files = {
            "lightgbm": "lgbm_risk_v1.pkl",
            "xgboost": "xgb_risk_v1.pkl",
            "catboost": "catboost_risk_v1.pkl",
            "random_forest": "rf_risk_v1.pkl",
            "neural_network": "nn_risk_v1.pkl",
        }

        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        for model_name, filename in model_files.items():
            model_path = MODELS_DIR / filename
            if model_path.exists():
                try:
                    with open(model_path, "rb") as f:
                        self._models[model_name] = pickle.load(f)
                    logger.info(f"Loaded model: {model_name}")
                except Exception as e:
                    logger.error(f"Failed to load model {model_name}", error=str(e))
            else:
                # Create synthetic fallback model for development
                self._models[model_name] = self._create_synthetic_model(model_name)
                logger.warning(f"Model file not found, using synthetic: {model_name}")

    def get_all_models(self) -> dict[str, Any]:
        return self._models

    def get_primary_model(self) -> Any | None:
        return self._models.get("lightgbm")

    def get_version(self) -> str:
        return self._version

    def _create_synthetic_model(self, model_name: str) -> Any:
        """Create a simple synthetic model for development/testing."""
        class SyntheticModel:
            """Deterministic model for development when trained models are unavailable."""
            def __init__(self, name):
                self.name = name
                self.feature_names_ = None

            def predict_proba(self, X):
                # Base PD on key features (liquidity, debt ratio, credit score)
                x = np.array(X).flatten()
                # Use feature positions for rough computation
                liquidity = float(x[0]) if len(x) > 0 else 0.5
                debt = float(x[8]) if len(x) > 8 else 1.0
                credit = float(x[24]) if len(x) > 24 else 0.5
                # Higher liquidity = lower PD, higher debt = higher PD
                pd = np.clip(0.3 - liquidity * 0.1 + debt * 0.05 + (1 - credit) * 0.15, 0.05, 0.95)
                # Add small noise per model for diversity
                noise = {"lightgbm": 0.0, "xgboost": 0.02, "catboost": -0.01,
                        "random_forest": 0.03, "neural_network": -0.02}.get(self.name, 0)
                pd = np.clip(pd + noise, 0.05, 0.95)
                return np.array([[1 - pd, pd]])

            def predict(self, X):
                return self.predict_proba(X)[:, 1]

        return SyntheticModel(model_name)
