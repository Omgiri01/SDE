"""
routes/risk.py
--------------
Risk metrics endpoints. Reads from Redis cache (written by risk engine).
"""

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Depends

from api.models import RiskMetricsResponse, PortfolioRiskResponse, VaRModel, VolatilityModel, RatiosModel, DrawdownModel
from api.deps import get_redis, get_tickers

router = APIRouter(prefix="/api/risk", tags=["risk"])
logger = structlog.get_logger(__name__)


def _parse_risk_metrics(symbol: str, raw: dict) -> RiskMetricsResponse:
    """Convert raw Redis dict to typed Pydantic model."""
    var_data = raw.get("var")
    vol_data = raw.get("volatility")
    ratio_data = raw.get("ratios")
    dd_data = raw.get("drawdown")

    return RiskMetricsResponse(
        symbol=symbol,
        current_price=raw.get("current_price", 0.0),
        computed_at=raw.get("computed_at", ""),
        alerts=raw.get("alerts", []),
        var=VaRModel(**var_data) if var_data else None,
        volatility=VolatilityModel(**vol_data) if vol_data else None,
        ratios=RatiosModel(**ratio_data) if ratio_data else None,
        drawdown=DrawdownModel(**dd_data) if dd_data else None,
        data_source="redis_cache",
    )


@router.get("/{symbol}", response_model=RiskMetricsResponse)
async def get_symbol_risk(
    symbol: str,
    redis=Depends(get_redis),
):
    """
    Get computed risk metrics for a single symbol.

    Metrics are pre-computed by the risk engine every 30 seconds
    and cached in Redis. This endpoint just reads the cache — no
    computation happens at request time (sub-millisecond latency).

    Returns VaR, rolling volatility, Sharpe/Sortino, and max drawdown.
    Returns 404 if symbol hasn't been computed yet (risk engine not running).
    """
    symbol = symbol.upper()
    raw = redis.get_risk_metrics(symbol)

    if raw is None:
        raise HTTPException(
            status_code=404,
            detail=f"No risk metrics for {symbol}. "
                   f"Ensure the risk engine (python -m risk.engine) is running "
                   f"and the symbol has sufficient price history (30+ bars).",
        )

    logger.info("risk_served", symbol=symbol)
    return _parse_risk_metrics(symbol, raw)


@router.get("/portfolio/aggregate", response_model=PortfolioRiskResponse)
async def get_portfolio_risk(
    redis=Depends(get_redis),
    tickers: list[str] = Depends(get_tickers),
):
    """
    Aggregate risk view across all tracked symbols.

    Fetches risk metrics for all tickers in one Redis pipeline call,
    then collects all active alerts. This is the "portfolio risk dashboard"
    endpoint — one call gives the frontend everything it needs.
    """
    all_metrics = redis.get_all_risk_metrics(tickers)

    computed = {}
    missing = []
    all_alerts = []

    for symbol, raw in all_metrics.items():
        if raw is None:
            missing.append(symbol)
        else:
            computed[symbol] = _parse_risk_metrics(symbol, raw)
            all_alerts.extend(raw.get("alerts", []))

    return PortfolioRiskResponse(
        portfolio_id=1,
        symbols_computed=list(computed.keys()),
        symbols_missing_data=missing,
        active_alerts=all_alerts,
        metrics={s: m for s, m in computed.items()},
        computed_at=datetime.now(timezone.utc).isoformat(),
    )
