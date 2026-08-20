"""
engine.py
---------
The risk engine runs as a continuous background process.

Every N seconds it:
  1. Reads price history from Redis ring buffer (fast) or TimescaleDB (fallback)
  2. Computes full risk report for each symbol
  3. Writes results to Redis so the API can serve them instantly
  4. Logs any alerts

This separation of concerns is important:
  - Ingestion service: gets data in
  - Storage consumer: persists data
  - Risk engine: computes analytics
  - API (Phase 5): serves results

Each can scale independently.
"""

import os
import sys
import time
import signal
import dataclasses
from datetime import datetime, timezone

import orjson
import structlog
from dotenv import load_dotenv

load_dotenv()

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = structlog.get_logger(__name__)

from storage.redis_client import RedisClient
from storage.timescale_client import TimescaleClient
from risk.metrics import compute_full_risk_report, RiskReport


# How often to recompute risk metrics (seconds)
COMPUTE_INTERVAL = 30

# Minimum prices needed before computing (need returns)
MIN_PRICES = 30

# Default portfolio value for VaR dollar calculations
DEFAULT_PORTFOLIO_VALUE = 100_000.0


class RiskEngine:
    def __init__(self):
        self.tickers = [
            t.strip().upper()
            for t in os.getenv("WATCH_TICKERS", "AAPL,MSFT,GOOGL,AMZN,NVDA").split(",")
        ]
        self._redis = RedisClient()
        self._timescale = TimescaleClient()
        self._running = False
        self._cycles = 0
        self._total_alerts = 0

    def _get_prices(self, symbol: str) -> list[float]:
        """
        Get price history for a symbol.
        Strategy:
          1. Try Redis ring buffer first (fastest, last 500 prices)
          2. Fall back to TimescaleDB if Redis doesn't have enough data
        """
        # Try Redis first
        redis_prices = self._redis.get_price_history(symbol, count=200)
        if len(redis_prices) >= MIN_PRICES:
            return redis_prices

        # Fallback: query TimescaleDB for historical data
        from datetime import timedelta
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=90)

        bars = self._timescale.get_price_history(symbol, start=start, end=end)
        if bars:
            return [float(b["close"]) for b in bars if b.get("close")]

        return redis_prices  # Return whatever we have, even if sparse

    def _report_to_dict(self, report: RiskReport) -> dict:
        """Convert RiskReport dataclass to JSON-serializable dict."""
        return {
            "symbol": report.symbol,
            "current_price": report.current_price,
            "computed_at": report.computed_at,
            "alerts": report.alerts,
            "var": dataclasses.asdict(report.var) if report.var else None,
            "volatility": dataclasses.asdict(report.volatility) if report.volatility else None,
            "ratios": dataclasses.asdict(report.ratios) if report.ratios else None,
            "drawdown": dataclasses.asdict(report.drawdown) if report.drawdown else None,
        }

    def _compute_cycle(self) -> None:
        """Run one full computation cycle across all tickers."""
        self._cycles += 1
        cycle_start = time.time()
        computed = 0
        alerts_this_cycle = []

        for symbol in self.tickers:
            try:
                prices = self._get_prices(symbol)

                if len(prices) < MIN_PRICES:
                    logger.debug(
                        "insufficient_data",
                        symbol=symbol,
                        prices=len(prices),
                        needed=MIN_PRICES,
                    )
                    continue

                # Compute full risk report
                report = compute_full_risk_report(
                    symbol=symbol,
                    prices=prices,
                    portfolio_value=DEFAULT_PORTFOLIO_VALUE,
                )

                if report is None:
                    continue

                # Write to Redis cache
                self._redis.set_risk_metrics(symbol, self._report_to_dict(report))
                computed += 1

                # Log key metrics
                log_data = {"symbol": symbol, "price": report.current_price}
                if report.volatility and report.volatility.vol_20d:
                    log_data["vol_20d"] = f"{report.volatility.vol_20d:.1f}%"
                if report.var:
                    log_data["var_95"] = f"{report.var.var_95:.2f}%"
                if report.ratios and report.ratios.sharpe is not None:
                    log_data["sharpe"] = report.ratios.sharpe
                if report.drawdown:
                    log_data["drawdown"] = f"{report.drawdown.current_drawdown:.2f}%"

                logger.info("risk_computed", **log_data)

                # Collect alerts
                if report.alerts:
                    alerts_this_cycle.extend(report.alerts)
                    self._total_alerts += len(report.alerts)
                    for alert in report.alerts:
                        logger.warning("RISK_ALERT", alert=alert)

            except Exception as e:
                logger.error("compute_error", symbol=symbol, error=str(e))

        elapsed = time.time() - cycle_start
        logger.info(
            "cycle_complete",
            cycle=self._cycles,
            computed=computed,
            alerts=len(alerts_this_cycle),
            elapsed_ms=round(elapsed * 1000),
        )

    def run(self) -> None:
        """Main loop — compute risk metrics every COMPUTE_INTERVAL seconds."""
        self._running = True
        logger.info(
            "risk_engine_started",
            tickers=self.tickers,
            interval_seconds=COMPUTE_INTERVAL,
        )

        while self._running:
            try:
                self._compute_cycle()
            except Exception as e:
                logger.error("cycle_error", error=str(e))

            # Wait for next cycle
            time.sleep(COMPUTE_INTERVAL)

    def stop(self) -> None:
        self._running = False
        self._redis.close()
        self._timescale.close()
        logger.info(
            "risk_engine_stopped",
            total_cycles=self._cycles,
            total_alerts=self._total_alerts,
        )


def main():
    engine = RiskEngine()

    def shutdown(signum, frame):
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    engine.run()


if __name__ == "__main__":
    main()
