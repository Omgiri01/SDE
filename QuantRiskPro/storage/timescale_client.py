"""
timescale_client.py
-------------------
Handles all reads and writes to TimescaleDB.

Key design decisions:
- Uses psycopg2 with a connection pool (not an ORM) for performance.
  ORMs add overhead that matters when inserting thousands of bars/minute.
- Batch inserts: accumulates bars and flushes in bulk every N records.
  Single-row inserts would bottleneck on network round-trips.
- Upsert pattern (ON CONFLICT DO NOTHING) so duplicate bars from
  reconnects don't cause errors.
"""

import os
import time
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras
from psycopg2 import pool
import structlog

logger = structlog.get_logger(__name__)

# How many bars to accumulate before flushing to DB
BATCH_SIZE = 50


class TimescaleClient:
    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or os.getenv(
            "TIMESCALE_DSN",
            "postgresql://quantriskpro:quantriskpro_secret@localhost:5432/quantriskpro"
        )
        # Connection pool: min 2, max 10 connections
        self._pool = psycopg2.pool.ThreadedConnectionPool(2, 10, self.dsn)
        self._batch: list[dict] = []
        self._total_inserted = 0
        logger.info("timescale_connected", dsn=self.dsn.split("@")[-1])  # Log host only, not password

    def _get_conn(self):
        return self._pool.getconn()

    def _put_conn(self, conn):
        self._pool.putconn(conn)

    def insert_bar(self, bar: dict) -> None:
        """
        Add a bar to the batch buffer.
        Flushes to DB automatically when batch is full.
        """
        record = {
            "time": datetime.fromtimestamp(
                bar["start_ms"] / 1000, tz=timezone.utc
            ) if bar.get("start_ms") else datetime.now(timezone.utc),
            "symbol": bar["symbol"],
            "open": bar.get("open"),
            "high": bar.get("high"),
            "low": bar.get("low"),
            "close": bar.get("close"),
            "volume": bar.get("volume", 0),
            "vwap": bar.get("vwap"),
            "num_trades": bar.get("num_trades"),
            "interval": "second" if bar.get("type") == "agg_second" else "minute",
        }

        # Skip bars with missing OHLC data
        if not all([record["open"], record["high"], record["low"], record["close"]]):
            return

        self._batch.append(record)

        if len(self._batch) >= BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        """Write all buffered bars to TimescaleDB in a single batch insert."""
        if not self._batch:
            return

        batch = self._batch.copy()
        self._batch.clear()

        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO price_bars
                        (time, symbol, open, high, low, close, volume, vwap, num_trades, interval)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                    """,
                    [
                        (
                            r["time"], r["symbol"], r["open"], r["high"],
                            r["low"], r["close"], r["volume"], r["vwap"],
                            r["num_trades"], r["interval"]
                        )
                        for r in batch
                    ],
                    page_size=100
                )
            conn.commit()
            self._total_inserted += len(batch)
            logger.debug("timescale_batch_written", count=len(batch), total=self._total_inserted)
        except Exception as e:
            conn.rollback()
            logger.error("timescale_insert_error", error=str(e), batch_size=len(batch))
        finally:
            self._put_conn(conn)

    # ── Query methods (used by risk engine + API) ──────────────

    def get_recent_bars(self, symbol: str, limit: int = 100) -> list[dict]:
        """Fetch the most recent N bars for a symbol."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT time, symbol, open, high, low, close, volume, vwap
                    FROM price_bars
                    WHERE symbol = %s AND interval = 'minute'
                    ORDER BY time DESC
                    LIMIT %s
                    """,
                    (symbol, limit)
                )
                rows = cur.fetchall()
                return [dict(r) for r in rows]
        finally:
            self._put_conn(conn)

    def get_price_history(
        self,
        symbol: str,
        start: datetime,
        end: Optional[datetime] = None,
        interval: str = "minute"
    ) -> list[dict]:
        """
        Fetch OHLCV history for a symbol between two timestamps.
        Used by the risk engine to calculate VaR and rolling volatility.
        """
        end = end or datetime.now(timezone.utc)
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT time, open, high, low, close, volume, vwap
                    FROM price_bars
                    WHERE symbol = %s
                      AND interval = %s
                      AND time BETWEEN %s AND %s
                    ORDER BY time ASC
                    """,
                    (symbol, interval, start, end)
                )
                return [dict(r) for r in cur.fetchall()]
        finally:
            self._put_conn(conn)

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the single most recent close price for a symbol."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT close FROM price_bars
                    WHERE symbol = %s
                    ORDER BY time DESC LIMIT 1
                    """,
                    (symbol,)
                )
                row = cur.fetchone()
                return float(row[0]) if row else None
        finally:
            self._put_conn(conn)

    def get_symbols_with_data(self) -> list[str]:
        """Return all symbols that have price data in the DB."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT symbol FROM price_bars ORDER BY symbol")
                return [row[0] for row in cur.fetchall()]
        finally:
            self._put_conn(conn)

    def close(self) -> None:
        self.flush()  # Write any remaining buffered bars
        self._pool.closeall()
        logger.info("timescale_closed", total_inserted=self._total_inserted)
