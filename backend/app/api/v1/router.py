"""
FinTwin AI — API v1 Main Router
Aggregates all module sub-routers.
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    users,
    msme,
    documents,
    digital_twin,
    risk,
    simulation,
    agents,
    portfolio,
    ews,
    notifications,
    reports,
    audit,
    settings as settings_router,
    websocket,
)

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(msme.router, prefix="/msme", tags=["MSME Management"])
api_v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(digital_twin.router, prefix="/digital-twin", tags=["Digital Twin"])
api_v1_router.include_router(risk.router, prefix="/risk", tags=["Risk Prediction"])
api_v1_router.include_router(simulation.router, prefix="/simulation", tags=["Scenario Simulation"])
api_v1_router.include_router(agents.router, prefix="/agents", tags=["Multi-Agent AI"])
api_v1_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio Dashboard"])
api_v1_router.include_router(ews.router, prefix="/ews", tags=["Early Warning System"])
api_v1_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_v1_router.include_router(settings_router.router, prefix="/settings", tags=["Settings"])
api_v1_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
