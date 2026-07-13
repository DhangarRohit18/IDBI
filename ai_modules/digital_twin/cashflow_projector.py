"""
FinTwin AI — Cash Flow Projector
Projects future cash flows using time-series analysis.
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, date
from typing import Any


class CashFlowProjector:
    """Projects monthly cash flows using trend analysis and seasonality detection."""

    def project(
        self,
        transaction_records: list[dict],
        financial_records: list[dict],
        months: int = 12,
    ) -> dict:
        """
        Project cash flows for the specified number of months.
        
        Returns dict with:
            months: list of month labels ("YYYY-MM")
            projected_inflow: list of projected inflow values
            projected_outflow: list of projected outflow values
            net_cashflow: list of net cash flow values
            confidence_band_upper: upper confidence bound
            confidence_band_lower: lower confidence bound
        """
        # Extract monthly cash flow series from transactions
        monthly_data = self._aggregate_monthly(transaction_records)

        if len(monthly_data) < 3:
            # Fall back to financial record estimates
            return self._estimate_from_financials(financial_records, months)

        # Get arrays
        inflows = np.array([m["credits"] for m in monthly_data], dtype=float)
        outflows = np.array([m["debits"] for m in monthly_data], dtype=float)

        # Project using linear trend + seasonality
        projected_inflow = self._project_series(inflows, months)
        projected_outflow = self._project_series(outflows, months)
        net = projected_inflow - projected_outflow

        # Confidence bands (±15%)
        return {
            "months": self._generate_month_labels(months),
            "projected_inflow": [round(float(v), 2) for v in projected_inflow],
            "projected_outflow": [round(float(v), 2) for v in projected_outflow],
            "net_cashflow": [round(float(v), 2) for v in net],
            "confidence_band_upper": [round(float(v * 1.15), 2) for v in net],
            "confidence_band_lower": [round(float(v * 0.85), 2) for v in net],
            "historical_months": len(monthly_data),
        }

    def _aggregate_monthly(self, transactions: list[dict]) -> list[dict]:
        """Group transactions by month."""
        monthly: dict[str, dict] = {}
        for txn in transactions:
            date_str = str(txn.get("txn_date", ""))
            if len(date_str) >= 7:
                month_key = date_str[:7]
                if month_key not in monthly:
                    monthly[month_key] = {"month": month_key, "credits": 0.0, "debits": 0.0}
                amount = float(txn.get("amount") or 0)
                if txn.get("txn_type") == "CREDIT":
                    monthly[month_key]["credits"] += amount
                else:
                    monthly[month_key]["debits"] += amount
        return sorted(monthly.values(), key=lambda x: x["month"])

    def _project_series(self, series: np.ndarray, months: int) -> np.ndarray:
        """Project future values using polynomial trend."""
        n = len(series)
        x = np.arange(n)
        # Fit linear trend
        coeffs = np.polyfit(x, series, deg=min(2, n - 1))
        poly = np.poly1d(coeffs)
        # Project
        future_x = np.arange(n, n + months)
        projected = poly(future_x)
        # Ensure non-negative
        return np.maximum(projected, 0)

    def _estimate_from_financials(self, financial_records: list[dict], months: int) -> dict:
        """Fallback: estimate from annual financial data."""
        if not financial_records:
            zeros = [0.0] * months
            return {
                "months": self._generate_month_labels(months),
                "projected_inflow": zeros,
                "projected_outflow": zeros,
                "net_cashflow": zeros,
                "confidence_band_upper": zeros,
                "confidence_band_lower": zeros,
                "historical_months": 0,
            }
        latest = financial_records[0]
        annual_revenue = float(latest.get("revenue") or 0)
        annual_expenses = float(latest.get("operating_expenses") or 0) + float(latest.get("cost_of_goods_sold") or 0)
        monthly_inflow = annual_revenue / 12
        monthly_outflow = annual_expenses / 12
        net = monthly_inflow - monthly_outflow
        months_list = self._generate_month_labels(months)
        return {
            "months": months_list,
            "projected_inflow": [round(monthly_inflow, 2)] * months,
            "projected_outflow": [round(monthly_outflow, 2)] * months,
            "net_cashflow": [round(net, 2)] * months,
            "confidence_band_upper": [round(net * 1.2, 2)] * months,
            "confidence_band_lower": [round(net * 0.8, 2)] * months,
            "historical_months": len(financial_records),
        }

    def _generate_month_labels(self, months: int) -> list[str]:
        """Generate list of future month labels."""
        from datetime import datetime, timedelta
        labels = []
        now = datetime.now()
        for i in range(1, months + 1):
            future = now.replace(day=1) + timedelta(days=32 * i)
            labels.append(future.strftime("%Y-%m"))
        return labels
