"""
FinTwin AI — Scenario Simulation Engine
Simulates What-If business scenarios and their impact on risk.
"""

from __future__ import annotations

import time
from copy import deepcopy
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


SCENARIO_FEATURE_IMPACTS = {
    "REVENUE_DROP": {
        "revenue_growth_yoy": lambda sev: -sev / 100,
        "net_profit_margin": lambda sev: -(sev / 100) * 0.8,
        "operating_cashflow_ratio": lambda sev: -(sev / 100) * 0.6,
        "current_ratio": lambda sev: -(sev / 100) * 0.5,
        "inflow_trend": lambda sev: -sev / 100,
    },
    "INFLATION": {
        "net_profit_margin": lambda sev: -(sev / 100) * 0.4,
        "operating_cashflow_ratio": lambda sev: -(sev / 100) * 0.3,
        "gross_profit_margin": lambda sev: -(sev / 100) * 0.35,
        "current_ratio": lambda sev: -(sev / 100) * 0.2,
    },
    "INTEREST_RATE_INCREASE": {
        "interest_coverage": lambda sev: -(sev / 100) * 2,
        "debt_service_coverage": lambda sev: -(sev / 100) * 1.5,
        "net_profit_margin": lambda sev: -(sev / 100) * 0.15,
        "operating_cashflow_ratio": lambda sev: -(sev / 100) * 0.1,
    },
    "DELAYED_PAYMENTS": {
        "days_sales_outstanding": lambda sev: sev * 0.5,  # More days outstanding
        "current_ratio": lambda sev: -(sev / 100) * 0.4,
        "cash_ratio": lambda sev: -(sev / 100) * 0.6,
        "inflow_trend": lambda sev: -(sev / 100) * 0.7,
    },
    "SUPPLIER_FAILURE": {
        "revenue_growth_yoy": lambda sev: -(sev / 100) * 0.6,
        "gross_profit_margin": lambda sev: -(sev / 100) * 0.5,
        "operating_cashflow_ratio": lambda sev: -(sev / 100) * 0.4,
        "current_ratio": lambda sev: -(sev / 100) * 0.3,
    },
    "PANDEMIC": {
        "revenue_growth_yoy": lambda sev: -(sev / 100) * 0.9,
        "net_profit_margin": lambda sev: -(sev / 100) * 0.85,
        "operating_cashflow_ratio": lambda sev: -(sev / 100) * 0.80,
        "current_ratio": lambda sev: -(sev / 100) * 0.60,
        "cash_ratio": lambda sev: -(sev / 100) * 0.70,
        "gst_filing_rate": lambda sev: -(sev / 100) * 0.40,
    },
}


class ScenarioEngine:
    """Simulates stress scenarios and computes impact on MSME risk profile."""

    def __init__(self) -> None:
        from ai_modules.risk_prediction.predictor import RiskPredictor
        self.predictor = RiskPredictor()

    async def simulate(
        self,
        features: dict[str, float],
        scenario_type: str,
        severity_percent: float,
        duration_months: int,
        probability: float = 1.0,
    ) -> dict:
        """
        Run a single scenario simulation.
        
        Args:
            features: Current MSME feature dict
            scenario_type: Scenario identifier (REVENUE_DROP, etc.)
            severity_percent: Severity 0-100%
            duration_months: Duration of stress period
            probability: Probability the scenario occurs (0-1)
        """
        start = time.perf_counter()

        # Get baseline prediction
        baseline = await self.predictor.predict(features)

        # Apply scenario stress to features
        stressed_features = self._apply_scenario(
            deepcopy(features), scenario_type, severity_percent, duration_months
        )

        # Get stressed prediction
        stressed = await self.predictor.predict(stressed_features)

        # Build cashflow comparison
        from ai_modules.digital_twin.cashflow_projector import CashFlowProjector
        projector = CashFlowProjector()
        baseline_cf = projector._estimate_from_financials([], duration_months)
        # Apply severity reduction to cashflow
        severity_factor = 1 - (severity_percent / 100) * probability
        stressed_cf = {
            "months": baseline_cf["months"],
            "projected_inflow": [v * severity_factor for v in baseline_cf["projected_inflow"]],
            "projected_outflow": baseline_cf["projected_outflow"],
            "net_cashflow": [v * severity_factor for v in baseline_cf["net_cashflow"]],
        }

        duration_ms = int((time.perf_counter() - start) * 1000)

        # Stress test: passed if stressed PD < 50%
        stress_test_passed = stressed["probability_of_default"] < 0.50

        return {
            "baseline_risk_score": baseline["risk_score"],
            "stressed_risk_score": min(stressed["risk_score"], 1000),
            "baseline_pd": baseline["probability_of_default"],
            "stressed_pd": stressed["probability_of_default"],
            "baseline_health_score": None,
            "stressed_health_score": None,
            "delta_risk_score": stressed["risk_score"] - baseline["risk_score"],
            "delta_pd": stressed["probability_of_default"] - baseline["probability_of_default"],
            "stress_test_passed": stress_test_passed,
            "cashflow_comparison": {
                "baseline": baseline_cf,
                "stressed": stressed_cf,
            },
            "full_simulation_output": {
                "scenario_type": scenario_type,
                "severity_percent": severity_percent,
                "duration_months": duration_months,
                "probability": probability,
                "baseline_model_outputs": baseline,
                "stressed_model_outputs": stressed,
            },
            "duration_ms": duration_ms,
        }

    async def compound_simulate(
        self,
        features: dict[str, float],
        scenarios: list[dict],
    ) -> dict:
        """Simulate multiple stressors simultaneously."""
        stressed = deepcopy(features)
        for scenario in scenarios:
            stressed = self._apply_scenario(
                stressed,
                scenario["scenario_type"],
                scenario["severity_percent"],
                scenario["duration_months"],
            )
        baseline_pred = await self.predictor.predict(features)
        stressed_pred = await self.predictor.predict(stressed)
        return {
            "baseline_pd": baseline_pred["probability_of_default"],
            "stressed_pd": stressed_pred["probability_of_default"],
            "delta_pd": stressed_pred["probability_of_default"] - baseline_pred["probability_of_default"],
            "stress_test_passed": stressed_pred["probability_of_default"] < 0.50,
        }

    def _apply_scenario(
        self,
        features: dict[str, float],
        scenario_type: str,
        severity_percent: float,
        duration_months: int,
    ) -> dict[str, float]:
        """Apply scenario stress adjustments to feature values."""
        impacts = SCENARIO_FEATURE_IMPACTS.get(scenario_type, {})
        # Duration amplifier: longer duration = more impact (up to 2x)
        duration_multiplier = min(1 + (duration_months - 1) / 59, 2.0)

        for feature_name, impact_fn in impacts.items():
            if feature_name in features:
                delta = impact_fn(severity_percent) * duration_multiplier
                features[feature_name] = float(np.clip(
                    features[feature_name] + delta, -10, 100
                ))
        return features
