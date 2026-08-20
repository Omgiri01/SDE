"""
websocket_manager.py
--------------------
Manages all active WebSocket connections and broadcasts live updates.

Design:
  - ConnectionManager holds a set of active WebSocket connections
  - Background task polls Redis every second for price changes
  - On change: broadcasts update to all connected clients
  - Handles client disconnect gracefully (removes from set)

This is the pub-sub pattern used by Bloomberg Terminal, Robinhood, etc.
Redis is the shared state between the ingestion pipeline and the WS broadcaster.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """
    Tracks active WebSocket connections and broadcasts messages.

    Thread-safety: FastAPI runs in an async event loop. All operations
    here are coroutines — no threading needed.
    """

    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._connection_count = 0
        self._message_count = 0

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        self._connection_count += 1
        logger.info("ws_client_connected", total=len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.info("ws_client_disconnected", remaining=len(self._connections))

    async def broadcast(self, data: dict) -> None:
        """Send message to all connected clients. Remove stale connections."""
        if not self._connections:
            return

        message = json.dumps(data)
        dead = set()

        for ws in self._connections:
            try:
                await ws.send_text(message)
                self._message_count += 1
            except Exception:
                dead.add(ws)

        for ws in dead:
            self._connections.discard(ws)

    async def send_personal(self, ws: WebSocket, data: dict) -> None:
        """Send message to a single client."""
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            self.disconnect(ws)

    @property
    def active_connections(self) -> int:
        return len(self._connections)


# Singleton — shared across all routes
manager = ConnectionManager()


async def live_price_broadcaster(redis_client, tickers: list[str]) -> None:
    """
    Background coroutine: polls Redis every second and broadcasts
    price updates to all connected WebSocket clients.

    This is what makes the dashboard "live" — prices appear to move
    in real time even though we're just polling Redis.
    """
    prev_prices: dict[str, Optional[float]] = {t: None for t in tickers}

    while True:
        try:
            if manager.active_connections > 0:
                # Fetch all prices in one Redis pipeline call
                prices = redis_client.get_all_live_prices(tickers)

                updates = []
                for symbol, data in prices.items():
                    if data is None:
                        continue

                    current = data.get("close")
                    if current is None:
                        continue

                    prev = prev_prices.get(symbol)
                    change_pct = None
                    if prev and prev > 0:
                        change_pct = round((current - prev) / prev * 100, 4)

                    updates.append({
                        "symbol": symbol,
                        "price": current,
                        "change_pct": change_pct,
                        "volume": data.get("volume"),
                        "vwap": data.get("vwap"),
                        "timestamp": data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                    })

                    prev_prices[symbol] = current

                if updates:
                    await manager.broadcast({
                        "type": "price_update",
                        "payload": updates,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

            # Also broadcast any active risk alerts
            await _broadcast_alerts(redis_client, tickers)

        except Exception as e:
            logger.error("broadcaster_error", error=str(e))

        await asyncio.sleep(1.0)  # 1-second poll interval


async def _broadcast_alerts(redis_client, tickers: list[str]) -> None:
    """Check risk cache and broadcast active alerts to clients."""
    if manager.active_connections == 0:
        return

    try:
        all_metrics = redis_client.get_all_risk_metrics(tickers)
        active_alerts = []

        for symbol, metrics in all_metrics.items():
            if metrics and metrics.get("alerts"):
                for alert in metrics["alerts"]:
                    active_alerts.append({
                        "symbol": symbol,
                        "alert": alert,
                        "severity": "warning",
                    })

        if active_alerts:
            await manager.broadcast({
                "type": "risk_alerts",
                "payload": active_alerts,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except Exception:
        pass  # Don't let alert failures crash the price broadcaster
