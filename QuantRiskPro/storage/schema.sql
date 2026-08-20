-- ============================================================
-- EquityPulse Database Schema
-- ============================================================
-- Run once to initialize the database.
-- TimescaleDB converts price_bars into a hypertable —
-- this is what makes time-range queries 10-100x faster
-- than vanilla PostgreSQL on time-series data.
-- ============================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ── Price Bars (time-series) ─────────────────────────────────
-- Stores every OHLCV bar received from Polygon.
-- Partitioned automatically by TimescaleDB into 1-week chunks.
CREATE TABLE IF NOT EXISTS price_bars (
    time        TIMESTAMPTZ     NOT NULL,
    symbol      VARCHAR(10)     NOT NULL,
    open        NUMERIC(12, 4)  NOT NULL,
    high        NUMERIC(12, 4)  NOT NULL,
    low         NUMERIC(12, 4)  NOT NULL,
    close       NUMERIC(12, 4)  NOT NULL,
    volume      BIGINT          NOT NULL,
    vwap        NUMERIC(12, 4),
    num_trades  INTEGER,
    interval    VARCHAR(10)     NOT NULL  -- 'second' or 'minute'
);

-- Convert to hypertable — this is the TimescaleDB magic
SELECT create_hypertable(
    'price_bars',
    'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- Composite index: symbol + time is the most common query pattern
CREATE INDEX IF NOT EXISTS idx_price_bars_symbol_time
    ON price_bars (symbol, time DESC);

-- ── Continuous Aggregate: 1-minute OHLCV ────────────────────
-- TimescaleDB automatically maintains this materialized view.
-- Querying 1-minute bars is instant — no aggregation at query time.
CREATE MATERIALIZED VIEW IF NOT EXISTS price_bars_1min
WITH (timescaledb.continuous) AS
    SELECT
        time_bucket('1 minute', time) AS bucket,
        symbol,
        first(open, time)             AS open,
        max(high)                     AS high,
        min(low)                      AS low,
        last(close, time)             AS close,
        sum(volume)                   AS volume,
        avg(vwap)                     AS vwap
    FROM price_bars
    WHERE interval = 'second'
    GROUP BY bucket, symbol
WITH NO DATA;

-- Refresh policy: keep 1-min aggregate up to date automatically
SELECT add_continuous_aggregate_policy(
    'price_bars_1min',
    start_offset => INTERVAL '1 hour',
    end_offset   => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- ── Portfolios ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portfolios (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    description     TEXT,
    cash_balance    NUMERIC(15, 2)  NOT NULL DEFAULT 100000.00,  -- Start with $100k
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── Positions ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS positions (
    id              SERIAL PRIMARY KEY,
    portfolio_id    INTEGER         NOT NULL REFERENCES portfolios(id),
    symbol          VARCHAR(10)     NOT NULL,
    quantity        NUMERIC(15, 6)  NOT NULL DEFAULT 0,
    avg_cost        NUMERIC(12, 4)  NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (portfolio_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_positions_portfolio
    ON positions (portfolio_id);

-- ── Transactions ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    id              SERIAL PRIMARY KEY,
    portfolio_id    INTEGER         NOT NULL REFERENCES portfolios(id),
    symbol          VARCHAR(10)     NOT NULL,
    side            VARCHAR(4)      NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity        NUMERIC(15, 6)  NOT NULL,
    price           NUMERIC(12, 4)  NOT NULL,
    total_value     NUMERIC(15, 2)  NOT NULL,
    executed_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_portfolio
    ON transactions (portfolio_id, executed_at DESC);

-- ── Seed data: default portfolio ─────────────────────────────
INSERT INTO portfolios (name, description, cash_balance)
VALUES ('Main Portfolio', 'EquityPulse default portfolio', 100000.00)
ON CONFLICT DO NOTHING;
