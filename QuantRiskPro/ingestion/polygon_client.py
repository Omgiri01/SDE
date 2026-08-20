import os
import json
import time
from datetime import datetime, timezone
from typing import Callable, Optional

import structlog
from websocket import WebSocketApp
from ingestion.kafka_producer import EquityProducer

logger = structlog.get_logger(__name__)
WS_URL = "wss://delayed.polygon.io/stocks"


class PolygonClient:
    def __init__(self, producer: EquityProducer, tickers: list[str]):
        self.api_key = os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not set. Add it to your .env file.")
        self.producer = producer
        self.tickers = [t.upper() for t in tickers]
        self.topic_ticks = os.getenv("KAFKA_TOPIC_RAW_TICKS", "raw.ticks")
        self.topic_agg = os.getenv("KAFKA_TOPIC_AGGREGATED", "aggregated.ohlcv")
        self._ws: Optional[WebSocketApp] = None
        self._authenticated = False
        self._running = False
        self._reconnect_delay = 1.0
        self._message_count = 0
        self._start_time: Optional[float] = None
        self._on_tick: Optional[Callable] = None

    def on_tick(self, callback: Callable) -> None:
        self._on_tick = callback

    def _on_open(self, ws) -> None:
        logger.info("polygon_ws_connected", url=WS_URL)

    def _on_message(self, ws, raw: str) -> None:
        try:
            events = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("polygon_invalid_json", raw=raw[:200])
            return

        for event in events:
            ev_type = event.get("ev")

            if ev_type == "connected":
                logger.info("polygon_connected", status=event.get("status"))
                self._authenticate(ws)

            elif ev_type == "auth_response":
                if event.get("status") == "auth_success":
                    self._authenticated = True
                    self._start_time = time.time()
                    logger.info("polygon_authenticated")
                    self._subscribe(ws)
                else:
                    logger.error("polygon_auth_failed", event=event)
                    ws.close()

            elif ev_type == "T":
                self._handle_trade(event)

            elif ev_type == "Q":
                self._handle_quote(event)

            elif ev_type == "A":
                self._handle_aggregate(event, interval="second")

            elif ev_type == "AM":
                self._handle_aggregate(event, interval="minute")

    def _on_error(self, ws, error) -> None:
        logger.error("polygon_ws_error", error=str(error))

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        self._authenticated = False
        logger.warning("polygon_ws_closed", code=close_status_code, message=close_msg)
        if self._running:
            self._schedule_reconnect()

    def _authenticate(self, ws) -> None:
        ws.send(json.dumps({"action": "auth", "params": self.api_key}))

    def _subscribe(self, ws) -> None:
        channels = [f"A.{t}" for t in self.tickers] + [f"AM.{t}" for t in self.tickers]
        ws.send(json.dumps({"action": "subscribe", "params": ",".join(channels)}))
        logger.info("polygon_subscribed", tickers=self.tickers, channels=len(channels))

    def _handle_trade(self, event: dict) -> None:
        tick = {
            "type": "trade",
            "symbol": event.get("sym"),
            "price": event.get("p"),
            "size": event.get("s"),
            "exchange": event.get("x"),
            "conditions": event.get("c", []),
            "timestamp_ms": event.get("t"),
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        self._publish_tick(tick)

    def _handle_quote(self, event: dict) -> None:
        tick = {
            "type": "quote",
            "symbol": event.get("sym"),
            "bid_price": event.get("bp"),
            "bid_size": event.get("bs"),
            "ask_price": event.get("ap"),
            "ask_size": event.get("as"),
            "spread": round((event.get("ap", 0) - event.get("bp", 0)), 4),
            "timestamp_ms": event.get("t"),
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        self._publish_tick(tick)

    def _handle_aggregate(self, event: dict, interval: str) -> None:
        bar = {
            "type": f"agg_{interval}",
            "symbol": event.get("sym"),
            "open": event.get("o"),
            "high": event.get("h"),
            "low": event.get("l"),
            "close": event.get("c"),
            "volume": event.get("v"),
            "vwap": event.get("vw"),
            "num_trades": event.get("z"),
            "start_ms": event.get("s"),
            "end_ms": event.get("e"),
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        self.producer.publish(topic=self.topic_agg, message=bar, key=bar["symbol"])
        self._message_count += 1
        if self._message_count % 100 == 0:
            elapsed = time.time() - (self._start_time or time.time())
            logger.info("throughput_update", messages=self._message_count,
                        mps=round(self._message_count / elapsed, 1) if elapsed > 0 else 0)
        if self._on_tick:
            self._on_tick(bar)

    def _publish_tick(self, tick: dict) -> None:
        self.producer.publish(topic=self.topic_ticks, message=tick, key=tick.get("symbol"))
        self._message_count += 1
        if self._on_tick:
            self._on_tick(tick)

    def _schedule_reconnect(self) -> None:
        delay = min(self._reconnect_delay, 30.0)
        logger.info("polygon_reconnecting", delay_seconds=delay)
        time.sleep(delay)
        self._reconnect_delay = min(self._reconnect_delay * 2, 30.0)
        self.start()

    def start(self) -> None:
        self._running = True
        self._ws = WebSocketApp(
            WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        logger.info("polygon_ws_starting", tickers=self.tickers)
        self._ws.run_forever(ping_interval=30, ping_timeout=10)

    def stop(self) -> None:
        self._running = False
        if self._ws:
            self._ws.close()
        logger.info("polygon_client_stopped", total_messages=self._message_count)