"""
FinTwin AI — Feature Pipeline
Transforms feature dictionaries to model-ready numpy arrays.
"""

from __future__ import annotations

import numpy as np

from ai_modules.digital_twin.feature_engineer import FeatureEngineer


class FeaturePipeline:
    """Transforms feature dictionaries into ML model inputs."""

    def __init__(self) -> None:
        self.feature_engineer = FeatureEngineer()
        self._scaler_params: dict | None = None

    def transform(self, features: dict[str, float]) -> np.ndarray:
        """Convert feature dict to normalized numpy array for ML model input."""
        # Convert dict to ordered array
        arr = self.feature_engineer.to_array(features)
        # Replace NaN/inf with 0
        arr = np.nan_to_num(arr, nan=0.0, posinf=5.0, neginf=-5.0)
        return arr.astype(np.float32)

    def fit_transform(self, features_list: list[dict]) -> np.ndarray:
        """Fit scaler and transform a batch of feature dicts (for training)."""
        arrays = np.array([
            self.feature_engineer.to_array(f) for f in features_list
        ])
        arrays = np.nan_to_num(arrays, nan=0.0, posinf=5.0, neginf=-5.0)
        self._scaler_params = {
            "mean": arrays.mean(axis=0),
            "std": arrays.std(axis=0) + 1e-8,
        }
        return (arrays - self._scaler_params["mean"]) / self._scaler_params["std"]
