"""
deps.py
-------
FastAPI dependency injection providers.

Using FastAPI's Depends() pattern means:
  - Clients share one Redis/TimescaleDB connection pool (efficient)
  - Tests can override deps with mock objects (testable)
  - Connection lifecycle is managed by the app, not each route
"""

import os
import time
from typing import Generator

from storage.redis_client import RedisClient
from storage.timescale_client import TimescaleClient

# Module-level singletons — created once on startup
_redis: RedisClient | None = None
_timescale: TimescaleClient | None = None
_start_time: float = time.monotonic()
_tickers: list[str] = []


def init_dependencies() -> None:
    """Called once at app startup to initialize shared clients."""
    global _redis, _timescale, _tickers

    _redis = RedisClient()
    _timescale = TimescaleClient()
    _tickers = [
        t.strip().upper()
        for t in os.getenv("WATCH_TICKERS", "AAPL,MSFT,GOOGL,AMZN,NVDA").split(",")
        if t.strip()
    ]


def shutdown_dependencies() -> None:
    """Called on app shutdown to close connections gracefully."""
    global _redis, _timescale
    if _redis:
        _redis.close()
    if _timescale:
        _timescale.close()


# FastAPI dependency functions — each returns the singleton

def get_redis() -> RedisClient:
    return _redis


def get_timescale() -> TimescaleClient:
    return _timescale


def get_tickers() -> list[str]:
    return _tickers


def get_start_time() -> float:
    return _start_time
