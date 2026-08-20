"""
models.py
---------
Pydantic response models for all API endpoints.

Every endpoint returns a typed model — this gives us:
  - Automatic OpenAPI/Swagger documentation at /docs
  - Request/response validation at the framework level
  - Type-safe JSON serialization
  - Self-documenting API for recruiter demos

Schema design follows the "envelope" pattern:
  All responses wrap data in a consistent structure so the frontend
  can handle errors uniformly without parsing different shapes.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ── Shared ─────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ── Price Models ────────────────────────────────────────────────────────────────

class LivePrice(BaseModel):
    symbol: str
    close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    vwap: Optional[float] = None
    timestamp: Optional[str] = None
    source: str = "redis"


class OHLCVBar(BaseModel):
    time: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None


class PriceHistoryResponse(BaseModel):
    symbol: str
    bars: list[OHLCVBar]
    count: int
    interval: str = "minute"


# ── Risk Models ─────────────────────────────────────────────────────────────────

class VaRModel(BaseModel):
    var_95: float = Field(description="95% confidence VaR as % of portfolio")
    var_99: float = Field(description="99% confidence VaR as % of portfolio")
    var_95_dollar: float = Field(description="95% VaR in dollars")
    var_99_dollar: float = Field(description="99% VaR in dollars")
    method: str
    lookback_days: int


class VolatilityModel(BaseModel):
    vol_20d: Optional[float] = Field(None, description="20-day annualized volatility (%)")
    vol_60d: Optional[float] = Field(None, description="60-day annualized volatility (%)")
    daily_vol: float
    latest_return: float


class RatiosModel(BaseModel):
    sharpe: Optional[float]
    sortino: Optional[float]
    annualized_return: float
    risk_free_rate: float


class DrawdownModel(BaseModel):
    current_drawdown: float
    max_drawdown: float
    peak_price: float
    trough_price: float


class RiskMetricsResponse(BaseModel):
    symbol: str
    current_price: float
    computed_at: str
    alerts: list[str]
    var: Optional[VaRModel] = None
    volatility: Optional[VolatilityModel] = None
    ratios: Optional[RatiosModel] = None
    drawdown: Optional[DrawdownModel] = None
    data_source: str = "redis_cache"


class PortfolioRiskResponse(BaseModel):
    portfolio_id: int
    symbols_computed: list[str]
    symbols_missing_data: list[str]
    active_alerts: list[str]
    metrics: dict[str, Optional[RiskMetricsResponse]]
    computed_at: str


# ── Portfolio Models ─────────────────────────────────────────────────────────────

class PositionModel(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    cost_basis: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    weight: Optional[float] = None


class PortfolioResponse(BaseModel):
    portfolio_id: int
    name: str
    cash_balance: float
    total_equity_value: float
    total_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    positions: list[PositionModel]
    as_of: str


class FrontierPoint(BaseModel):
    expected_return: float
    volatility: float
    sharpe: float


class FrontierResponse(BaseModel):
    symbols: list[str]
    frontier: list[FrontierPoint]
    min_variance: dict[str, Any]
    max_sharpe: dict[str, Any]
    n_simulations: int
    computed_at: str


class RebalanceOrder(BaseModel):
    symbol: str
    side: str
    quantity: float
    target_value: float
    current_value: float
    drift_pct: float


class RebalanceResponse(BaseModel):
    needs_rebalancing: bool
    drift_threshold_pct: float
    drifted_symbols: list[str]
    orders: list[RebalanceOrder]
    estimated_trades: int
    estimated_turnover_pct: float
    current_weights: dict[str, float]
    target_weights: dict[str, float]
    computed_at: str


# ── Health Models ────────────────────────────────────────────────────────────────

class ServiceStatus(BaseModel):
    status: str          # "ok" | "degraded" | "down"
    latency_ms: Optional[float] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str          # overall: "ok" | "degraded" | "down"
    version: str = "1.0.0"
    services: dict[str, ServiceStatus]
    tickers_watched: list[str]
    tickers_with_data: int
    uptime_seconds: float
    checked_at: str


# ── WebSocket Models ─────────────────────────────────────────────────────────────

class WSPriceUpdate(BaseModel):
    type: str = "price_update"
    symbol: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[float] = None
    timestamp: str


class WSRiskAlert(BaseModel):
    type: str = "risk_alert"
    symbol: str
    alert: str
    severity: str = "warning"
    timestamp: str


class WSMessage(BaseModel):
    type: str
    payload: dict[str, Any]
    timestamp: str
