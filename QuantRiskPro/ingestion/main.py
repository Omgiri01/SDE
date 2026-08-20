# Author: Om Giri (github.com/Omgiri01)
# QuantRiskPro - Distributed Real-Time Risk Analytics Platform

"""
main.py
-------
Entry point for the QuantRiskPro ingestion service.

What this does:
  1. Loads environment config
  2. Starts a Kafka producer
  3. Connects to Polygon.io WebSocket
  4. Streams live tick data into Kafka topics
  5. Prints throughput metrics every 60 seconds
  6. Handles Ctrl+C gracefully

Usage:
  python -m ingestion.main
"""

import os
import sys
import signal
import threading
import time

import structlog
from dotenv import load_dotenv

load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = structlog.get_logger(__name__)

from ingestion.kafka_producer import EquityProducer
from ingestion.polygon_client import PolygonClient


def parse_tickers() -> list[str]:
    """Read ticker list from env. Defaults to a diversified set."""
    raw = os.getenv("WATCH_TICKERS", "AAPL,MSFT,GOOGL,AMZN,NVDA")
    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def print_metrics_loop(producer: EquityProducer, interval: int = 60) -> None:
    """Background thread: prints Kafka throughput stats every `interval` seconds."""
    while True:
        time.sleep(interval)
        metrics = producer.get_metrics()
        if metrics:
            logger.info("=== throughput metrics ===")
            for topic, stats in metrics.items():
                logger.info(
                    "topic_stats",
                    topic=topic,
                    messages=stats["total_messages"],
                    mps=stats["messages_per_second"],
                    errors=stats["errors"],
                )


def main():
    logger.info("quantriskpro_starting")

    tickers = parse_tickers()
    logger.info("watching_tickers", tickers=tickers, count=len(tickers))

    # Initialize Kafka producer
    try:
        producer = EquityProducer()
    except Exception as e:
        logger.error(
            "kafka_init_failed",
            error=str(e),
            hint="Is Docker running? Try: docker compose up -d",
        )
        sys.exit(1)

    # Initialize Polygon client
    try:
        client = PolygonClient(producer=producer, tickers=tickers)
    except ValueError as e:
        logger.error("polygon_init_failed", error=str(e))
        producer.close()
        sys.exit(1)

    # Graceful shutdown on Ctrl+C
    def shutdown(signum, frame):
        logger.info("shutdown_signal_received")
        client.stop()
        producer.flush()
        producer.close()
        logger.info("shutdown_complete")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start metrics reporter in background
    metrics_thread = threading.Thread(
        target=print_metrics_loop,
        args=(producer,),
        daemon=True,
    )
    metrics_thread.start()

    # Log a sample tick to console so you can see data flowing
    def log_sample(tick: dict) -> None:
        symbol = tick.get("symbol")
        tick_type = tick.get("type")
        if tick_type == "agg_second":
            logger.info(
                "tick",
                symbol=symbol,
                close=tick.get("close"),
                volume=tick.get("volume"),
                vwap=tick.get("vwap"),
            )

    client.on_tick(log_sample)

    # Start WebSocket (blocking — runs until shutdown)
    logger.info(
        "ingestion_live",
        kafka_broker=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        polygon_url="wss://delayed.polygon.io/stocks",
    )
    client.start()


if __name__ == "__main__":
    main()
