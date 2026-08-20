"""
demo_server.py
--------------
Author: Om Giri (github.com/Omgiri01)
QuantRiskPro - COMPLETE DEMO SERVER (WebDev + AI/ML + Distributed Systems)

Runs without Docker. Includes all 5 AI/ML endpoints:
  1. LSTM Price Forecasting (PyTorch)
  2. HMM Market Regime Detection
  3. Isolation Forest Anomaly Detection
  4. GARCH + XGBoost Volatility Forecasting
  5. FinBERT Sentiment Analysis

Run: python demo_server.py
Open: http://localhost:8000/docs  (interactive API)
      http://localhost:8000/dashboard  (live WebSocket dashboard)
"""

import asyncio
import math
import random
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# ── Simulated market data ─────────────────────────────────────────────────────

TICKERS = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "JPM", "NFLX", "AMD"]

BASE_PRICES = {
    "AAPL": 189.30, "TSLA": 248.50, "MSFT": 415.20, "NVDA": 875.60,
    "AMZN": 185.90, "GOOGL": 175.40, "META": 520.10, "JPM": 198.70,
    "NFLX": 680.30, "AMD": 156.80,
}

VOLATILITIES = {
    "AAPL": 0.018, "TSLA": 0.045, "MSFT": 0.016, "NVDA": 0.040,
    "AMZN": 0.022, "GOOGL": 0.020, "META": 0.030, "JPM": 0.015,
    "NFLX": 0.035, "AMD": 0.042,
}

price_state: Dict[str, dict] = {}


def init_prices():
    for ticker in TICKERS:
        price_state[ticker] = {
            "symbol": ticker,
            "price": BASE_PRICES[ticker],
            "prev_close": BASE_PRICES[ticker] * (1 + random.uniform(-0.02, 0.02)),
            "volume": random.randint(5_000_000, 50_000_000),
            "timestamp": time.time(),
        }


def tick_prices():
    for ticker in TICKERS:
        state = price_state[ticker]
        dt = 1 / (252 * 6.5 * 3600)
        mu = 0.08
        sigma = VOLATILITIES[ticker]
        dW = random.gauss(0, 1) * math.sqrt(dt)
        dS = (mu * dt + sigma * dW) * state["price"]
        state["price"] = round(max(state["price"] + dS, 1.0), 2)
        state["volume"] += random.randint(100, 5000)
        state["timestamp"] = time.time()


def get_price_payload():
    payload = []
    for ticker in TICKERS:
        s = price_state[ticker]
        prev = s["prev_close"]
        change_pct = ((s["price"] - prev) / prev) * 100
        payload.append({
            "symbol": ticker,
            "price": s["price"],
            "prev_close": round(prev, 2),
            "change_pct": round(change_pct, 4),
            "volume": s["volume"],
            "timestamp": s["timestamp"],
        })
    return payload


# ── Risk Engine ───────────────────────────────────────────────────────────────

def generate_mock_returns(n_days: int = 252) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    returns = {}
    for ticker in TICKERS:
        sigma = VOLATILITIES[ticker]
        mu = 0.08 / 252
        r = rng.normal(mu, sigma / math.sqrt(252), n_days)
        returns[ticker] = r
    return returns


MOCK_RETURNS = generate_mock_returns()


def compute_var(returns: np.ndarray, confidence: float = 0.95) -> float:
    return float(-np.quantile(returns, 1 - confidence))


def compute_sharpe(returns: np.ndarray, risk_free: float = 0.05 / 252) -> float:
    excess = returns - risk_free
    return float((excess.mean() / excess.std()) * math.sqrt(252)) if excess.std() else 0.0


def compute_sortino(returns: np.ndarray, risk_free: float = 0.05 / 252) -> float:
    downside = returns[returns < risk_free]
    return float(((returns.mean() - risk_free) / downside.std()) * math.sqrt(252)) if len(downside) and downside.std() else 0.0


def compute_max_drawdown(returns: np.ndarray) -> float:
    cum = np.cumprod(1 + returns)
    rolling_max = np.maximum.accumulate(cum)
    return float(((cum - rolling_max) / rolling_max).min())


