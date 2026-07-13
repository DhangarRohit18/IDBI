"""
FinTwin AI — Digital Twin Generation Engine
Orchestrates all components to produce a complete AI Digital Twin.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

import numpy as np
import structlog

from ai_modules.digital_twin.feature_engineer import FeatureEngineer
from ai_modules.digital_twin.health_calculator import HealthScoreCalculator
from ai_modules.digital_twin.cashflow_projector import CashFlowProjector
from ai_modules.digital_twin.benchmark_comparator import BenchmarkComparator
from ai_modules.digital_twin.narrative_generator import NarrativeGenerator
from app.config import settings

logger = structlog.get_logger(__name__)

DT_MODEL_VERSION = "1.0.0"


class DigitalTwinEngine:
    """Orchestrates Digital Twin generation from raw MSME financial data."""

    def __init__(self) -> None:
        self.feature_engineer = FeatureEngineer()
        self.health_calculator = HealthScoreCalculator()
        self.cashflow_projector = CashFlowProjector()
        self.benchmark_comparator = BenchmarkComparator()
        self.narrative_generator = NarrativeGenerator()

    async def generate(
        self,
        msme_data: dict,
        financial_records: list[dict],
        gst_records: list[dict],
        credit_records: list[dict],
        transaction_records: list[dict],
        industry_type: str,
        state: str,
    ) -> dict:
        """
        Generate a complete Digital Twin output.
        
        Args:
            msme_data: Core MSME profile information
            financial_records: Historical financial statements
            gst_records: GST filing history
            credit_records: Credit bureau records
            transaction_records: Bank transaction history
            industry_type: Industry for benchmark comparison
            state: Geographic state
            
        Returns:
            Complete Digital Twin data dictionary
        """
        start_time = time.perf_counter()
        logger.info("Starting Digital Twin generation", msme_id=msme_data.get("id"))

        # Step 1: Feature engineering — extract 47 ML features
        features = self.feature_engineer.extract(
            financial_records=financial_records,
            gst_records=gst_records,
            credit_records=credit_records,
            transaction_records=transaction_records,
            msme_data=msme_data,
        )

        # Step 2: Health score computation
        health_scores = self.health_calculator.compute(features)

        # Step 3: Cash flow projection (3/6/12 months)
        cashflow_3m = self.cashflow_projector.project(
            transaction_records, financial_records, months=3
        )
        cashflow_6m = self.cashflow_projector.project(
            transaction_records, financial_records, months=6
        )
        cashflow_12m = self.cashflow_projector.project(
            transaction_records, financial_records, months=12
        )

        # Step 4: Industry benchmark comparison
        benchmark = self.benchmark_comparator.compare(
            features=features,
            industry_type=industry_type,
            state=state,
        )

        # Step 5: LLM narrative generation
        narrative = await self.narrative_generator.generate(
            msme_data=msme_data,
            health_scores=health_scores,
            features=features,
            benchmark=benchmark,
        )

        # Step 6: Determine data coverage
        data_coverage_months = self._compute_data_coverage(financial_records, transaction_records)

        # Step 7: Confidence level
        confidence = self._determine_confidence(data_coverage_months, len(financial_records))

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Digital Twin generated",
            duration_ms=duration_ms,
            health_score=health_scores["overall"],
        )

        return {
            "health_score": round(health_scores["overall"], 2),
            "growth_trend_index": round(health_scores["growth_trend"], 2),
            "risk_index": round(health_scores["risk_index"], 2),
            "liquidity_score": round(health_scores["liquidity"], 2),
            "profitability_score": round(health_scores["profitability"], 2),
            "solvency_score": round(health_scores["solvency"], 2),
            "compliance_score": round(health_scores["compliance"], 2),
            "cashflow_3m": cashflow_3m,
            "cashflow_6m": cashflow_6m,
            "cashflow_12m": cashflow_12m,
            "industry_benchmark": benchmark,
            "feature_vector": features,
            "narrative_summary": narrative,
            "data_coverage_months": data_coverage_months,
            "confidence_level": confidence,
            "model_version": DT_MODEL_VERSION,
            "generation_duration_ms": duration_ms,
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(days=settings.DIGITAL_TWIN_EXPIRY_DAYS)
            ).isoformat(),
        }

    def _compute_data_coverage(self, financial_records: list, transactions: list) -> int:
        """Estimate how many months of data are available."""
        if not financial_records and not transactions:
            return 0
        months = len(financial_records) * 3  # Approximate quarterly records
        if transactions:
            from datetime import datetime
            dates = []
            for t in transactions:
                try:
                    dates.append(datetime.fromisoformat(t.get("txn_date", "")))
                except (ValueError, TypeError):
                    continue
            if dates:
                span = (max(dates) - min(dates)).days // 30
                months = max(months, span)
        return min(months, 60)  # Cap at 60 months

    def _determine_confidence(self, coverage_months: int, fin_record_count: int) -> str:
        if coverage_months >= 24 and fin_record_count >= 4:
            return "HIGH"
        elif coverage_months >= 12 and fin_record_count >= 2:
            return "MEDIUM"
        return "LOW"
