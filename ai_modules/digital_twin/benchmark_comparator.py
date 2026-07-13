"""
FinTwin AI — Industry Benchmark Comparator
Compares MSME metrics against industry peer group benchmarks.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

# Fallback benchmarks when database is unavailable
DEFAULT_BENCHMARKS = {
    "Manufacturing": {
        "current_ratio": {"p25": 1.1, "median": 1.5, "p75": 2.1},
        "net_profit_margin": {"p25": 0.03, "median": 0.07, "p75": 0.12},
        "debt_to_equity": {"p25": 0.7, "median": 1.2, "p75": 2.0},
        "revenue_growth_yoy": {"p25": 0.02, "median": 0.08, "p75": 0.18},
    },
    "Retail Trade": {
        "current_ratio": {"p25": 0.9, "median": 1.3, "p75": 1.8},
        "net_profit_margin": {"p25": 0.02, "median": 0.04, "p75": 0.08},
        "debt_to_equity": {"p25": 0.5, "median": 0.9, "p75": 1.5},
        "revenue_growth_yoy": {"p25": 0.03, "median": 0.10, "p75": 0.20},
    },
    "IT Services": {
        "current_ratio": {"p25": 1.5, "median": 2.1, "p75": 3.0},
        "net_profit_margin": {"p25": 0.08, "median": 0.15, "p75": 0.25},
        "debt_to_equity": {"p25": 0.1, "median": 0.3, "p75": 0.8},
        "revenue_growth_yoy": {"p25": 0.10, "median": 0.20, "p75": 0.40},
    },
    "Food Processing": {
        "current_ratio": {"p25": 1.0, "median": 1.4, "p75": 1.9},
        "net_profit_margin": {"p25": 0.02, "median": 0.05, "p75": 0.10},
        "debt_to_equity": {"p25": 0.8, "median": 1.4, "p75": 2.2},
        "revenue_growth_yoy": {"p25": 0.04, "median": 0.10, "p75": 0.22},
    },
}

COMPARED_METRICS = [
    "current_ratio",
    "net_profit_margin",
    "debt_to_equity",
    "revenue_growth_yoy",
    "roa",
    "interest_coverage",
]


class BenchmarkComparator:
    """Compares MSME financial metrics against industry benchmarks."""

    def compare(
        self,
        features: dict[str, float],
        industry_type: str,
        state: str | None = None,
    ) -> dict:
        """
        Compare MSME metrics against industry benchmarks.
        Returns comparison data for each metric.
        """
        benchmarks = DEFAULT_BENCHMARKS.get(industry_type, DEFAULT_BENCHMARKS["Manufacturing"])
        result = {}

        for metric in COMPARED_METRICS:
            msme_value = features.get(metric, 0.0)
            industry_data = benchmarks.get(metric)

            if industry_data:
                percentile = self._compute_percentile(msme_value, industry_data)
                result[metric] = {
                    "msme_value": round(float(msme_value), 4),
                    "industry_median": industry_data["median"],
                    "industry_p25": industry_data["p25"],
                    "industry_p75": industry_data["p75"],
                    "percentile": percentile,
                    "vs_median_pct": round(
                        (msme_value - industry_data["median"]) / max(abs(industry_data["median"]), 0.0001) * 100, 2
                    ),
                    "status": self._status(percentile),
                }
            else:
                result[metric] = {
                    "msme_value": round(float(msme_value), 4),
                    "industry_median": None,
                    "percentile": None,
                    "status": "unknown",
                }

        result["industry_type"] = industry_type
        result["peer_group_size"] = 100  # Placeholder
        return result

    def _compute_percentile(
        self, value: float, benchmarks: dict[str, float]
    ) -> int:
        """Estimate percentile position relative to industry distribution."""
        p25 = benchmarks["p25"]
        median = benchmarks["median"]
        p75 = benchmarks["p75"]

        if value <= p25:
            return max(0, int(25 * (value / max(p25, 0.0001))))
        elif value <= median:
            return 25 + int(25 * (value - p25) / max(median - p25, 0.0001))
        elif value <= p75:
            return 50 + int(25 * (value - median) / max(p75 - median, 0.0001))
        else:
            return min(100, 75 + int(25 * (value - p75) / max(p75, 0.0001)))

    def _status(self, percentile: int | None) -> str:
        if percentile is None:
            return "unknown"
        if percentile >= 75:
            return "above_average"
        elif percentile >= 50:
            return "average"
        elif percentile >= 25:
            return "below_average"
        return "poor"
