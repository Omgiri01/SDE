"""
metrics.py
----------
Pure mathematical implementation of institutional risk metrics.
No external finance libraries — every formula implemented from first principles.

This is intentional. In interviews you need to explain:
  - WHY we use historical simulation for VaR (not parametric)
  - WHY Sortino is better than Sharpe for asymmetric return distributions
  - WHY we annualize volatility by multiplying by sqrt(252)

If you pulled these from a library you couldn't explain any of that.
"""

import math
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class VaRResult:
    """Value at Risk result at multiple confidence levels."""
    var_95: float          # 95% confidence VaR (daily, as % of portfolio)
    var_99: float          # 99% confidence VaR
    var_95_dollar: float   # Dollar value at risk (95%)
    var_99_dollar: float   # Dollar value at risk (99%)
    method: str            # 'historical' or 'parametric'
    lookback_days: int     # Number of days of history used


@dataclass
class VolatilityResult:
    """Rolling volatility at multiple windows."""
    vol_20d: Optional[float]    # 20-day annualized volatility (%)
    vol_60d: Optional[float]    # 60-day annualized volatility (%)
    daily_vol: float            # Raw daily volatility (not annualized)
    latest_return: float        # Most recent daily return


@dataclass
class RatioResult:
    """Sharpe and Sortino ratios."""
    sharpe: Optional[float]     # (return - risk_free) / total_volatility
    sortino: Optional[float]    # (return - risk_free) / downside_volatility
    annualized_return: float    # Annualized return of the period
    risk_free_rate: float       # Risk-free rate used (annualized)


@dataclass
class DrawdownResult:
    """Drawdown analysis."""
    current_drawdown: float     # Current drawdown from peak (%)
    max_drawdown: float         # Maximum drawdown in the period (%)
    peak_price: float           # Highest price in the period
    trough_price: float         # Lowest price after the peak


@dataclass
class RiskReport:
    """Complete risk report for a single symbol."""
    symbol: str
    current_price: float
    var: Optional[VaRResult] = None
    volatility: Optional[VolatilityResult] = None
    ratios: Optional[RatioResult] = None
    drawdown: Optional[DrawdownResult] = None
    alerts: list[str] = field(default_factory=list)
    computed_at: str = ""


# ── Core Math Functions ───────────────────────────────────────────────────────

def compute_returns(prices: list[float]) -> np.ndarray:
    """
    Compute daily log returns from a price series.

    We use LOG returns (not simple returns) because:
    1. Log returns are time-additive: r_total = r_1 + r_2 + ... + r_n
    2. They're more normally distributed — important for VaR assumptions
    3. They prevent negative prices in simulations

    Formula: r_t = ln(P_t / P_{t-1})
    """
    if len(prices) < 2:
        return np.array([])
    prices_arr = np.array(prices, dtype=float)
    # np.diff(np.log(prices)) is equivalent to ln(P_t/P_{t-1}) for all t
    return np.diff(np.log(prices_arr))


def compute_var(
    returns: np.ndarray,
    portfolio_value: float,
    confidence_levels: tuple[float, float] = (0.95, 0.99)
) -> Optional[VaRResult]:
    """
    Historical Simulation VaR.

    Method: Sort historical returns, take the loss at the Nth percentile.

    WHY historical simulation over parametric (normal distribution) VaR:
    - Real returns have "fat tails" — extreme events happen more often than
      a normal distribution predicts (see: 2008 crash, COVID drop)
    - Historical simulation makes NO assumptions about the distribution shape
    - It naturally captures skewness and kurtosis from real market behavior
    - Parametric VaR underestimates tail risk by 20-40% in volatile markets

    Args:
        returns: Array of daily log returns
        portfolio_value: Current portfolio value in dollars
        confidence_levels: Tuple of (95%, 99%) confidence levels

    Returns:
        VaRResult with dollar and percentage VaR at both confidence levels
    """
    if len(returns) < 30:
        return None  # Need at least 30 days for meaningful VaR

    cl_95, cl_99 = confidence_levels

    # Sort returns ascending — worst losses are at the left tail
    sorted_returns = np.sort(returns)

    # VaR at 95%: the loss we'd exceed only 5% of the time
    # np.percentile(returns, 5) gives the 5th percentile (left tail)
    var_95_pct = float(np.percentile(sorted_returns, (1 - cl_95) * 100))
    var_99_pct = float(np.percentile(sorted_returns, (1 - cl_99) * 100))

    # Convert to positive dollar losses (VaR is reported as a positive number)
    var_95_dollar = abs(var_95_pct) * portfolio_value
    var_99_dollar = abs(var_99_pct) * portfolio_value

    return VaRResult(
        var_95=abs(var_95_pct) * 100,       # As percentage
        var_99=abs(var_99_pct) * 100,
        var_95_dollar=round(var_95_dollar, 2),
        var_99_dollar=round(var_99_dollar, 2),
        method="historical_simulation",
        lookback_days=len(returns),
    )