def compute_volatility(returns: np.ndarray) -> float:
    return float(returns.std() * math.sqrt(252))


def monte_carlo_frontier(n_portfolios: int = 5000) -> dict:
    rng = np.random.default_rng(99)
    ret_matrix = np.array([MOCK_RETURNS[t] for t in TICKERS])
    mean_returns = ret_matrix.mean(axis=1)
    cov_matrix = np.cov(ret_matrix)
    results = []
    for _ in range(n_portfolios):
        w = rng.dirichlet(np.ones(len(TICKERS)))
        port_return = float(np.dot(w, mean_returns) * 252)
        port_vol = float(math.sqrt(w @ cov_matrix @ w) * math.sqrt(252))
        sharpe = (port_return - 0.05) / port_vol if port_vol > 0 else 0
        results.append({
            "return": round(port_return, 6),
            "volatility": round(port_vol, 6),
            "sharpe": round(sharpe, 4),
            "weights": {t: round(float(w[i]), 4) for i, t in enumerate(TICKERS)},
        })
    best = max(results, key=lambda x: x["sharpe"])
    min_vol = min(results, key=lambda x: x["volatility"])
    return {
        "frontier_points": results[::20],
        "max_sharpe_portfolio": best,
        "min_volatility_portfolio": min_vol,
        "n_simulations": n_portfolios,
    }


# ── WebSocket Manager ─────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: dict):
        import json
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(msg))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = ConnectionManager()


async def price_broadcaster():
    while True:
        await asyncio.sleep(2)
        tick_prices()
        payload = get_price_payload()
        await ws_manager.broadcast({"type": "price_update", "payload": payload})
        alerts = []
        for item in payload:
            if abs(item["change_pct"]) > 2.0:
                alerts.append({
                    "symbol": item["symbol"],
                    "alert": f"Large move: {item['change_pct']:+.2f}%",
                    "severity": "high" if abs(item["change_pct"]) > 3.5 else "medium",
                })
        if alerts:
            await ws_manager.broadcast({"type": "risk_alerts", "payload": alerts})


# ── App Factory ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_prices()
    task = asyncio.create_task(price_broadcaster())
    print("\n" + "="*65)
    print("  QuantRiskPro — COMPLETE DEMO SERVER (WebDev + AI/ML)")
    print("="*65)
    print("  Dashboard:      http://localhost:8000/dashboard")
    print("  API Docs:       http://localhost:8000/docs")
    print("  Live Prices:    http://localhost:8000/api/prices")
    print("  WebSocket:      ws://localhost:8000/ws/live")
    print("-"*65)
    print("  AI/ML Endpoints:")
    print("  Train Models:   POST http://localhost:8000/api/ml/train")
    print("  ML Status:      GET  http://localhost:8000/api/ml/status")
    print("  LSTM Forecast:  GET  http://localhost:8000/api/ml/forecast/NVDA")
    print("  Regime:         GET  http://localhost:8000/api/ml/regime/AAPL")
    print("  Anomaly:        GET  http://localhost:8000/api/ml/anomaly/TSLA")
    print("  Volatility:     GET  http://localhost:8000/api/ml/volatility/MSFT")
    print("  Sentiment:      GET  http://localhost:8000/api/ml/sentiment/NVDA")
    print("="*65 + "\n")
    yield
    task.cancel()


