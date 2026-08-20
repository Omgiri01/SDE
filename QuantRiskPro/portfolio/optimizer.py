"""
optimizer.py
------------
Modern Portfolio Theory optimizer using SciPy.

Two optimization targets:
  1. Minimum Variance Portfolio  — lowest possible volatility
  2. Maximum Sharpe Portfolio    — best risk-adjusted return (tangency portfolio)

Also runs a 10,000-portfolio Monte Carlo simulation to map the efficient frontier.
This scatter plot is what the dashboard renders — it's visually compelling and
actually useful for showing recruiter panels why diversification matters.

WHY SciPy SLSQP over analytical solution:
- Analytical MPT only works with N assets and no constraints
- Real portfolios have long-only constraints (no shorting), max position limits, etc.
- SLSQP handles all of that as linear inequality constraints
- Same solver used by most institutional portfolio management systems
"""

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.optimize import minimize

TRADING_DAYS = 252
RISK_FREE_RATE = 0.053  # Fed funds ~5.3%


@dataclass
class PortfolioStats:
    """Statistics for a single portfolio (set of weights)."""
    weights: list[float]
    symbols: list[str]
    expected_return: float   # Annualized, %
    volatility: float        # Annualized, %
    sharpe: float
    weights_dict: dict = field(default_factory=dict)

    def __post_init__(self):
        self.weights_dict = dict(zip(self.symbols, [round(w, 6) for w in self.weights]))


@dataclass
class FrontierPoint:
    """Single point on the efficient frontier scatter plot."""
    expected_return: float
    volatility: float
    sharpe: float


@dataclass
class OptimizationResult:
    """Full output of the portfolio optimization."""
    symbols: list[str]
    min_variance: PortfolioStats
    max_sharpe: PortfolioStats
    frontier: list[FrontierPoint]          # Monte Carlo scatter (10k points)
    mean_returns: list[float]              # Annualized expected returns per symbol
    correlation_matrix: list[list[float]]  # N×N correlation matrix


class PortfolioOptimizer:
    """
    Fits MPT optimizer to historical price data.

    Usage:
        optimizer = PortfolioOptimizer(symbols, prices_matrix)
        result = optimizer.optimize()
    """

    def __init__(self, symbols: list[str], prices: np.ndarray):
        """
        Args:
            symbols: List of ticker symbols, length N
            prices:  2D array, shape (T, N) — T time steps, N assets
                     Each column is one symbol's price history.
        """
        if prices.shape[1] != len(symbols):
            raise ValueError(f"prices has {prices.shape[1]} columns but {len(symbols)} symbols")
        if prices.shape[0] < 30:
            raise ValueError("Need at least 30 price observations")

        self.symbols = symbols
        self.n = len(symbols)

        # Compute log returns: shape (T-1, N)
        log_returns = np.diff(np.log(prices), axis=0)

        # Mean daily return per symbol → annualize
        self.mean_returns = log_returns.mean(axis=0) * TRADING_DAYS

        # Covariance matrix of daily returns → annualize
        self.cov_matrix = np.cov(log_returns.T) * TRADING_DAYS

        # Correlation matrix (for display)
        std = np.sqrt(np.diag(self.cov_matrix))
        self.corr_matrix = self.cov_matrix / np.outer(std, std)

    def _portfolio_stats(self, weights: np.ndarray) -> tuple[float, float, float]:
        """
        Compute (return, volatility, sharpe) for a given weight vector.
        All values are annualized.
        """
        ret = float(weights @ self.mean_returns)
        vol = float(math.sqrt(weights @ self.cov_matrix @ weights))
        sharpe = (ret - RISK_FREE_RATE) / vol if vol > 0 else 0.0
        return ret, vol, sharpe

    def _to_stats(self, weights: np.ndarray) -> PortfolioStats:
        ret, vol, sharpe = self._portfolio_stats(weights)
        return PortfolioStats(
            weights=weights.tolist(),
            symbols=self.symbols,
            expected_return=round(ret * 100, 4),
            volatility=round(vol * 100, 4),
            sharpe=round(sharpe, 4),
        )

    def _min_variance_weights(self) -> np.ndarray:
        """
        Solve: min w^T Σ w
        s.t.  Σ w_i = 1,  w_i >= 0 (long-only)

        This finds the portfolio with the absolute lowest volatility.
        """
        n = self.n
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bounds = [(0.0, 1.0)] * n
        w0 = np.ones(n) / n  # Equal weight starting point

        result = minimize(
            lambda w: (w @ self.cov_matrix @ w),
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        return result.x

    def _max_sharpe_weights(self) -> np.ndarray:
        """
        Solve: max (w^T μ - r_f) / sqrt(w^T Σ w)
        s.t.  Σ w_i = 1,  w_i >= 0

        Maximizing Sharpe = finding the tangency portfolio on the CML.
        SciPy minimizes, so we minimize negative Sharpe.
        """
        n = self.n

        def neg_sharpe(w: np.ndarray) -> float:
            ret, vol, _ = self._portfolio_stats(w)
            if vol < 1e-10:
                return 0.0
            return -(ret - RISK_FREE_RATE) / vol

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bounds = [(0.0, 1.0)] * n
        w0 = np.ones(n) / n

        result = minimize(
            neg_sharpe,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        return result.x

    def monte_carlo_frontier(self, n_portfolios: int = 10_000) -> list[FrontierPoint]:
        """
        Generate N random portfolios and compute their (return, vol, sharpe).

        This creates the scatter plot that IS the efficient frontier visualization.
        Each dot is a possible portfolio; the upper-left boundary is the frontier.

        Recruiters find this compelling because it visually demonstrates:
        - Diversification reducing risk
        - The concave shape of the frontier (diminishing returns to risk-taking)
        """
        rng = np.random.default_rng(seed=42)
        points = []

        for _ in range(n_portfolios):
            # Random weights that sum to 1
            raw = rng.dirichlet(np.ones(self.n))
            ret, vol, sharpe = self._portfolio_stats(raw)
            points.append(FrontierPoint(
                expected_return=round(ret * 100, 4),
                volatility=round(vol * 100, 4),
                sharpe=round(sharpe, 4),
            ))

        return points

    def optimize(self, n_simulations: int = 10_000) -> OptimizationResult:
        """Run full optimization: min-var, max-sharpe, and Monte Carlo frontier."""
        min_var_w = self._min_variance_weights()
        max_sharpe_w = self._max_sharpe_weights()
        frontier = self.monte_carlo_frontier(n_simulations)

        return OptimizationResult(
            symbols=self.symbols,
            min_variance=self._to_stats(min_var_w),
            max_sharpe=self._to_stats(max_sharpe_w),
            frontier=frontier,
            mean_returns=[round(float(r) * 100, 4) for r in self.mean_returns],
            correlation_matrix=self.corr_matrix.tolist(),
        )
