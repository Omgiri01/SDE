"""
redis_client.py
---------------
Hot cache layer for QuantRiskPro.

What lives in Redis:
  - Live prices        → price:{SYMBOL}          (latest close, vwap, volume)
  - Price history      → prices:history:{SYMBOL}  (ring buffer of last 500 closes)
  - Portfolio values   → portfolio:{id}:value     (live P&L, updated on each tick)
  - Risk metrics cache → risk:{SYMBOL}            (VaR, volatility - computed by risk engine)

Why Redis for this:
  - TimescaleDB is great for historical queries but not for sub-millisecond live reads.
  - The dashboard needs current prices for 10 symbols simultaneously.
  - Redis GET on a key is ~0.1ms vs ~5ms for a PostgreSQL SELECT.
  - For a risk dashboard showing live P&L, that 50x difference is visible.
"""

import os
import json
from typing import Optional

import redis
import structlog

logger = structlog.get_logger(__name__)

# How many historical closes to keep per symbol in the ring buffer
PRICE_HISTORY_SIZE = 500

# TTL for risk metric cache (refresh every 60 seconds)
RISK_CACHE_TTL = 60


class RedisClient:
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = redis.from_url(
            self.url,
            decode_responses=True,      # Always return strings, not bytes
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        # Test connection
        self._client.ping()
        logger.info("redis_connected", url=self.url)

    # ── Live Price Cache ───────────────────────────────────────

    def set_live_price(self, symbol: str, bar: dict) -> None:
        """
        Cache the latest price bar for a symbol.
        Also appends the close price to the symbol's history ring buffer.
        """
        key = f"price:{symbol}"
        price_data = {
            "symbol": symbol,
            "close": bar.get("close"),
            "open": bar.get("open"),
            "high": bar.get("high"),
            "low": bar.get("low"),
            "volume": bar.get("volume"),
            "vwap": bar.get("vwap"),
            "timestamp": bar.get("received_at"),
        }

        pipe = self._client.pipeline()

        # Store latest bar (expires after 1 hour of no updates)
        pipe.setex(key, 3600, json.dumps(price_data))

        # Append close to ring buffer for rolling calculations
        history_key = f"prices:history:{symbol}"
        if bar.get("close"):
            pipe.rpush(history_key, bar["close"])
            pipe.ltrim(history_key, -PRICE_HISTORY_SIZE, -1)  # Keep last 500

        pipe.execute()

    def get_live_price(self, symbol: str) -> Optional[dict]:
        """Get the latest cached price bar for a symbol."""
        raw = self._client.get(f"price:{symbol}")
        return json.loads(raw) if raw else None

    def get_all_live_prices(self, symbols: list[str]) -> dict[str, Optional[dict]]:
        """
        Fetch live prices for multiple symbols in one round-trip.
        Uses Redis pipeline — much faster than N individual GETs.
        """
        pipe = self._client.pipeline()
        for symbol in symbols:
            pipe.get(f"price:{symbol}")
        results = pipe.execute()

        return {
            symbol: json.loads(raw) if raw else None
            for symbol, raw in zip(symbols, results)
        }

    def get_price_history(self, symbol: str, count: int = 100) -> list[float]:
        """
        Get the last N close prices for a symbol from the ring buffer.
        Used by the risk engine for rolling volatility calculations.
        """
        raw = self._client.lrange(f"prices:history:{symbol}", -count, -1)
        return [float(v) for v in raw]

    # ── Portfolio Cache ────────────────────────────────────────

    def set_portfolio_value(self, portfolio_id: int, value_data: dict) -> None:
        """Cache the live portfolio value and P&L."""
        key = f"portfolio:{portfolio_id}:value"
        self._client.setex(key, 300, json.dumps(value_data))  # Expires in 5 min

    def get_portfolio_value(self, portfolio_id: int) -> Optional[dict]:
        """Get cached portfolio value."""
        raw = self._client.get(f"portfolio:{portfolio_id}:value")
        return json.loads(raw) if raw else None

    # ── Risk Metrics Cache ─────────────────────────────────────

    def set_risk_metrics(self, symbol: str, metrics: dict) -> None:
        """
        Cache computed risk metrics for a symbol.
        Risk engine writes here; API reads from here.
        Avoids recomputing VaR on every API request.
        """
        key = f"risk:{symbol}"
        self._client.setex(key, RISK_CACHE_TTL, json.dumps(metrics))

    def get_risk_metrics(self, symbol: str) -> Optional[dict]:
        """Get cached risk metrics for a symbol."""
        raw = self._client.get(f"risk:{symbol}")
        return json.loads(raw) if raw else None

    def get_all_risk_metrics(self, symbols: list[str]) -> dict[str, Optional[dict]]:
        """Fetch risk metrics for all symbols in one pipeline call."""
        pipe = self._client.pipeline()
        for symbol in symbols:
            pipe.get(f"risk:{symbol}")
        results = pipe.execute()
        return {
            symbol: json.loads(raw) if raw else None
            for symbol, raw in zip(symbols, results)
        }

    # ── Utility ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return Redis memory and key stats — useful for monitoring."""
        info = self._client.info("memory")
        return {
            "used_memory_human": info.get("used_memory_human"),
            "total_keys": self._client.dbsize(),
        }

    def close(self) -> None:
        self._client.close()
        logger.info("redis_closed")
