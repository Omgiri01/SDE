"""
routes/prices.py
----------------
Price data endpoints. Redis for live; TimescaleDB for history.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query, Depends

from api.models import LivePrice, PriceHistoryResponse, OHLCVBar
from api.deps import get_redis, get_timescale

router = APIRouter(prefix="/api/prices", tags=["prices"])
logger = structlog.get_logger(__name__)


@router.get("/{symbol}", response_model=LivePrice)
async def get_live_price(
    symbol: str,
    redis=Depends(get_redis),
):
    """
    Get the latest cached price for a symbol.

    Reads from Redis — sub-millisecond response.
    Returns 404 if symbol has no data (market closed or not subscribed).
    """
    symbol = symbol.upper()
    data = redis.get_live_price(symbol)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No price data for {symbol}. "
                   f"Market may be closed or symbol not in watch list.",
        )

    return LivePrice(
        symbol=data.get("symbol", symbol),
        close=data.get("close"),
        open=data.get("open"),
        high=data.get("high"),
        low=data.get("low"),
        volume=data.get("volume"),
        vwap=data.get("vwap"),
        timestamp=data.get("timestamp"),
        source="redis",
    )


@router.get("/{symbol}/history", response_model=PriceHistoryResponse)
async def get_price_history(
    symbol: str,
    days: int = Query(default=5, ge=1, le=90, description="Number of days of history"),
    interval: str = Query(default="minute", pattern="^(minute|second)$"),
    timescale=Depends(get_timescale),
):
    """
    Get OHLCV bar history from TimescaleDB.

    Uses TimescaleDB hypertable for fast time-range queries.
    Default: last 5 days of minute bars (P99 query latency < 50ms).
    """
    symbol = symbol.upper()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    bars = timescale.get_price_history(symbol, start=start, end=end, interval=interval)

    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"No historical data for {symbol} in the last {days} days. "
                   f"Ensure the ingestion pipeline is running.",
        )

    ohlcv_bars = [
        OHLCVBar(
            time=b["time"].isoformat() if hasattr(b["time"], "isoformat") else str(b["time"]),
            symbol=symbol,
            open=float(b["open"]),
            high=float(b["high"]),
            low=float(b["low"]),
            close=float(b["close"]),
            volume=float(b["volume"]),
            vwap=float(b["vwap"]) if b.get("vwap") else None,
        )
        for b in bars
    ]

    logger.info("price_history_served", symbol=symbol, bars=len(ohlcv_bars), days=days)

    return PriceHistoryResponse(
        symbol=symbol,
        bars=ohlcv_bars,
        count=len(ohlcv_bars),
        interval=interval,
    )
