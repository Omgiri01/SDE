# QuantRiskPro

**A distributed real-time quantitative risk analytics and portfolio intelligence platform.**

Built by **Om Giri** to demonstrate institutional-grade backend systems engineering — live data pipelines, time-series storage, rigorous financial mathematics, and a reactive dashboard that updates tick-by-tick without a page refresh.

> *Every design decision mirrors what you'd find at a hedge fund, prime broker, or high-frequency trading desk.*

[![Author](https://img.shields.io/badge/Author-Om%20Giri-blue.svg)](https://github.com/Omgiri01)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](api/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](frontend/)
[![Kafka](https://img.shields.io/badge/Apache-Kafka-black.svg)](ingestion/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed.svg)](docker-compose.yml)

---

## What It Does

Connects to the Polygon.io WebSocket market feed, streams live NYSE / NASDAQ tick data through **Apache Kafka**, stores it in **TimescaleDB** (a purpose-built time-series database), runs an institutional risk engine on top, and serves everything through a **FastAPI** backend with a **React** dashboard that updates in real time.

- **Live Dashboard**: Prices for 10 tickers update via WebSocket.
- **Risk Metrics**: Value at Risk (VaR), Sharpe Ratio, Sortino Ratio, Volatility, and Max Drawdown refresh every 30 seconds.
- **Efficient Frontier**: Recomputed using 10,000 Monte Carlo simulations whenever the portfolio optimizer is invoked.

---

## Mathematical & Financial Core

### 1. Historical Simulation Value at Risk (VaR)

Computes tail risk without assuming a normal return distribution. Real market returns exhibit fat tails, skewness, and kurtosis. Historical simulation captures these empirically:

$$
\text{VaR}_\alpha = -\text{Quantile}_\alpha(r_1, r_2, \ldots, r_n)
$$

Where $r_i$ are realized daily log-returns and $\alpha$ is the confidence level (e.g., 95%, 99%).

### 2. Monte Carlo Portfolio Optimization (Markowitz MPT)

Simulates 10,000 random portfolio weight vectors, computing the expected return and volatility for each:

$$
\mu_p = \mathbf{w}^\top \boldsymbol{\mu}, \quad \sigma_p^2 = \mathbf{w}^\top \boldsymbol{\Sigma} \mathbf{w}
$$

The efficient frontier is traced by solving the constrained quadratic program (via SciPy SLSQP):

$$
\min_{\mathbf{w}} \; \mathbf{w}^\top \boldsymbol{\Sigma} \mathbf{w} \quad \text{subject to} \quad \mathbf{w}^\top \boldsymbol{\mu} = \mu^*, \; \sum_i w_i = 1, \; w_i \geq 0
$$

### 3. Sharpe & Sortino Ratios

$$
\text{Sharpe} = \frac{\mu_p - r_f}{\sigma_p}, \qquad \text{Sortino} = \frac{\mu_p - r_f}{\sigma_{\text{downside}}}
$$

Sortino penalizes only downside deviation, making it more appropriate for asymmetric return strategies.

### 4. Geometric Brownian Motion (GBM) Simulation

$$
dS_t = \mu S_t \, dt + \sigma S_t \, dW_t
$$

Used to simulate forward asset price paths for scenario analysis and stress testing.

---

## System Architecture

```
Polygon.io WebSocket
       │
       ▼
  ingestion/           ← connects to WS, publishes raw ticks to Kafka
       │
  Apache Kafka         ← raw.ticks + aggregated.ohlcv topics
       │
  storage/consumer     ← reads Kafka, writes to TimescaleDB + Redis
       │          │
 TimescaleDB    Redis  ← hypertable for history, hot cache for live prices
       │          │
  risk/engine          ← reads prices, computes VaR/Sharpe/Vol, writes to Redis
       │
  api/ (FastAPI)       ← REST endpoints + WebSocket broadcaster
       │
  frontend/ (React 18) ← live dashboard, charts, portfolio optimizer UI
       │
  nginx/               ← reverse proxy routing API and static assets
```

### Key Architecture Decisions

| Decision | Rationale |
|:---------|:----------|
| **Kafka over direct DB writes** | Decouples ingestion from storage. DB slowdowns don't block the producer. Adding a new consumer (e.g., alerts service) requires zero changes to the producer. |
| **TimescaleDB over plain PostgreSQL** | Hypertables partition time-series into weekly chunks automatically. Range queries on `price_bars` are 10–100x faster. Continuous aggregate `price_bars_1min` refreshes every minute — minute-bar queries are instant. |
| **Historical Simulation VaR** | Normal distribution underestimates tail risk by 20–40% in volatile regimes. Historical simulation makes zero assumptions about distribution shape and naturally captures skewness and kurtosis. |
| **SciPy SLSQP for MPT** | Analytical Markowitz only works unconstrained. Real portfolios have long-only constraints and position limits. SLSQP handles arbitrary linear inequality constraints — the same solver used in institutional PM systems. |
| **Redis hot cache** | Dashboard needs prices for 10 symbols simultaneously. TimescaleDB SELECT ≈ 5ms; Redis GET ≈ 0.1ms. For a live P&L dashboard updating on every tick, that 50x difference is visible to users. |

---

## Tech Stack

| Layer | Technology |
|:------|:-----------|
| **Frontend** | React 18, TypeScript, WebSockets, Chart.js |
| **API Backend** | FastAPI (Python 3.11), Pydantic v2 |
| **Stream Processing** | Apache Kafka (Confluent) |
| **Time-Series Database** | TimescaleDB (PostgreSQL extension) |
| **Cache** | Redis 7 |
| **Risk Engine** | Python, NumPy, SciPy, Pandas |
| **DevOps** | Docker Compose (prod + dev), Nginx reverse proxy |
| **CI/CD** | GitHub Actions |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Polygon.io API key (free tier works)

### 1. Clone & Configure

```bash
git clone https://github.com/Omgiri01/SDE.git
cd SDE/QuantRiskPro
cp .env.example .env
# Add your POLYGON_API_KEY to .env
```

### 2. Launch All Services

```bash
docker-compose up --build
```

This starts: Kafka, Zookeeper, TimescaleDB, Redis, ingestion service, consumer, risk engine, FastAPI, and React frontend.

### 3. Open Dashboard

```
http://localhost:3000   → React Live Dashboard
http://localhost:8000/docs  → FastAPI Interactive API Docs
```

---

## Project Structure

```
QuantRiskPro/
├── api/               # FastAPI backend — REST + WebSocket endpoints
├── ingestion/         # Polygon.io WebSocket → Kafka producer
├── storage/           # Kafka → TimescaleDB + Redis consumer
├── risk/              # Risk engine (VaR, Sharpe, MPT optimizer)
├── portfolio/         # Portfolio management and optimizer logic
├── frontend/          # React 18 + TypeScript dashboard
├── nginx/             # Reverse proxy configuration
├── docker-compose.yml # Full multi-service orchestration
└── .github/           # GitHub Actions CI/CD workflows
```

---

## License

MIT License — Created by **Om Giri**
GitHub: [@Omgiri01](https://github.com/Omgiri01)