app = FastAPI(
    title="QuantRiskPro API",
    description=(
        "**Distributed Real-Time Quantitative Risk Analytics & AI Platform**\n\n"
        "Built by **Om Giri** (github.com/Omgiri01)\n\n"
        "## Tech Stack\n"
        "- **WebDev**: FastAPI, React 18, TypeScript, WebSockets, Nginx\n"
        "- **AI/ML**: PyTorch LSTM, HMM, Isolation Forest, GARCH+XGBoost, FinBERT\n"
        "- **Distributed Systems**: Apache Kafka, TimescaleDB, Redis\n"
        "- **Math**: VaR, Sharpe, Sortino, Monte Carlo MPT, GBM, SLSQP\n"
        "- **DevOps**: Docker Compose, GitHub Actions CI/CD\n\n"
        "## AI/ML Models\n"
        "1. **LSTM** — 2-layer stacked LSTM for 5-day price forecasting (PyTorch)\n"
        "2. **HMM** — Gaussian Hidden Markov Model for Bull/Bear/Sideways regime detection\n"
        "3. **Isolation Forest** — Real-time anomaly detection for flash crashes\n"
        "4. **GARCH+XGBoost** — Ensemble volatility forecasting\n"
        "5. **FinBERT** — Financial news sentiment analysis (NLP)"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount AI/ML Routes ────────────────────────────────────────────────────────
try:
    from ml.ml_routes import router as ml_router
    app.include_router(ml_router)
    print("[OK] AI/ML routes mounted at /api/ml/*")
except Exception as e:
    print(f"[WARN] ML routes skipped: {e}")


# ── REST Endpoints ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "QuantRiskPro API",
        "author": "Om Giri (github.com/Omgiri01)",
        "version": "2.0.0",
        "tech_stack": {
            "web": ["FastAPI", "React 18", "TypeScript", "WebSockets", "Nginx"],
            "ai_ml": ["PyTorch LSTM", "Gaussian HMM", "Isolation Forest", "GARCH+XGBoost", "FinBERT"],
            "distributed": ["Apache Kafka", "TimescaleDB", "Redis"],
            "devops": ["Docker Compose", "GitHub Actions"],
        },
        "endpoints": {
            "dashboard": "GET /dashboard",
            "docs": "GET /docs",
            "live_prices": "GET /api/prices",
            "risk": "GET /api/risk/{symbol}",
            "portfolio_frontier": "GET /api/portfolio/frontier",
            "ml_train": "POST /api/ml/train",
            "ml_lstm_forecast": "GET /api/ml/forecast/{symbol}",
            "ml_regime": "GET /api/ml/regime/{symbol}",
            "ml_anomaly": "GET /api/ml/anomaly/{symbol}",
            "ml_volatility": "GET /api/ml/volatility/{symbol}",
            "ml_sentiment": "GET /api/ml/sentiment/{symbol}",
            "websocket": "ws://localhost:8000/ws/live",
        },
        "tickers": TICKERS,
    }


@app.get("/api/prices", tags=["Market Data"])
async def get_all_prices():
    """Live prices for all 10 tickers (GBM simulation in demo mode)."""
    return get_price_payload()


@app.get("/api/prices/{symbol}", tags=["Market Data"])
async def get_price(symbol: str):
    sym = symbol.upper()
    if sym not in price_state:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Ticker {sym} not tracked")
    s = price_state[sym]
    prev = s["prev_close"]
    change_pct = ((s["price"] - prev) / prev) * 100
    return {"symbol": sym, "price": s["price"], "prev_close": round(prev, 2),
            "change_pct": round(change_pct, 4), "volume": s["volume"], "timestamp": s["timestamp"]}


@app.get("/api/risk/{symbol}", tags=["Risk Engine"])
async def get_risk(symbol: str, confidence: float = 0.95):
    """VaR, Sharpe, Sortino, Max Drawdown, Volatility — from-scratch math."""
    sym = symbol.upper()
    if sym not in MOCK_RETURNS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"{sym} not found")
    r = MOCK_RETURNS[sym]
    return {
        "symbol": sym, "confidence_level": confidence,
        "value_at_risk_1d": round(compute_var(r, confidence), 6),
        "annualized_sharpe": round(compute_sharpe(r), 4),
        "annualized_sortino": round(compute_sortino(r), 4),
        "max_drawdown": round(compute_max_drawdown(r), 6),
        "annualized_volatility": round(compute_volatility(r), 6),
    }


