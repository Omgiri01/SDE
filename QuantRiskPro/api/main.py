# Author: Om Giri (github.com/Omgiri01)
# QuantRiskPro - Distributed Real-Time Risk Analytics Platform

"""
main.py
-------
QuantRiskPro FastAPI application.

Entry point: python -m api.main

Architecture:
  - REST endpoints via routers (prices, risk, portfolio, health)
  - WebSocket endpoint at /ws/live for dashboard streaming
  - Prometheus metrics at /metrics for Grafana
  - Background task: live price broadcaster (polls Redis → pushes to WS clients)
  - CORS configured for React dev server (localhost:5173)

Startup sequence:
  1. Load .env
  2. Initialize Redis + TimescaleDB connection pools
  3. Start live price broadcaster background task
  4. Begin accepting requests
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager

import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from starlette.responses import Response

load_dotenv()

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = structlog.get_logger(__name__)

from api.deps import init_dependencies, shutdown_dependencies, get_redis, get_tickers
from api.websocket_manager import manager, live_price_broadcaster
from api.routes.prices import router as prices_router
from api.routes.risk import router as risk_router
from api.routes.portfolio import router as portfolio_router
from api.routes.health import router as health_router


# ── Prometheus Metrics ────────────────────────────────────────────────────────
# Guard against duplicate registration when uvicorn reloads the module

def _get_or_create_counter(name, doc, labels=()):
    try:
        return Counter(name, doc, labels)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

def _get_or_create_histogram(name, doc, labels=(), buckets=None):
    try:
        kwargs = {"buckets": buckets} if buckets else {}
        return Histogram(name, doc, labels, **kwargs)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

REQUEST_COUNT = _get_or_create_counter(
    "quantriskpro_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = _get_or_create_histogram(
    "quantriskpro_http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
WS_CONNECTIONS = _get_or_create_counter(
    "quantriskpro_ws_connections_total",
    "Total WebSocket connections accepted",
)


# ── App factory ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage startup and shutdown of shared resources."""
    logger.info("quantriskpro_api_starting")
    init_dependencies()

    tickers = get_tickers()
    redis = get_redis()
    task = asyncio.create_task(live_price_broadcaster(redis, tickers))

    logger.info(
        "quantriskpro_api_ready",
        tickers=tickers,
        docs="http://localhost:8000/docs",
        ws="ws://localhost:8000/ws/live",
        metrics="http://localhost:8000/metrics",
    )

    yield  # App is running

    task.cancel()
    shutdown_dependencies()
    logger.info("quantriskpro_api_stopped")


app = FastAPI(
    title="QuantRiskPro API",
    description=(
        "Real-time stock risk and portfolio intelligence platform. "
        "Serves live prices, institutional risk metrics, and MPT portfolio analytics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS: allow React dev server + any deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Create React App
        "http://localhost:8000",   # Same origin
        "*",                       # Allow all for recruiter demos
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(prices_router)
app.include_router(risk_router)
app.include_router(portfolio_router)
app.include_router(health_router)


# ── Prometheus metrics endpoint ───────────────────────────────────────────────

@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus scrape endpoint. Grafana reads from here."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    """
    WebSocket endpoint for live price + risk streaming.

    Connect from the dashboard:
        const ws = new WebSocket("ws://localhost:8000/ws/live");
        ws.onmessage = (e) => {
            const msg = JSON.parse(e.data);
            if (msg.type === "price_update") updatePriceCards(msg.payload);
            if (msg.type === "risk_alerts") showAlerts(msg.payload);
        };

    Message types:
      { type: "price_update", payload: [{symbol, price, change_pct, ...}] }
      { type: "risk_alerts",  payload: [{symbol, alert, severity}] }
      { type: "connected",    payload: {message, tickers} }
    """
    WS_CONNECTIONS.inc()
    await manager.connect(ws)

    try:
        # Send welcome message with subscribed tickers
        tickers = get_tickers()
        await manager.send_personal(ws, {
            "type": "connected",
            "payload": {
                "message": "Connected to QuantRiskPro live stream",
                "tickers": tickers,
                "active_connections": manager.active_connections,
            },
        })

        # Keep connection alive — the broadcaster handles all outbound messages
        while True:
            # Wait for any client message (ping/pong keepalive)
            data = await ws.receive_text()
            # Echo back any subscription commands the client sends
            if data == "ping":
                await manager.send_personal(ws, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.error("ws_error", error=str(e))
        manager.disconnect(ws)


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "QuantRiskPro API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "websocket": "ws://localhost:8000/ws/live",
        "endpoints": {
            "live_price":        "GET /api/prices/{symbol}",
            "price_history":     "GET /api/prices/{symbol}/history",
            "risk_symbol":       "GET /api/risk/{symbol}",
            "risk_portfolio":    "GET /api/risk/portfolio/aggregate",
            "portfolio":         "GET /api/portfolio",
            "frontier":          "GET /api/portfolio/frontier",
            "rebalance":         "POST /api/portfolio/rebalance",
            "health":            "GET /api/health",
            "metrics":           "GET /metrics",
        },
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