def compute_volatility(returns: np.ndarray) -> Optional[VolatilityResult]:
    """
    Rolling annualized volatility.

    Annualization formula: σ_annual = σ_daily × √252
    WHY √252: There are ~252 trading days per year. Variance scales linearly
    with time, so standard deviation scales with √time.

    We compute at two windows:
    - 20-day: captures recent/short-term volatility regime
    - 60-day: captures medium-term volatility (less noise)

    Comparing 20d vs 60d tells you if volatility is expanding or contracting.
    """
    if len(returns) < 2:
        return None

    trading_days_per_year = 252
    latest_return = float(returns[-1])
    daily_vol = float(np.std(returns, ddof=1))  # ddof=1 for sample std dev

    # 20-day volatility
    vol_20d = None
    if len(returns) >= 20:
        recent_20 = returns[-20:]
        vol_20d = round(float(np.std(recent_20, ddof=1)) * math.sqrt(trading_days_per_year) * 100, 4)

    # 60-day volatility
    vol_60d = None
    if len(returns) >= 60:
        recent_60 = returns[-60:]
        vol_60d = round(float(np.std(recent_60, ddof=1)) * math.sqrt(trading_days_per_year) * 100, 4)

    return VolatilityResult(
        vol_20d=vol_20d,
        vol_60d=vol_60d,
        daily_vol=round(daily_vol * 100, 4),
        latest_return=round(latest_return * 100, 4),
    )


def compute_ratios(
    returns: np.ndarray,
    risk_free_rate: float = 0.053  # ~5.3% (current Fed funds rate)
) -> Optional[RatioResult]:
    """
    Sharpe and Sortino ratios.

    SHARPE RATIO = (R_portfolio - R_risk_free) / σ_total
    Measures: How much excess return per unit of TOTAL risk (up and down moves)

    SORTINO RATIO = (R_portfolio - R_risk_free) / σ_downside
    Measures: How much excess return per unit of DOWNSIDE risk only

    WHY Sortino is often better:
    - Sharpe penalizes upside volatility (big up days hurt your Sharpe)
    - For asymmetric strategies, Sortino gives a truer picture of risk-adjusted return
    - A strategy that goes up a lot but rarely goes down has high Sortino, lower Sharpe

    Interpretation:
    - Sharpe > 1.0: Good
    - Sharpe > 2.0: Very good
    - Sharpe > 3.0: Exceptional (rare outside HFT)
    """
    if len(returns) < 20:
        return None

    trading_days = 252
    daily_rf = risk_free_rate / trading_days

    # Annualized return
    mean_daily_return = float(np.mean(returns))
    annualized_return = mean_daily_return * trading_days

    # Excess returns over risk-free rate
    excess_returns = returns - daily_rf

    # Total volatility (all returns)
    total_vol = float(np.std(returns, ddof=1)) * math.sqrt(trading_days)

    # Downside volatility (only negative excess returns)
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) < 2:
        downside_vol = total_vol  # Fallback if no negative returns
    else:
        downside_vol = float(np.std(downside_returns, ddof=1)) * math.sqrt(trading_days)

    # Compute ratios
    sharpe = None
    sortino = None

    if total_vol > 0:
        annualized_excess = float(np.mean(excess_returns)) * trading_days
        sharpe = round(annualized_excess / total_vol, 4)

    if downside_vol > 0:
        annualized_excess = float(np.mean(excess_returns)) * trading_days
        sortino = round(annualized_excess / downside_vol, 4)

    return RatioResult(
        sharpe=sharpe,
        sortino=sortino,
        annualized_return=round(annualized_return * 100, 4),
        risk_free_rate=risk_free_rate * 100,
    )


