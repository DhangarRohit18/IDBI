"""
FinTwin AI — LLM Narrative Generator
Generates human-readable Digital Twin narrative using Gemini API.
"""

from __future__ import annotations

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

_NARRATIVE_PROMPT = """
You are a senior credit analyst at a bank. Based on the following MSME financial data,
write a concise professional narrative (3-4 paragraphs, maximum 400 words) summarizing:
1. Business health and financial performance
2. Key strengths and risk factors
3. Cash flow and liquidity assessment
4. Overall credit recommendation perspective

MSME Profile:
- Business Name: {business_name}
- Industry: {industry_type}
- State: {state}
- Business Age: {age_years:.1f} years

Health Scores (0-100 scale):
- Overall Health: {health_score}/100
- Liquidity: {liquidity}/100
- Profitability: {profitability}/100
- Solvency: {solvency}/100
- Growth Trend: {growth}/100
- GST Compliance: {compliance}/100
- Risk Index: {risk_index}/100 (higher = more risky)

Key Metrics:
- Revenue Growth (YoY): {revenue_growth:.1%}
- Net Profit Margin: {npm:.1%}
- Current Ratio: {current_ratio:.2f}
- Debt-to-Equity: {dte:.2f}
- Credit Score: {credit_score}
- GST Filing Rate: {gst_rate:.1%}

Write the narrative in a professional, factual tone. Highlight specific numbers.
Do not use generic language. Be specific about this MSME's situation.
"""

FALLBACK_TEMPLATE = """
{business_name} is a {age_years:.0f}-year-old enterprise in the {industry_type} sector based in {state}.

Financial Health Assessment: The business demonstrates an overall health score of {health_score}/100, 
reflecting its composite financial position. Liquidity stands at {liquidity}/100 with a current ratio 
of {current_ratio:.2f}, while profitability registers at {profitability}/100 with a net profit margin 
of {npm:.1%}.

Risk Profile: The solvency score of {solvency}/100 and a debt-to-equity ratio of {dte:.2f} indicate 
{'moderate' if dte < 2 else 'elevated'} financial leverage. GST compliance rate of {gst_rate:.1%} 
{'reflects good regulatory adherence' if gst_rate > 0.85 else 'indicates compliance gaps that require attention'}.

Growth Trajectory: Revenue growth of {revenue_growth:.1%} year-on-year {'shows positive momentum' if revenue_growth > 0 else 'indicates contraction requiring monitoring'}. 
The growth trend index of {growth}/100 {'supports credit confidence' if growth > 50 else 'warrants careful risk assessment'}.
"""


class NarrativeGenerator:
    """Generates business narrative using LLM with fallback to template."""

    def __init__(self) -> None:
        self._llm = None

    async def generate(
        self,
        msme_data: dict,
        health_scores: dict,
        features: dict,
        benchmark: dict,
    ) -> str:
        """Generate narrative using LLM with fallback."""
        context = self._build_context(msme_data, health_scores, features)
        try:
            return await self._generate_with_llm(context)
        except Exception as e:
            logger.warning("LLM narrative generation failed, using template", error=str(e))
            return self._generate_from_template(context)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
    )
    async def _generate_with_llm(self, context: dict) -> str:
        from app.config import settings
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")

        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        prompt = _NARRATIVE_PROMPT.format(**context)
        response = await model.generate_content_async(prompt)
        return response.text.strip()

    def _generate_from_template(self, context: dict) -> str:
        return FALLBACK_TEMPLATE.format(**context).strip()

    def _build_context(self, msme_data: dict, health_scores: dict, features: dict) -> dict:
        from datetime import date
        reg_date = msme_data.get("registration_date")
        age_years = 0.0
        if reg_date:
            try:
                if isinstance(reg_date, str):
                    reg_date = date.fromisoformat(reg_date)
                age_years = (date.today() - reg_date).days / 365.25
            except Exception:
                pass

        credit_score = 0
        # Will be populated from credit records in the engine

        return {
            "business_name": msme_data.get("business_name", "The MSME"),
            "industry_type": msme_data.get("industry_type", "General"),
            "state": msme_data.get("state", "India"),
            "age_years": age_years,
            "health_score": health_scores.get("overall", 0),
            "liquidity": health_scores.get("liquidity", 0),
            "profitability": health_scores.get("profitability", 0),
            "solvency": health_scores.get("solvency", 0),
            "growth": health_scores.get("growth", 0),
            "compliance": health_scores.get("compliance", 0),
            "risk_index": health_scores.get("risk_index", 0),
            "revenue_growth": features.get("revenue_growth_yoy", 0),
            "npm": features.get("net_profit_margin", 0),
            "current_ratio": features.get("current_ratio", 0),
            "dte": features.get("debt_to_equity", 0),
            "credit_score": int(features.get("credit_score_normalized", 0) * 600 + 300),
            "gst_rate": features.get("gst_filing_rate", 0),
        }
