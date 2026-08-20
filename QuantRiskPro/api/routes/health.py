"""
routes/health.py
----------------
System health check endpoint. Pings all downstream services.
Used by load balancers, uptime monitors, and Grafana.
"""

import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends

from api.models import HealthResponse, ServiceStatus
from api.deps import get_redis, get_timescale, get_tickers, get_start_time

router = APIRouter(tags=["health"])
logger = structlog.get_logger(__name__)


@router.get("/api/health", response_model=HealthResponse)
async def health_check(
    redis=Depends(get_redis),
    timescale=Depends(get_timescale),
    tickers: list[str] = Depends(get_tickers),
    start_time: float = Depends(get_start_time),
):
    """
    Check health of all downstream services.

    Returns:
      - Redis connectivity and latency
      - TimescaleDB connectivity and latency
      - Number of tickers with live data
      - Server uptime

    Status is "ok" if all services respond, "degraded" if some fail.
    """
    services: dict[str, ServiceStatus] = {}
    overall_ok = True

    # ── Redis check ──────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        redis._client.ping()
        latency = (time.monotonic() - t0) * 1000
        services["redis"] = ServiceStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        services["redis"] = ServiceStatus(status="down", detail=str(e))
        overall_ok = False

    # ── TimescaleDB check ────────────────────────────────────────
    try:
        t0 = time.monotonic()
        conn = timescale._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        timescale._put_conn(conn)
        latency = (time.monotonic() - t0) * 1000
        services["timescaledb"] = ServiceStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        services["timescaledb"] = ServiceStatus(status="down", detail=str(e))
        overall_ok = False

    # ── Live data check ──────────────────────────────────────────
    try:
        prices = redis.get_all_live_prices(tickers)
        tickers_with_data = sum(1 for v in prices.values() if v is not None)
    except Exception:
        tickers_with_data = 0

    uptime = time.monotonic() - start_time
    overall_status = "ok" if overall_ok else "degraded"

    logger.info("health_checked", status=overall_status, tickers_with_data=tickers_with_data)

    return HealthResponse(
        status=overall_status,
        services=services,
        tickers_watched=tickers,
        tickers_with_data=tickers_with_data,
        uptime_seconds=round(uptime, 1),
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