@app.get("/api/risk/portfolio/aggregate", tags=["Risk Engine"])
async def get_portfolio_risk():
    equal_w = np.array([1 / len(TICKERS)] * len(TICKERS))
    ret_matrix = np.array([MOCK_RETURNS[t] for t in TICKERS])
    port_returns = equal_w @ ret_matrix
    return {
        "portfolio": "Equal Weight", "n_assets": len(TICKERS), "tickers": TICKERS,
        "weights": {t: round(float(equal_w[i]), 4) for i, t in enumerate(TICKERS)},
        "value_at_risk_1d_95": round(compute_var(port_returns, 0.95), 6),
        "annualized_sharpe": round(compute_sharpe(port_returns), 4),
        "annualized_sortino": round(compute_sortino(port_returns), 4),
        "max_drawdown": round(compute_max_drawdown(port_returns), 6),
        "annualized_volatility": round(compute_volatility(port_returns), 6),
    }


@app.get("/api/portfolio/frontier", tags=["Portfolio"])
async def get_frontier(n: int = 3000):
    return monte_carlo_frontier(min(n, 10_000))


@app.get("/api/health", tags=["Health"])
async def health():
    return {
        "status": "healthy", "version": "2.0.0",
        "services": {
            "api": "up", "websocket": "up", "risk_engine": "up",
            "ml_module": "up", "redis": "simulated", "kafka": "simulated", "timescaledb": "simulated",
        },
        "active_ws_connections": len(ws_manager.active),
    }


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        await ws_manager.broadcast({"type": "connected",
                                    "payload": {"message": "Connected to QuantRiskPro", "tickers": TICKERS}})
        while True:
            data = await ws.receive_text()
            if data == "ping":
                import json
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)