def compute_drawdown(prices: list[float]) -> Optional[DrawdownResult]:
    """
    Maximum drawdown and current drawdown.

    Drawdown = (Peak - Trough) / Peak × 100

    This measures the largest peak-to-trough decline in the price series.
    It's the most intuitive risk metric for portfolio managers:
    "At worst, how much did we lose from the top?"

    Current drawdown tells you where you are NOW relative to the recent peak.
    """
    if len(prices) < 2:
        return None

    prices_arr = np.array(prices, dtype=float)

    # Running maximum — the "peak" at each point in time
    running_max = np.maximum.accumulate(prices_arr)

    # Drawdown at each point: how far below the peak are we?
    drawdowns = (prices_arr - running_max) / running_max * 100

    max_drawdown = float(np.min(drawdowns))         # Most negative = worst drawdown
    current_drawdown = float(drawdowns[-1])          # Where we are now
    peak_price = float(np.max(prices_arr))
    trough_idx = int(np.argmin(drawdowns))
    trough_price = float(prices_arr[trough_idx])

    return DrawdownResult(
        current_drawdown=round(current_drawdown, 4),
        max_drawdown=round(max_drawdown, 4),
        peak_price=round(peak_price, 4),
        trough_price=round(trough_price, 4),
    )


# ── Alert Engine ──────────────────────────────────────────────────────────────

@dataclass
class AlertThresholds:
    """Configurable thresholds for risk alerts."""
    max_var_95_pct: float = 3.0          # Alert if VaR 95% > 3% of portfolio
    max_volatility_20d: float = 40.0     # Alert if 20d vol > 40% annualized
    min_sharpe: float = 0.0              # Alert if Sharpe < 0 (losing vs risk-free)
    max_drawdown: float = -15.0          # Alert if drawdown worse than -15%
    max_current_drawdown: float = -10.0  # Alert if currently down > 10% from peak


def check_alerts(report: RiskReport, thresholds: AlertThresholds = AlertThresholds()) -> list[str]:
    """
    Check all risk metrics against thresholds and return human-readable alerts.
    These alerts will appear on the dashboard and trigger notifications.
    """
    alerts = []

    if report.var and report.var.var_95 > thresholds.max_var_95_pct:
        alerts.append(
            f"HIGH VAR: {report.symbol} 95% VaR is {report.var.var_95:.2f}% "
            f"(${report.var.var_95_dollar:,.0f}) — exceeds {thresholds.max_var_95_pct}% threshold"
        )

    if report.volatility and report.volatility.vol_20d:
        if report.volatility.vol_20d > thresholds.max_volatility_20d:
            alerts.append(
                f"HIGH VOLATILITY: {report.symbol} 20d vol is {report.volatility.vol_20d:.1f}% annualized"
            )

    if report.ratios and report.ratios.sharpe is not None:
        if report.ratios.sharpe < thresholds.min_sharpe:
            alerts.append(
                f"NEGATIVE SHARPE: {report.symbol} Sharpe ratio is {report.ratios.sharpe:.2f} "
                f"— underperforming risk-free rate"
            )

    if report.drawdown:
        if report.drawdown.max_drawdown < thresholds.max_drawdown:
            alerts.append(
                f"MAX DRAWDOWN: {report.symbol} peak-to-trough decline of "
                f"{report.drawdown.max_drawdown:.1f}%"
            )
        if report.drawdown.current_drawdown < thresholds.max_current_drawdown:
            alerts.append(
                f"DRAWDOWN ALERT: {report.symbol} currently {report.drawdown.current_drawdown:.1f}% "
                f"below recent peak"
            )

    return alerts


# ── Main computation entry point ──────────────────────────────────────────────

def compute_full_risk_report(
    symbol: str,
    prices: list[float],
    portfolio_value: float = 100_000.0,
    risk_free_rate: float = 0.053,
) -> Optional[RiskReport]:
    """
    Compute all risk metrics for a symbol given its price history.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL')
        prices: List of closing prices, oldest first
        portfolio_value: Total portfolio value for dollar VaR calculation
        risk_free_rate: Annual risk-free rate (default: current Fed funds ~5.3%)

    Returns:
        Complete RiskReport with all metrics and alerts
    """
    from datetime import datetime, timezone

    if len(prices) < 5:
        return None

    returns = compute_returns(prices)
    if len(returns) == 0:
        return None

    current_price = prices[-1]

    report = RiskReport(
        symbol=symbol,
        current_price=current_price,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )

    # Compute each metric independently — if one fails, others still run
    try:
        report.var = compute_var(returns, portfolio_value)
    except Exception:
        pass

    try:
        report.volatility = compute_volatility(returns)
    except Exception:
        pass

    try:
        report.ratios = compute_ratios(returns, risk_free_rate)
    except Exception:
        pass

    try:
        report.drawdown = compute_drawdown(prices)
    except Exception:
        pass

    # Check alerts
    report.alerts = check_alerts(report)

    return report
