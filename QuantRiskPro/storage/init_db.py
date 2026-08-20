"""
init_db.py
----------
Run once to create all tables and hypertables in TimescaleDB.
Safe to re-run — uses IF NOT EXISTS throughout.

Usage:
    python -m storage.init_db
"""

import os
import sys
import psycopg2
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


def init_db():
    dsn = os.getenv(
        "TIMESCALE_DSN",
        "postgresql://quantriskpro:quantriskpro_secret@localhost:5432/quantriskpro"
    )

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    logger.info("db_init_starting", host=dsn.split("@")[-1])

    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True

        with open(schema_path, "r") as f:
            schema_sql = f.read()

        with conn.cursor() as cur:
            cur.execute(schema_sql)

        logger.info("db_init_complete")
        logger.info("tables_created", tables=["price_bars", "portfolios", "positions", "transactions"])
        logger.info("hypertable_created", table="price_bars", chunk_interval="1 week")
        logger.info("continuous_aggregate_created", view="price_bars_1min")

        conn.close()

    except psycopg2.OperationalError as e:
        logger.error(
            "db_connection_failed",
            error=str(e),
            hint="Is TimescaleDB running? Try: docker compose up -d timescaledb"
        )
        sys.exit(1)
    except Exception as e:
        logger.error("db_init_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    init_db()
