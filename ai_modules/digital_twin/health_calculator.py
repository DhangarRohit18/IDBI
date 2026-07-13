"""
FinTwin AI — Business Health Score Calculator
Computes weighted composite health scores from ML features.
"""

from __future__ import annotations

import numpy as np


class HealthScoreCalculator:
    """
    Computes 6 sub-scores and 1 composite health score.
    All scores are on a 0-100 scale.
    """

    # Weights for composite health score
    COMPOSITE_WEIGHTS = {
        "liquidity": 0.25,
        "profitability": 0.25,
        "solvency": 0.20,
        "growth": 0.20,
        "compliance": 0.10,
    }

    def compute(self, features: dict[str, float]) -> dict[str, float]:
        """Compute all health scores from feature dictionary."""
        liquidity = self._compute_liquidity_score(features)
        profitability = self._compute_profitability_score(features)
        solvency = self._compute_solvency_score(features)
        growth = self._compute_growth_score(features)
        compliance = self._compute_compliance_score(features)

        # Risk Index: inverse of health (higher = more risky)
        overall = (
            liquidity * self.COMPOSITE_WEIGHTS["liquidity"]
            + profitability * self.COMPOSITE_WEIGHTS["profitability"]
            + solvency * self.COMPOSITE_WEIGHTS["solvency"]
            + growth * self.COMPOSITE_WEIGHTS["growth"]
            + compliance * self.COMPOSITE_WEIGHTS["compliance"]
        )

        risk_index = 100 - overall  # Higher health = lower risk
        growth_trend = self._compute_growth_trend(features)

        return {
            "overall": round(float(np.clip(overall, 0, 100)), 2),
            "liquidity": round(float(np.clip(liquidity, 0, 100)), 2),
            "profitability": round(float(np.clip(profitability, 0, 100)), 2),
            "solvency": round(float(np.clip(solvency, 0, 100)), 2),
            "growth": round(float(np.clip(growth, 0, 100)), 2),
            "compliance": round(float(np.clip(compliance, 0, 100)), 2),
            "risk_index": round(float(np.clip(risk_index, 0, 100)), 2),
            "growth_trend": round(float(np.clip(growth_trend, -100, 100)), 2),
        }

    def _compute_liquidity_score(self, f: dict) -> float:
        """Score based on current ratio, quick ratio, cash ratio, working capital."""
        current_ratio = f.get("current_ratio", 0)
        quick_ratio = f.get("quick_ratio", 0)
        cash_ratio = f.get("cash_ratio", 0)
        ocf_ratio = f.get("operating_cashflow_ratio", 0)

        # Ideal benchmarks
        cr_score = min((current_ratio / 2.0) * 100, 100)
        qr_score = min((quick_ratio / 1.0) * 100, 100)
        cash_score = min((cash_ratio / 0.5) * 100, 100)
        ocf_score = min((max(ocf_ratio, 0) / 0.3) * 100, 100)

        return float(0.35 * cr_score + 0.30 * qr_score + 0.20 * cash_score + 0.15 * ocf_score)

    def _compute_profitability_score(self, f: dict) -> float:
        npm = f.get("net_profit_margin", 0)
        gpm = f.get("gross_profit_margin", 0)
        ebitda_margin = f.get("ebitda_margin", 0)
        roa = f.get("roa", 0)
        roe = f.get("roe", 0)

        npm_score = min(max(npm * 500, 0), 100)
        gpm_score = min(max(gpm * 200, 0), 100)
        ebitda_score = min(max(ebitda_margin * 400, 0), 100)
        roa_score = min(max(roa * 1000, 0), 100)
        roe_score = min(max(roe * 500, 0), 100)

        return float(0.25 * npm_score + 0.20 * gpm_score + 0.20 * ebitda_score
                     + 0.20 * roa_score + 0.15 * roe_score)

    def _compute_solvency_score(self, f: dict) -> float:
        de = f.get("debt_to_equity", 0)
        da = f.get("debt_to_assets", 0)
        ic = f.get("interest_coverage", 0)
        dscr = f.get("debt_service_coverage", 0)

        # Lower debt ratios = better score
        de_score = max(100 - de * 30, 0)
        da_score = max(100 - da * 150, 0)
        ic_score = min(ic * 15, 100)
        dscr_score = min(max(dscr * 40, 0), 100)

        return float(0.30 * de_score + 0.25 * da_score + 0.25 * ic_score + 0.20 * dscr_score)

    def _compute_growth_score(self, f: dict) -> float:
        rev_growth = f.get("revenue_growth_yoy", 0)
        profit_growth = f.get("profit_growth_yoy", 0)
        asset_growth = f.get("asset_growth_yoy", 0)

        rev_score = min(max(50 + rev_growth * 200, 0), 100)
        profit_score = min(max(50 + profit_growth * 200, 0), 100)
        asset_score = min(max(50 + asset_growth * 200, 0), 100)

        return float(0.45 * rev_score + 0.35 * profit_score + 0.20 * asset_score)

    def _compute_compliance_score(self, f: dict) -> float:
        filing_rate = f.get("gst_filing_rate", 0)
        late_rate = f.get("gst_late_filing_rate", 0)
        months_since = f.get("gst_months_since_last_filing", 6)

        filing_score = filing_rate * 100
        late_penalty = late_rate * 30
        recency_score = max(100 - months_since * 15, 0)

        return float(max(0.5 * filing_score + 0.25 * recency_score - late_penalty, 0))

    def _compute_growth_trend(self, f: dict) -> float:
        """Growth trend index: positive = growing, negative = declining."""
        rev = f.get("revenue_growth_yoy", 0)
        profit = f.get("profit_growth_yoy", 0)
        cashflow = f.get("cashflow_growth_yoy", 0)
        inflow_trend = f.get("inflow_trend", 0)
        return float(0.35 * rev + 0.30 * profit + 0.20 * cashflow + 0.15 * inflow_trend) * 100
