"""
FinTwin AI — Portfolio Dashboard API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.permissions import require_permission
from app.dependencies import CurrentActiveUser, DBSession
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/summary", summary="Portfolio KPI Summary")
async def get_portfolio_summary(
    current_user: CurrentActiveUser,
    db: DBSession,
    _: CurrentActiveUser = Depends(require_permission("portfolio:read")),
) -> dict:
    """Get real-time portfolio KPIs: total value, NPA%, avg risk, alerts."""
    service = PortfolioService(db)
    return await service.get_summary(
        tenant_id=current_user.tenant_id,
        region=current_user.region if current_user.role == "REGIONAL_MANAGER" else None,
    )


@router.get("/heatmap", summary="State/District Risk Heatmap Data")
async def get_heatmap(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> list[dict]:
    """Get geographic risk data for Leaflet heatmap visualization."""
    service = PortfolioService(db)
    return await service.get_heatmap_data(
        tenant_id=current_user.tenant_id,
        region=current_user.region if current_user.role == "REGIONAL_MANAGER" else None,
    )


@router.get("/risk-distribution", summary="Risk Distribution by Industry")
async def get_risk_distribution(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> dict:
    """Get risk distribution across industry sectors."""
    service = PortfolioService(db)
    return await service.get_industry_risk_distribution(current_user.tenant_id)


@router.get("/default-trend", summary="Default Trend Over Time")
async def get_default_trend(
    current_user: CurrentActiveUser,
    db: DBSession,
    period: str = Query(default="monthly", pattern="^(daily|monthly|quarterly)$"),
    months: int = Query(default=12, ge=1, le=36),
) -> list[dict]:
    """Get default rate trend over time for charts."""
    service = PortfolioService(db)
    return await service.get_default_trend(current_user.tenant_id, period, months)


@router.get("/top-risky", summary="Top Risky MSMEs")
async def get_top_risky(
    current_user: CurrentActiveUser,
    db: DBSession,
    n: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    """Get top N highest-risk MSMEs with one-click drill-down links."""
    service = PortfolioService(db)
    return await service.get_top_risky_msmes(current_user.tenant_id, n)


@router.get("/forecast", summary="Portfolio NPA Forecast")
async def get_npa_forecast(
    current_user: CurrentActiveUser,
    db: DBSession,
) -> dict:
    """Get predicted NPA% for the next 30/60/90 days."""
    service = PortfolioService(db)
    return await service.get_npa_forecast(current_user.tenant_id)