# ── Embedded Live Dashboard ───────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>QuantRiskPro — Live AI Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0e1a; color: #e2e8f0; }
    header { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); border-bottom: 1px solid #1e40af33; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
    .logo { font-size: 22px; font-weight: 700; color: #60a5fa; }
    .logo span { color: #38bdf8; }
    .badge { background: #1d4ed8; color: #bfdbfe; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 999px; margin-left: 8px; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; animation: pulse 2s infinite; display: inline-block; }
    @keyframes pulse { 0%,100%{opacity:1}50%{opacity:.4} }
    .container { max-width: 1400px; margin: 0 auto; padding: 24px 32px; }
    .section-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: #475569; margin-bottom: 12px; }
    .links { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }
    .link-btn { background: #1e293b; border: 1px solid #334155; color: #60a5fa; padding: 7px 14px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 500; transition: background .2s; }
    .link-btn:hover { background: #334155; }
    .link-btn.ml { border-color: #7c3aed; color: #c4b5fd; }
    .price-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; margin-bottom: 28px; }
    .price-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 14px; transition: border-color .3s, transform .15s; }
    .price-card:hover { transform: translateY(-2px); border-color: #3b82f6; }
    .price-card.up { border-left: 3px solid #22c55e; }
    .price-card.down { border-left: 3px solid #ef4444; }
    .ticker { font-size: 12px; font-weight: 700; color: #94a3b8; letter-spacing: 1px; }
    .price { font-size: 22px; font-weight: 700; color: #f1f5f9; margin: 4px 0; }
    .change.pos { color: #22c55e; font-size: 12px; font-weight: 600; }
    .change.neg { color: #ef4444; font-size: 12px; font-weight: 600; }
    .flash { animation: flash-anim .5s ease; }
    @keyframes flash-anim { 0%{background:#1e3a5f}100%{background:#0f172a} }
    .panels { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 24px; }
    .panel { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 18px; }
    .panel h3 { font-size: 13px; font-weight: 700; color: #60a5fa; margin-bottom: 14px; }
    .panel.ml { border-color: #4c1d95; }
    .panel.ml h3 { color: #c4b5fd; }
    .metric-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #1e293b22; }
    .metric-label { font-size: 12px; color: #64748b; }
    .metric-value { font-size: 12px; font-weight: 600; color: #f1f5f9; font-family: monospace; }
    .ws-log { background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 11px; color: #22d3ee; height: 120px; overflow-y: auto; }
    .ml-status { background: #0f172a; border: 1px solid #4c1d95; border-radius: 8px; padding: 12px; font-size: 12px; margin-bottom: 16px; }
    .train-btn { background: #7c3aed; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; transition: background .2s; }
    .train-btn:hover { background: #6d28d9; }
    .train-btn:disabled { background: #374151; cursor: not-allowed; }
    footer { text-align: center; padding: 20px; color: #334155; font-size: 12px; border-top: 1px solid #1e293b; margin-top: 16px; }
  </style>
</head>
<body>
<header>
  <div>
    <span class="logo">Quant<span>Risk</span>Pro</span>
    <span class="badge">WebDev + AI/ML + Distributed</span>
    <div style="font-size:12px;color:#64748b;margin-top:4px">Built by Om Giri · github.com/Omgiri01</div>
  </div>
  <div style="display:flex;align-items:center;gap:8px;font-size:13px">
    <span class="dot"></span>
    <span id="ws-status">Connecting...</span>
  </div>
</header>

<div class="container">
  <div class="links">
    <a class="link-btn" href="/docs" target="_blank">📄 API Docs (Swagger)</a>
    <a class="link-btn" href="/api/prices" target="_blank">📈 Live Prices JSON</a>
    <a class="link-btn" href="/api/risk/NVDA" target="_blank">⚠️ NVDA Risk Metrics</a>
    <a class="link-btn" href="/api/portfolio/frontier?n=2000" target="_blank">🎯 Monte Carlo Frontier</a>
    <a class="link-btn ml" href="/api/ml/status" target="_blank">🤖 ML Status</a>
    <a class="link-btn ml" href="/api/ml/sentiment/NVDA" target="_blank">💬 NVDA Sentiment</a>
  </div>

  <!-- ML Training Panel -->
  <div class="ml-status">
    <div style="display:flex;align-items:center;justify-content:space-between">
      <div>
        <strong style="color:#c4b5fd">🧠 AI/ML Models</strong>
        <span style="color:#64748b;font-size:11px;margin-left:8px">LSTM · HMM · Isolation Forest · GARCH+XGBoost · FinBERT</span>
      </div>
      <button class="train-btn" id="train-btn" onclick="trainModels()">⚡ Train All Models</button>
    </div>
    <div id="ml-result" style="margin-top:8px;color:#94a3b8;font-size:11px">Click "Train All Models" to train LSTM, HMM, Isolation Forest, GARCH+XGBoost, and FinBERT sentiment on AAPL, TSLA, MSFT, NVDA...</div>
  </div>

  <p class="section-title">Live Market Prices — Streaming via WebSocket (GBM Simulation)</p>
  <div class="price-grid" id="price-grid"></div>

  <div class="panels">
    <div class="panel">
      <h3>📊 Portfolio Risk (Equal Weight)</h3>
      <div id="risk-panel"><div style="color:#475569;font-size:12px">Loading...</div></div>
    </div>
    <div class="panel ml">
      <h3>🤖 AI/ML Predictions</h3>
      <div id="ml-panel"><div style="color:#6b21a8;font-size:12px">Train models first →</div></div>
    </div>
    <div class="panel">
      <h3>🔌 WebSocket Log</h3>
      <div class="ws-log" id="ws-log"></div>
    </div>
  </div>
</div>

<footer>QuantRiskPro v2.0 · WebDev + AI/ML + Distributed Systems · Om Giri · github.com/Omgiri01</footer>

<script>
const tickers = ["AAPL","TSLA","MSFT","NVDA","AMZN","GOOGL","META","JPM","NFLX","AMD"];
const grid = document.getElementById('price-grid');
const wsLog = document.getElementById('ws-log');

tickers.forEach(t => {
  const card = document.createElement('div');
  card.className = 'price-card';
  card.id = 'card-' + t;
  card.innerHTML = `<div class="ticker">${t}</div><div class="price" id="p-${t}">---.--</div><div class="change" id="c-${t}">--</div>`;
  grid.appendChild(card);
});

fetch('/api/risk/portfolio/aggregate').then(r=>r.json()).then(d => {
  document.getElementById('risk-panel').innerHTML = [
    ['VaR 95% (1d)', (d.value_at_risk_1d_95*100).toFixed(3)+'%'],
    ['Sharpe (Ann.)', d.annualized_sharpe.toFixed(3)],
    ['Sortino (Ann.)', d.annualized_sortino.toFixed(3)],
    ['Max Drawdown', (d.max_drawdown*100).toFixed(2)+'%'],
    ['Volatility', (d.annualized_volatility*100).toFixed(2)+'%'],
  ].map(([l,v])=>`<div class="metric-row"><span class="metric-label">${l}</span><span class="metric-value">${v}</span></div>`).join('');
});

function logWs(msg) {
  const l = document.createElement('div');
  l.textContent = '['+new Date().toLocaleTimeString()+'] '+msg;
  wsLog.appendChild(l);
  wsLog.scrollTop = wsLog.scrollHeight;
  if (wsLog.children.length > 40) wsLog.removeChild(wsLog.firstChild);
}

function updateCard(item) {
  const card = document.getElementById('card-'+item.symbol);
  if (!card) return;
  document.getElementById('p-'+item.symbol).textContent = '$'+item.price.toFixed(2);
  const el = document.getElementById('c-'+item.symbol);
  const sign = item.change_pct >= 0 ? '+' : '';
  el.textContent = sign+item.change_pct.toFixed(2)+'%';
  el.className = 'change '+(item.change_pct >= 0 ? 'pos' : 'neg');
  card.className = 'price-card flash '+(item.change_pct >= 0 ? 'up' : 'down');
  setTimeout(() => card.classList.remove('flash'), 500);
}

async function trainModels() {
  const btn = document.getElementById('train-btn');
  const res = document.getElementById('ml-result');
  btn.disabled = true;
  btn.textContent = '⏳ Training...';
  res.textContent = 'Training LSTM, HMM, Isolation Forest, GARCH+XGBoost for AAPL, TSLA, MSFT, NVDA...';
  try {
    const resp = await fetch('/api/ml/train', {method: 'POST'});
    const data = await resp.json();
    btn.textContent = '✅ Models Trained';
    res.innerHTML = '<span style="color:#22c55e">All 5 AI/ML models trained!</span> Tickers: '+data.tickers_trained.join(', ')+'. Now loading predictions...';
    loadMLPredictions();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = '⚡ Train All Models';
    res.textContent = 'Error: '+e.message;
  }
}

async function loadMLPredictions() {
  const panel = document.getElementById('ml-panel');
  try {
    const [forecast, regime, vol, sentiment] = await Promise.all([
      fetch('/api/ml/forecast/NVDA').then(r=>r.json()),
      fetch('/api/ml/regime/AAPL').then(r=>r.json()),
      fetch('/api/ml/volatility/MSFT').then(r=>r.json()),
      fetch('/api/ml/sentiment/NVDA').then(r=>r.json()),
    ]);
    panel.innerHTML = [
      ['LSTM (NVDA 5d)', forecast.forecast_returns_pct ? forecast.forecast_returns_pct.map(r=>(r>0?'+':'')+r.toFixed(2)+'%').join(', ') : '–'],
      ['HMM Regime (AAPL)', regime.current_regime || '–'],
      ['Volatility (MSFT)', vol.ensemble_1d_vol_pct+'% — '+vol.vol_regime],
      ['Sentiment (NVDA)', sentiment.aggregate_signal+' (score: '+(sentiment.sentiment_score>0?'+':'')+sentiment.sentiment_score+')'],
    ].map(([l,v])=>`<div class="metric-row"><span class="metric-label">${l}</span><span class="metric-value">${v}</span></div>`).join('');
  } catch(e) {
    panel.innerHTML = '<div style="color:#ef4444;font-size:12px">Error loading ML: '+e+'</div>';
  }
}

function connect() {
  const ws = new WebSocket('ws://localhost:8000/ws/live');
  ws.onopen = () => { document.getElementById('ws-status').textContent = 'Live ✅'; logWs('WebSocket connected'); };
  ws.onmessage = e => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'price_update') { msg.payload.forEach(updateCard); logWs('price_update ×'+msg.payload.length); }
    if (msg.type === 'risk_alerts') { logWs('ALERT: '+msg.payload.map(a=>a.symbol+' '+a.alert).join(', ')); }
  };
  ws.onclose = () => { document.getElementById('ws-status').textContent = 'Reconnecting...'; setTimeout(connect, 3000); };
}
connect();
</script>
</body>
</html>"""


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
