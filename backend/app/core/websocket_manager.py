"""
FinTwin AI — WebSocket Connection Manager
Manages real-time connections for portfolio updates and notifications.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections organized by tenant and channel."""

    def __init__(self) -> None:
        # tenant_id → channel_name → list of WebSocket connections
        self._connections: dict[str, dict[str, list[WebSocket]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # user_id → list of WebSocket connections
        self._user_connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        user_id: str,
        channel: str,
    ) -> None:
        """Accept a new WebSocket connection and register it."""
        await websocket.accept()
        async with self._lock:
            self._connections[tenant_id][channel].append(websocket)
            self._user_connections[user_id].append(websocket)
        logger.info(
            "WebSocket connected",
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
        )

    async def disconnect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        user_id: str,
        channel: str,
    ) -> None:
        """Remove a WebSocket connection from all registries."""
        async with self._lock:
            channel_conns = self._connections[tenant_id].get(channel, [])
            if websocket in channel_conns:
                channel_conns.remove(websocket)

            user_conns = self._user_connections.get(user_id, [])
            if websocket in user_conns:
                user_conns.remove(websocket)

        logger.info(
            "WebSocket disconnected",
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
        )

    async def broadcast_to_channel(
        self,
        tenant_id: str,
        channel: str,
        message: dict[str, Any],
    ) -> None:
        """Broadcast a message to all connections in a tenant channel."""
        payload = self._build_payload(message)
        disconnected: list[WebSocket] = []

        connections = self._connections[tenant_id].get(channel, [])
        for ws in list(connections):
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        # Clean up dead connections
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if ws in connections:
                        connections.remove(ws)

    async def send_to_user(
        self,
        user_id: str,
        message: dict[str, Any],
    ) -> None:
        """Send a message to all connections of a specific user."""
        payload = self._build_payload(message)
        disconnected: list[WebSocket] = []

        connections = self._user_connections.get(user_id, [])
        for ws in list(connections):
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if ws in connections:
                        connections.remove(ws)

    def _build_payload(self, message: dict[str, Any]) -> str:
        """Serialize message with timestamp."""
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        return json.dumps(message, default=str)

    def get_connection_count(self, tenant_id: str | None = None) -> int:
        """Get total active connection count."""
        if tenant_id:
            return sum(
                len(conns)
                for conns in self._connections[tenant_id].values()
            )
        return sum(
            len(conns)
            for tenant_channels in self._connections.values()
            for conns in tenant_channels.values()
        )


# Singleton instance shared across the application
ws_manager = ConnectionManager()
