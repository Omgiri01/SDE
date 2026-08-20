"""
consumer.py
-----------
Kafka consumer that bridges the ingestion layer to the storage layer.

Flow:
  Polygon WebSocket → Kafka topics → THIS FILE → TimescaleDB + Redis

This runs as a separate process from the producer so they scale independently.
In production you'd run multiple consumer instances for higher throughput.
"""

import os
import signal
import sys
import time
import threading

import orjson
import structlog
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
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

from storage.timescale_client import TimescaleClient
from storage.redis_client import RedisClient


class StorageConsumer:
    """
    Reads OHLCV bars from Kafka and persists them to:
      - TimescaleDB (durable time-series storage)
      - Redis (live price cache for dashboard + risk engine)
    """

    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic_agg = os.getenv("KAFKA_TOPIC_AGGREGATED", "aggregated.ohlcv")
        self.topic_ticks = os.getenv("KAFKA_TOPIC_RAW_TICKS", "raw.ticks")

        self._running = False
        self._consumer: KafkaConsumer | None = None
        self._timescale: TimescaleClient | None = None
        self._redis: RedisClient | None = None

        # Metrics
        self._processed = 0
        self._errors = 0
        self._start_time = time.time()

    def _connect(self) -> None:
        logger.info("storage_consumer_connecting")

        # TimescaleDB
        self._timescale = TimescaleClient()

        # Redis
        self._redis = RedisClient()

        # Kafka consumer — subscribe to both topics
        self._consumer = KafkaConsumer(
            self.topic_agg,
            self.topic_ticks,
            bootstrap_servers=self.bootstrap_servers,
            group_id="quantriskpro-storage",       # Consumer group for offset tracking
            auto_offset_reset="latest",            # Start from latest on first run
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            value_deserializer=lambda v: orjson.loads(v),
            max_poll_records=500,                  # Process up to 500 messages per poll
            session_timeout_ms=30000,
        )
        logger.info("storage_consumer_ready", topics=[self.topic_agg, self.topic_ticks])

    def _process_message(self, message) -> None:
        """Route a Kafka message to the right storage handler."""
        bar = message.value
        msg_type = bar.get("type", "")

        if msg_type in ("agg_second", "agg_minute"):
            # Write to TimescaleDB (batched)
            self._timescale.insert_bar(bar)
            # Update Redis live price cache
            if bar.get("symbol") and bar.get("close"):
                self._redis.set_live_price(bar["symbol"], bar)

        # Raw trades/quotes go to Redis only (too high-frequency for DB)
        elif msg_type in ("trade", "quote"):
            if bar.get("symbol"):
                self._redis.set_live_price(bar["symbol"], bar)

        self._processed += 1

        # Log progress every 500 messages
        if self._processed % 500 == 0:
            elapsed = time.time() - self._start_time
            logger.info(
                "consumer_progress",
                processed=self._processed,
                errors=self._errors,
                mps=round(self._processed / elapsed, 1),
            )

    def _flush_loop(self, interval: int = 10) -> None:
        """Background thread: flush TimescaleDB batch every N seconds."""
        while self._running:
            time.sleep(interval)
            if self._timescale:
                self._timescale.flush()

    def run(self) -> None:
        """Main consumer loop."""
        self._connect()
        self._running = True

        # Start background flush thread
        flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        flush_thread.start()

        logger.info("storage_consumer_started")

        try:
            for message in self._consumer:
                if not self._running:
                    break
                try:
                    self._process_message(message)
                except Exception as e:
                    self._errors += 1
                    logger.error("message_processing_error", error=str(e))
        except Exception as e:
            logger.error("consumer_loop_error", error=str(e))
        finally:
            self._shutdown()

    def _shutdown(self) -> None:
        self._running = False
        logger.info("storage_consumer_shutting_down")
        if self._timescale:
            self._timescale.close()  # Flushes remaining batch
        if self._redis:
            self._redis.close()
        if self._consumer:
            self._consumer.close()
        logger.info(
            "storage_consumer_stopped",
            total_processed=self._processed,
            total_errors=self._errors,
        )


def main():
    consumer = StorageConsumer()

    def shutdown(signum, frame):
        logger.info("shutdown_signal")
        consumer._running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    consumer.run()


if __name__ == "__main__":
    main()
