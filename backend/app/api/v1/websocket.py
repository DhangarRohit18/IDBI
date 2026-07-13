"""
FinTwin AI — WebSocket Endpoints
Real-time portfolio updates and evaluation progress streaming.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.security import decode_access_token
from app.core.websocket_manager import ws_manager

logger = structlog.get_logger(__name__)

router = APIRouter()


async def _authenticate_ws(websocket: WebSocket) -> dict | None:
    """Extract and validate JWT from WebSocket query param."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return None
    try:
        payload = decode_access_token(token)
        return payload
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return None


@router.websocket("/portfolio")
async def portfolio_websocket(websocket: WebSocket) -> None:
    """Real-time portfolio updates WebSocket channel."""
    payload = await _authenticate_ws(websocket)
    if not payload:
        return

    tenant_id = payload["tenant_id"]
    user_id = payload["sub"]
    channel = f"portfolio:{tenant_id}"

    await ws_manager.connect(websocket, tenant_id, user_id, channel)
    logger.info("Portfolio WS connected", user_id=user_id, tenant_id=tenant_id)

    try:
        # Send initial ping
        await websocket.send_json({"type": "connected", "channel": "portfolio"})
        while True:
            # Keep alive — wait for ping or disconnect
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, tenant_id, user_id, channel)


@router.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket) -> None:
    """Real-time notification stream for authenticated user."""
    payload = await _authenticate_ws(websocket)
    if not payload:
        return

    tenant_id = payload["tenant_id"]
    user_id = payload["sub"]
    channel = f"notifications:{user_id}"

    await ws_manager.connect(websocket, tenant_id, user_id, channel)
    logger.info("Notification WS connected", user_id=user_id)

    try:
        await websocket.send_json({"type": "connected", "channel": "notifications"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, tenant_id, user_id, channel)


@router.websocket("/evaluation/{evaluation_id}")
async def evaluation_progress_websocket(
    websocket: WebSocket,
    evaluation_id: UUID,
) -> None:
    """Stream real-time progress for an active loan evaluation."""
    payload = await _authenticate_ws(websocket)
    if not payload:
        return

    tenant_id = payload["tenant_id"]
    user_id = payload["sub"]
    channel = f"evaluation:{str(evaluation_id)}"

    await ws_manager.connect(websocket, tenant_id, user_id, channel)
    logger.info("Evaluation WS connected", evaluation_id=str(evaluation_id))

    try:
        await websocket.send_json({"type": "connected", "evaluation_id": str(evaluation_id)})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, tenant_id, user_id, channel)
