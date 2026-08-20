"""
kafka_producer.py
-----------------
Wraps kafka-python's KafkaProducer with:
  - Automatic serialization via orjson (faster than stdlib json)
  - Per-topic throughput metrics
  - Graceful shutdown
  - Reconnection on broker failure
"""

import os
import time
import threading
from typing import Optional
from collections import defaultdict

import orjson
import structlog
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

logger = structlog.get_logger(__name__)


class EquityProducer:
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self._producer: Optional[KafkaProducer] = None
        self._lock = threading.Lock()

        # Metrics - track messages and bytes per topic
        self._metrics = defaultdict(lambda: {"messages": 0, "bytes": 0, "errors": 0})
        self._start_time = time.time()

        self._connect()

    def _connect(self, retries: int = 5, delay: float = 2.0) -> None:
        """Connect to Kafka broker with retry logic."""
        for attempt in range(retries):
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: orjson.dumps(v),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    # Batching settings - balance latency vs throughput
                    batch_size=16384,           # 16KB batches
                    linger_ms=5,                # Wait up to 5ms to fill a batch
                    compression_type="lz4",     # Fast compression for network efficiency
                    # Reliability settings
                    acks="all",                 # Wait for all replicas to acknowledge
                    retries=3,
                    max_in_flight_requests_per_connection=5,
                )
                logger.info("kafka_connected", broker=self.bootstrap_servers)
                return
            except NoBrokersAvailable:
                if attempt < retries - 1:
                    logger.warning(
                        "kafka_connect_retry",
                        attempt=attempt + 1,
                        retries=retries,
                        delay=delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error("kafka_connect_failed", broker=self.bootstrap_servers)
                    raise

    def publish(
        self,
        topic: str,
        message: dict,
        key: Optional[str] = None,
        on_error=None,
    ) -> None:
        """
        Publish a single message to a Kafka topic.
        Uses the ticker symbol as the partition key so all ticks
        for one symbol land on the same partition (ordering guarantee).
        """
        with self._lock:
            if self._producer is None:
                self._connect()

        serialized = orjson.dumps(message)

        def on_send_success(record_metadata):
            self._metrics[topic]["messages"] += 1
            self._metrics[topic]["bytes"] += len(serialized)

        def on_send_error(exc):
            self._metrics[topic]["errors"] += 1
            logger.error("kafka_publish_error", topic=topic, error=str(exc))
            if on_error:
                on_error(exc)

        self._producer.send(
            topic,
            value=message,
            key=key,
        ).add_callback(on_send_success).add_errback(on_send_error)

    def flush(self) -> None:
        """Force all buffered messages to be sent immediately."""
        if self._producer:
            self._producer.flush()

    def get_metrics(self) -> dict:
        """Return throughput stats - useful for the Grafana dashboard later."""
        elapsed = time.time() - self._start_time
        summary = {}
        for topic, stats in self._metrics.items():
            msgs = stats["messages"]
            summary[topic] = {
                "total_messages": msgs,
                "total_bytes": stats["bytes"],
                "errors": stats["errors"],
                "messages_per_second": round(msgs / elapsed, 2) if elapsed > 0 else 0,
            }
        return summary

    def close(self) -> None:
        """Graceful shutdown - flush pending messages before closing."""
        if self._producer:
            logger.info("kafka_producer_shutting_down")
            self._producer.flush(timeout=10)
            self._producer.close()
            self._producer = None
            logger.info("kafka_producer_closed", metrics=self.get_metrics())
