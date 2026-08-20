"""
rebalancer.py
-------------
Drift-based portfolio rebalancing engine.

When a position's actual weight drifts more than DRIFT_THRESHOLD from its
target, the engine generates BUY/SELL orders to restore the target weights.

WHY drift-based rebalancing:
- Time-based (monthly) rebalancing ignores whether drift has actually occurred.
- Drift-based only trades when needed — lower costs, less turnover.
- Threshold of 5% is common in institutional practice (Vanguard uses ~5%).
- Sells are executed first so cash is available for buys (critical for margin accounts).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    """A single portfolio holding."""
    symbol: str
    quantity: float       # Number of shares
    avg_cost: float       # Average purchase price per share
    current_price: float  # Latest market price


@dataclass
class RebalanceOrder:
    """A single rebalancing trade instruction."""
    symbol: str
    side: str              # 'BUY' or 'SELL'
    quantity: float        # Number of shares to trade
    target_value: float    # Dollar value we're targeting
    current_value: float   # Current dollar value of position
    drift_pct: float       # How far off target weight this position was


@dataclass
class PortfolioSnapshot:
    """Current state of the portfolio."""
    positions: list[Position]
    cash: float
    total_value: float
    weights: dict[str, float]           # symbol → actual weight
    target_weights: dict[str, float]    # symbol → target weight
    drifted_symbols: list[str]          # symbols that exceed drift threshold


@dataclass
class RebalanceResult:
    """Output of a rebalancing analysis."""
    needs_rebalancing: bool
    snapshot: PortfolioSnapshot
    orders: list[RebalanceOrder]        # Sells first, then buys
    estimated_trades: int
    estimated_turnover_pct: float       # % of portfolio that would trade
    drift_threshold_pct: float


@dataclass
class PerformanceAttribution:
    """P&L breakdown by position."""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight: float


class RebalancingEngine:
    """
    Computes drift and generates rebalancing orders for a portfolio.

    Args:
        drift_threshold: Minimum weight drift (%) to trigger rebalancing.
                         Default 5% — standard institutional threshold.
    """

    def __init__(self, drift_threshold: float = 5.0):
        self.drift_threshold = drift_threshold

    def snapshot(
        self,
        positions: list[Position],
        target_weights: dict[str, float],
        cash: float = 0.0,
    ) -> PortfolioSnapshot:
        """
        Compute current portfolio state and identify drifted positions.

        Args:
            positions:      Current holdings with live prices
            target_weights: Desired allocation by symbol (must sum to ~1.0)
            cash:           Uninvested cash balance
        """
        equity_value = sum(p.quantity * p.current_price for p in positions)
        total_value = equity_value + cash

        if total_value <= 0:
            return PortfolioSnapshot(
                positions=positions,
                cash=cash,
                total_value=0.0,
                weights={},
                target_weights=target_weights,
                drifted_symbols=[],
            )

        actual_weights = {
            p.symbol: (p.quantity * p.current_price / total_value) * 100
            for p in positions
        }

        drifted = [
            symbol
            for symbol, actual_w in actual_weights.items()
            if symbol in target_weights
            and abs(actual_w - target_weights[symbol]) > self.drift_threshold
        ]

        return PortfolioSnapshot(
            positions=positions,
            cash=cash,
            total_value=total_value,
            weights=actual_weights,
            target_weights=target_weights,
            drifted_symbols=drifted,
        )

    def generate_orders(
        self,
        positions: list[Position],
        target_weights: dict[str, float],
        cash: float = 0.0,
    ) -> RebalanceResult:
        """
        Generate the full rebalancing plan.

        Returns RebalanceResult with:
        - needs_rebalancing: True if any position exceeds drift_threshold
        - orders: List of trades sorted sells-first (so cash is available for buys)
        - turnover estimate: % of portfolio being traded
        """
        snap = self.snapshot(positions, target_weights, cash)
        needs_rebalancing = len(snap.drifted_symbols) > 0

        if not needs_rebalancing:
            return RebalanceResult(
                needs_rebalancing=False,
                snapshot=snap,
                orders=[],
                estimated_trades=0,
                estimated_turnover_pct=0.0,
                drift_threshold_pct=self.drift_threshold,
            )

        orders = []
        total_trade_value = 0.0

        for p in positions:
            if p.symbol not in target_weights:
                continue

            target_w = target_weights[p.symbol] / 100.0
            target_value = snap.total_value * target_w
            current_value = p.quantity * p.current_price
            drift = snap.weights.get(p.symbol, 0.0) - target_weights[p.symbol]

            if abs(drift) <= self.drift_threshold:
                continue

            delta_value = target_value - current_value
            quantity = abs(delta_value) / p.current_price if p.current_price > 0 else 0.0

            if quantity < 0.001:
                continue

            orders.append(RebalanceOrder(
                symbol=p.symbol,
                side="BUY" if delta_value > 0 else "SELL",
                quantity=round(quantity, 4),
                target_value=round(target_value, 2),
                current_value=round(current_value, 2),
                drift_pct=round(drift, 4),
            ))
            total_trade_value += abs(delta_value)

        # Sells first — release cash before buying
        orders.sort(key=lambda o: (0 if o.side == "SELL" else 1, o.symbol))

        turnover = (total_trade_value / snap.total_value * 100) if snap.total_value > 0 else 0.0

        return RebalanceResult(
            needs_rebalancing=True,
            snapshot=snap,
            orders=orders,
            estimated_trades=len(orders),
            estimated_turnover_pct=round(turnover, 2),
            drift_threshold_pct=self.drift_threshold,
        )

    def performance_attribution(
        self,
        positions: list[Position],
        total_value: float,
    ) -> list[PerformanceAttribution]:
        """
        Break down P&L by position.

        Shows: market value, cost basis, unrealized P&L, weight.
        This is the "Portfolio Panel" data for the dashboard.
        """
        attributions = []
        for p in positions:
            market_value = p.quantity * p.current_price
            cost_basis = p.quantity * p.avg_cost
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0
            weight = (market_value / total_value * 100) if total_value > 0 else 0.0

            attributions.append(PerformanceAttribution(
                symbol=p.symbol,
                quantity=p.quantity,
                avg_cost=p.avg_cost,
                current_price=p.current_price,
                market_value=round(market_value, 2),
                cost_basis=round(cost_basis, 2),
                unrealized_pnl=round(pnl, 2),
                unrealized_pnl_pct=round(pnl_pct, 4),
                weight=round(weight, 4),
            ))

        # Sort by market value descending
        attributions.sort(key=lambda a: a.market_value, reverse=True)
        return attributions
