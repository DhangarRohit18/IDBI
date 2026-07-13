"""
FinTwin AI — Feature Engineering
Extracts 47 standardized financial features for ML model input.
"""

from __future__ import annotations

import numpy as np
from typing import Any


class FeatureEngineer:
    """Extracts and normalizes financial features from raw MSME data."""

    FEATURE_NAMES = [
        # Liquidity (8 features)
        "current_ratio", "quick_ratio", "cash_ratio", "operating_cashflow_ratio",
        "working_capital", "working_capital_turnover", "days_sales_outstanding",
        "days_payable_outstanding",
        # Profitability (7 features)
        "net_profit_margin", "gross_profit_margin", "ebitda_margin", "roa",
        "roe", "roce", "asset_turnover",
        # Solvency (6 features)
        "debt_to_equity", "debt_to_assets", "interest_coverage", "debt_service_coverage",
        "equity_ratio", "financial_leverage",
        # Growth (5 features)
        "revenue_growth_yoy", "profit_growth_yoy", "asset_growth_yoy",
        "cashflow_growth_yoy", "equity_growth_yoy",
        # GST Compliance (5 features)
        "gst_filing_rate", "gst_late_filing_rate", "gst_months_since_last_filing",
        "avg_monthly_gst_turnover", "gst_payment_consistency",
        # Credit (6 features)
        "credit_score_normalized", "credit_utilization", "dpd_90_count",
        "existing_loan_count", "credit_history_months_normalized",
        "recent_enquiries_normalized",
        # Transaction Behavior (5 features)
        "avg_monthly_credits", "credit_debit_ratio", "transaction_regularity",
        "balance_volatility", "inflow_trend",
        # Business Age (5 features)
        "business_age_years", "business_age_category",
        "registration_to_first_loan_months", "loan_count_normalized",
        "annual_turnover_normalized",
    ]

    def extract(
        self,
        financial_records: list[dict],
        gst_records: list[dict],
        credit_records: list[dict],
        transaction_records: list[dict],
        msme_data: dict,
    ) -> dict[str, float]:
        """Extract all 47 features. Missing values default to 0 (handled by models)."""
        features: dict[str, float] = {}

        # Sort financial records by year
        fin = sorted(financial_records, key=lambda x: x.get("fiscal_year", 0), reverse=True)

        # Liquidity features
        features.update(self._extract_liquidity(fin))
        # Profitability features
        features.update(self._extract_profitability(fin))
        # Solvency features
        features.update(self._extract_solvency(fin))
        # Growth features
        features.update(self._extract_growth(fin))
        # GST compliance features
        features.update(self._extract_gst(gst_records))
        # Credit features
        features.update(self._extract_credit(credit_records))
        # Transaction features
        features.update(self._extract_transactions(transaction_records))
        # Business characteristics
        features.update(self._extract_business_info(msme_data))

        return features

    def to_array(self, features: dict[str, float]) -> np.ndarray:
        """Convert feature dict to numpy array in canonical order for ML models."""
        return np.array([features.get(name, 0.0) for name in self.FEATURE_NAMES], dtype=np.float32)

    def _safe_ratio(self, numerator: float | None, denominator: float | None) -> float:
        if numerator is None or denominator is None or denominator == 0:
            return 0.0
        return float(numerator) / float(denominator)

    def _extract_liquidity(self, fin: list[dict]) -> dict[str, float]:
        if not fin:
            return {k: 0.0 for k in [
                "current_ratio", "quick_ratio", "cash_ratio", "operating_cashflow_ratio",
                "working_capital", "working_capital_turnover", "days_sales_outstanding",
                "days_payable_outstanding",
            ]}
        latest = fin[0]
        ca = float(latest.get("current_assets") or 0)
        cl = float(latest.get("current_liabilities") or 1)
        cash = float(latest.get("cash_and_equivalents") or 0)
        inv = float(latest.get("inventory") or 0)
        ar = float(latest.get("accounts_receivable") or 0)
        ap = float(latest.get("accounts_payable") or 1)
        ocf = float(latest.get("operating_cashflow") or 0)
        revenue = float(latest.get("revenue") or 1)
        return {
            "current_ratio": self._safe_ratio(ca, cl),
            "quick_ratio": self._safe_ratio(ca - inv, cl),
            "cash_ratio": self._safe_ratio(cash, cl),
            "operating_cashflow_ratio": self._safe_ratio(ocf, cl),
            "working_capital": ca - cl,
            "working_capital_turnover": self._safe_ratio(revenue, ca - cl),
            "days_sales_outstanding": self._safe_ratio(ar * 365, revenue),
            "days_payable_outstanding": self._safe_ratio(ap * 365, revenue),
        }

    def _extract_profitability(self, fin: list[dict]) -> dict[str, float]:
        if not fin:
            return {k: 0.0 for k in [
                "net_profit_margin", "gross_profit_margin", "ebitda_margin",
                "roa", "roe", "roce", "asset_turnover"
            ]}
        latest = fin[0]
        revenue = float(latest.get("revenue") or 1)
        np_ = float(latest.get("net_profit") or 0)
        gp = float(latest.get("gross_profit") or 0)
        ebitda = float(latest.get("ebitda") or 0)
        assets = float(latest.get("total_assets") or 1)
        equity = float(latest.get("equity") or 1)
        ebit = float(latest.get("ebit") or 0)
        cl = float(latest.get("current_liabilities") or 0)
        return {
            "net_profit_margin": self._safe_ratio(np_, revenue),
            "gross_profit_margin": self._safe_ratio(gp, revenue),
            "ebitda_margin": self._safe_ratio(ebitda, revenue),
            "roa": self._safe_ratio(np_, assets),
            "roe": self._safe_ratio(np_, equity),
            "roce": self._safe_ratio(ebit, assets - cl),
            "asset_turnover": self._safe_ratio(revenue, assets),
        }

    def _extract_solvency(self, fin: list[dict]) -> dict[str, float]:
        if not fin:
            return {k: 0.0 for k in [
                "debt_to_equity", "debt_to_assets", "interest_coverage",
                "debt_service_coverage", "equity_ratio", "financial_leverage"
            ]}
        latest = fin[0]
        debt = float(latest.get("long_term_debt") or 0) + float(latest.get("short_term_debt") or 0)
        equity = float(latest.get("equity") or 1)
        assets = float(latest.get("total_assets") or 1)
        ebit = float(latest.get("ebit") or 0)
        interest = float(latest.get("interest_expense") or 1)
        ebitda = float(latest.get("ebitda") or 0)
        return {
            "debt_to_equity": self._safe_ratio(debt, equity),
            "debt_to_assets": self._safe_ratio(debt, assets),
            "interest_coverage": self._safe_ratio(ebit, interest),
            "debt_service_coverage": self._safe_ratio(ebitda, debt),
            "equity_ratio": self._safe_ratio(equity, assets),
            "financial_leverage": self._safe_ratio(assets, equity),
        }

    def _extract_growth(self, fin: list[dict]) -> dict[str, float]:
        zero = {k: 0.0 for k in [
            "revenue_growth_yoy", "profit_growth_yoy", "asset_growth_yoy",
            "cashflow_growth_yoy", "equity_growth_yoy"
        ]}
        if len(fin) < 2:
            return zero
        current, prior = fin[0], fin[1]
        def growth(curr_val, prev_val):
            curr = float(curr_val or 0)
            prev = float(prev_val or 0)
            if prev == 0:
                return 0.0
            return (curr - prev) / abs(prev)
        return {
            "revenue_growth_yoy": growth(current.get("revenue"), prior.get("revenue")),
            "profit_growth_yoy": growth(current.get("net_profit"), prior.get("net_profit")),
            "asset_growth_yoy": growth(current.get("total_assets"), prior.get("total_assets")),
            "cashflow_growth_yoy": growth(current.get("operating_cashflow"), prior.get("operating_cashflow")),
            "equity_growth_yoy": growth(current.get("equity"), prior.get("equity")),
        }

    def _extract_gst(self, gst_records: list[dict]) -> dict[str, float]:
        if not gst_records:
            return {k: 0.0 for k in [
                "gst_filing_rate", "gst_late_filing_rate", "gst_months_since_last_filing",
                "avg_monthly_gst_turnover", "gst_payment_consistency"
            ]}
        total = len(gst_records)
        filed = sum(1 for r in gst_records if r.get("filing_status") in ("FILED", "LATE_FILED"))
        late = sum(1 for r in gst_records if r.get("filing_status") == "LATE_FILED")
        turnovers = [float(r.get("taxable_turnover") or 0) for r in gst_records]
        avg_turnover = np.mean(turnovers) if turnovers else 0.0
        std_turnover = np.std(turnovers) if len(turnovers) > 1 else 0.0
        consistency = 1.0 - min(self._safe_ratio(std_turnover, avg_turnover if avg_turnover > 0 else 1), 1.0)

        # Months since last filing
        from datetime import datetime
        filed_dates = []
        for r in gst_records:
            if r.get("filed_date"):
                try:
                    filed_dates.append(datetime.fromisoformat(str(r["filed_date"])))
                except ValueError:
                    pass
        if filed_dates:
            days_since = (datetime.now() - max(filed_dates)).days
            months_since = days_since / 30
        else:
            months_since = 12.0

        return {
            "gst_filing_rate": self._safe_ratio(filed, total),
            "gst_late_filing_rate": self._safe_ratio(late, total),
            "gst_months_since_last_filing": months_since,
            "avg_monthly_gst_turnover": avg_turnover,
            "gst_payment_consistency": consistency,
        }

    def _extract_credit(self, credit_records: list[dict]) -> dict[str, float]:
        if not credit_records:
            return {k: 0.0 for k in [
                "credit_score_normalized", "credit_utilization", "dpd_90_count",
                "existing_loan_count", "credit_history_months_normalized",
                "recent_enquiries_normalized"
            ]}
        latest = credit_records[0]
        score = float(latest.get("credit_score") or 300)
        return {
            "credit_score_normalized": (score - 300) / 600,  # Normalize 300-900 to 0-1
            "credit_utilization": float(latest.get("credit_utilization") or 0) / 100,
            "dpd_90_count": float(latest.get("dpd_90") or 0),
            "existing_loan_count": float(latest.get("existing_loan_count") or 0),
            "credit_history_months_normalized": min(float(latest.get("credit_history_months") or 0) / 120, 1.0),
            "recent_enquiries_normalized": min(float(latest.get("recent_enquiries") or 0) / 10, 1.0),
        }

    def _extract_transactions(self, transactions: list[dict]) -> dict[str, float]:
        if not transactions:
            return {k: 0.0 for k in [
                "avg_monthly_credits", "credit_debit_ratio", "transaction_regularity",
                "balance_volatility", "inflow_trend"
            ]}
        credits = [float(t.get("amount") or 0) for t in transactions if t.get("txn_type") == "CREDIT"]
        debits = [float(t.get("amount") or 0) for t in transactions if t.get("txn_type") == "DEBIT"]
        balances = [float(t.get("balance") or 0) for t in transactions if t.get("balance") is not None]

        total_credits = sum(credits)
        total_debits = sum(debits)
        avg_monthly_credits = total_credits / max(len(set([t.get("txn_date", "")[:7] for t in transactions])), 1)

        # Trend: compare first half vs second half
        mid = len(credits) // 2
        inflow_trend = 0.0
        if mid > 0 and len(credits) > mid:
            first_half_avg = np.mean(credits[:mid]) if credits[:mid] else 0
            second_half_avg = np.mean(credits[mid:]) if credits[mid:] else 0
            inflow_trend = self._safe_ratio(second_half_avg - first_half_avg, first_half_avg if first_half_avg > 0 else 1)

        return {
            "avg_monthly_credits": avg_monthly_credits,
            "credit_debit_ratio": self._safe_ratio(total_credits, total_debits if total_debits > 0 else 1),
            "transaction_regularity": min(len(transactions) / 100, 1.0),
            "balance_volatility": float(np.std(balances)) if len(balances) > 1 else 0.0,
            "inflow_trend": inflow_trend,
        }

    def _extract_business_info(self, msme_data: dict) -> dict[str, float]:
        from datetime import date
        reg_date = msme_data.get("registration_date")
        age_years = 0.0
        if reg_date:
            try:
                if isinstance(reg_date, str):
                    reg_date = date.fromisoformat(reg_date)
                age_years = (date.today() - reg_date).days / 365.25
            except (ValueError, TypeError):
                pass

        category_map = {"MICRO": 0, "SMALL": 1, "MEDIUM": 2}
        category = category_map.get(msme_data.get("msme_category", "MICRO"), 0)
        turnover = float(msme_data.get("annual_turnover") or 0)

        return {
            "business_age_years": age_years,
            "business_age_category": min(age_years / 20, 1.0),
            "registration_to_first_loan_months": min(age_years * 12, 60),
            "loan_count_normalized": 0.0,  # Updated from credit records
            "annual_turnover_normalized": min(turnover / 100_000_000, 1.0),  # Normalize to 10Cr
        }
