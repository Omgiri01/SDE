"""
routes/portfolio.py
-------------------
Portfolio endpoints: positions, P&L, frontier, and rebalancing.
"""

from datetime import datetime, timezone
from typing import Optional

import numpy as np
import structlog
from fastapi import APIRouter, HTTPException, Depends

from api.models import (
    PortfolioResponse,
    PositionModel,
    FrontierResponse,
    FrontierPoint,
    RebalanceResponse,
    RebalanceOrder,
)
from api.deps import get_redis, get_timescale, get_tickers
from portfolio.optimizer import PortfolioOptimizer
from portfolio.rebalancer import RebalancingEngine, Position

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])
logger = structlog.get_logger(__name__)

# Equal-weight target for a 10-symbol portfolio
DEFAULT_PORTFOLIO_ID = 1


def _equal_weight_targets(symbols: list[str]) -> dict[str, float]:
    """Default target: equal weight across all symbols."""
    w = round(100.0 / len(symbols), 4) if symbols else 0.0
    return {s: w for s in symbols}


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    redis=Depends(get_redis),
    timescale=Depends(get_timescale),
    tickers: list[str] = Depends(get_tickers),
):
    """
    Get current portfolio state: positions, weights, and P&L.

    Reads live prices from Redis, position data from TimescaleDB.
    Falls back to demo positions if no real positions exist.
    """
    # Read live prices for all tickers (one Redis pipeline call)
    live_prices = redis.get_all_live_prices(tickers)

    # Read positions from PostgreSQL
    positions_data = _load_positions(timescale, DEFAULT_PORTFOLIO_ID)
    cash = _load_cash(timescale, DEFAULT_PORTFOLIO_ID)

    if not positions_data:
        # Demo mode: show equal-weight hypothetical positions
        positions_data = _demo_positions(tickers, live_prices)

    # Enrich positions with live prices and compute P&L
    position_models = []
    total_equity = 0.0
    total_pnl = 0.0
    total_cost = 0.0

    for pos in positions_data:
        symbol = pos["symbol"]
        price_data = live_prices.get(symbol)
        current_price = price_data.get("close") if price_data else None

        market_value = None
        cost_basis = pos["quantity"] * pos["avg_cost"]
        unrealized_pnl = None
        unrealized_pnl_pct = None

        if current_price:
            market_value = pos["quantity"] * current_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
            total_equity += market_value
            total_pnl += unrealized_pnl
            total_cost += cost_basis

        position_models.append(PositionModel(
            symbol=symbol,
            quantity=pos["quantity"],
            avg_cost=pos["avg_cost"],
            current_price=current_price,
            market_value=market_value,
            cost_basis=round(cost_basis, 2),
            unrealized_pnl=round(unrealized_pnl, 2) if unrealized_pnl is not None else None,
            unrealized_pnl_pct=round(unrealized_pnl_pct, 4) if unrealized_pnl_pct is not None else None,
            weight=None,  # computed below
        ))

    total_value = total_equity + cash

    # Compute weights after we know total
    for pm in position_models:
        if pm.market_value and total_value > 0:
            pm.weight = round(pm.market_value / total_value * 100, 4)

    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

    return PortfolioResponse(
        portfolio_id=DEFAULT_PORTFOLIO_ID,
        name="Main Portfolio",
        cash_balance=round(cash, 2),
        total_equity_value=round(total_equity, 2),
        total_value=round(total_value, 2),
        total_unrealized_pnl=round(total_pnl, 2),
        total_unrealized_pnl_pct=round(total_pnl_pct, 4),
        positions=position_models,
        as_of=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/frontier", response_model=FrontierResponse)
async def get_efficient_frontier(
    redis=Depends(get_redis),
    timescale=Depends(get_timescale),
    tickers: list[str] = Depends(get_tickers),
):
    """
    Compute and return the efficient frontier for the tracked symbols.

    Uses the last 90 days of minute bars from TimescaleDB as input.
    Runs 10,000 Monte Carlo simulations + SLSQP optimization.

    This is the computation-heavy endpoint — takes ~2-3 seconds.
    In production you'd cache this result and recompute daily.
    """
    from datetime import timedelta

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=90)

    # Build price matrix: T rows × N columns
    prices_by_symbol: dict[str, list[float]] = {}
    valid_symbols = []

    for symbol in tickers:
        # Try Redis ring buffer first (faster)
        redis_prices = redis.get_price_history(symbol, count=500)
        if len(redis_prices) >= 30:
            prices_by_symbol[symbol] = redis_prices
            valid_symbols.append(symbol)
            continue

        # Fallback to TimescaleDB
        bars = timescale.get_price_history(symbol, start=start, end=end, interval="minute")
        closes = [float(b["close"]) for b in bars if b.get("close")]
        if len(closes) >= 30:
            prices_by_symbol[symbol] = closes
            valid_symbols.append(symbol)

    if len(valid_symbols) < 2:
        raise HTTPException(
            status_code=503,
            detail="Need price history for at least 2 symbols to compute frontier. "
                   "Ensure the ingestion pipeline has been running for at least 1 day.",
        )

    # Align series to same length (use minimum)
    min_len = min(len(prices_by_symbol[s]) for s in valid_symbols)
    prices_matrix = np.array([prices_by_symbol[s][-min_len:] for s in valid_symbols]).T

    logger.info("frontier_computing", symbols=valid_symbols, data_points=min_len)

    optimizer = PortfolioOptimizer(valid_symbols, prices_matrix)
    result = optimizer.optimize(n_simulations=10_000)

    frontier_points = [
        FrontierPoint(
            expected_return=p.expected_return,
            volatility=p.volatility,
            sharpe=p.sharpe,
        )
        for p in result.frontier
    ]

    return FrontierResponse(
        symbols=valid_symbols,
        frontier=frontier_points,
        min_variance={
            "weights": result.min_variance.weights_dict,
            "expected_return": result.min_variance.expected_return,
            "volatility": result.min_variance.volatility,
            "sharpe": result.min_variance.sharpe,
        },
        max_sharpe={
            "weights": result.max_sharpe.weights_dict,
            "expected_return": result.max_sharpe.expected_return,
            "volatility": result.max_sharpe.volatility,
            "sharpe": result.max_sharpe.sharpe,
        },
        n_simulations=len(frontier_points),
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/rebalance", response_model=RebalanceResponse)
async def trigger_rebalance(
    redis=Depends(get_redis),
    tickers: list[str] = Depends(get_tickers),
):
    """
    Analyze portfolio drift and generate rebalancing orders.

    Uses 5% drift threshold (standard institutional practice).
    Returns the full rebalancing plan — sells first, then buys.
    Does NOT execute trades (read-only analysis).
    """
    live_prices = redis.get_all_live_prices(tickers)

    # Build Position objects from live prices
    # In production this would read real positions from PostgreSQL.
    # For now we use equal-weight synthetic positions for demonstration.
    positions = _synthetic_positions(tickers, live_prices)
    target_weights = _equal_weight_targets(tickers)

    engine = RebalancingEngine(drift_threshold=5.0)
    result = engine.generate_orders(positions, target_weights, cash=0.0)

    orders = [
        RebalanceOrder(
            symbol=o.symbol,
            side=o.side,
            quantity=o.quantity,
            target_value=o.target_value,
            current_value=o.current_value,
            drift_pct=o.drift_pct,
        )
        for o in result.orders
    ]

    return RebalanceResponse(
        needs_rebalancing=result.needs_rebalancing,
        drift_threshold_pct=result.drift_threshold_pct,
        drifted_symbols=result.snapshot.drifted_symbols,
        orders=orders,
        estimated_trades=result.estimated_trades,
        estimated_turnover_pct=result.estimated_turnover_pct,
        current_weights=result.snapshot.weights,
        target_weights=result.snapshot.target_weights,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_positions(timescale, portfolio_id: int) -> list[dict]:
    """Load positions from PostgreSQL."""
    conn = timescale._get_conn()
    try:
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT symbol, quantity, avg_cost
                FROM positions
                WHERE portfolio_id = %s AND quantity > 0
                ORDER BY symbol
                """,
                (portfolio_id,),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        timescale._put_conn(conn)


def _load_cash(timescale, portfolio_id: int) -> float:
    """Load cash balance from PostgreSQL."""
    conn = timescale._get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cash_balance FROM portfolios WHERE id = %s",
                (portfolio_id,),
            )
            row = cur.fetchone()
            return float(row[0]) if row else 100_000.0
    finally:
        timescale._put_conn(conn)


def _demo_positions(tickers: list[str], live_prices: dict) -> list[dict]:
    """
    Generate synthetic equal-weight positions for demo mode.
    Used when no real positions exist in the database.
    """
    total_value = 100_000.0
    per_symbol = total_value / len(tickers) if tickers else 0

    positions = []
    for symbol in tickers:
        price_data = live_prices.get(symbol)
        price = price_data.get("close") if price_data else 150.0
        if not price:
            price = 150.0
        quantity = per_symbol / price
        positions.append({
            "symbol": symbol,
            "quantity": round(quantity, 4),
            "avg_cost": round(price * 0.95, 4),  # Simulated 5% gain
        })

    return positions


def _synthetic_positions(tickers: list[str], live_prices: dict) -> list[Position]:
    """
    Create Position objects for rebalancing analysis.
    In production this reads from the database; here we simulate drift
    by assigning slightly random quantities.
    """
    import random
    random.seed(42)
    total_value = 100_000.0
    n = len(tickers)

    positions = []
    for i, symbol in enumerate(tickers):
        price_data = live_prices.get(symbol)
        price = price_data.get("close") if price_data else 150.0
        if not price:
            price = 150.0

        # Simulate weight drift: some positions have run up, others haven't
        drift_factor = 1.0 + (random.random() - 0.5) * 0.3
        target_value = (total_value / n) * drift_factor
        quantity = target_value / price

        positions.append(Position(
            symbol=symbol,
            quantity=round(quantity, 4),
            avg_cost=round(price * 0.9, 4),
            current_price=price,
        ))

    return positions
