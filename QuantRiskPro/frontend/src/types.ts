// TypeScript interfaces matching the FastAPI Pydantic models exactly.
// Keep these in sync with api/models.py.

export interface LivePrice {
  symbol: string
  close: number | null
  open: number | null
  high: number | null
  low: number | null
  volume: number | null
  vwap: number | null
  timestamp: string | null
  source: string
}

export interface OHLCVBar {
  time: string
  symbol: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  vwap: number | null
}

export interface VaR {
  var_95: number
  var_99: number
  var_95_dollar: number
  var_99_dollar: number
  method: string
  lookback_days: number
}

export interface Volatility {
  vol_20d: number | null
  vol_60d: number | null
  daily_vol: number
  latest_return: number
}

export interface Ratios {
  sharpe: number | null
  sortino: number | null
  annualized_return: number
  risk_free_rate: number
}

export interface Drawdown {
  current_drawdown: number
  max_drawdown: number
  peak_price: number
  trough_price: number
}

export interface RiskMetrics {
  symbol: string
  current_price: number
  computed_at: string
  alerts: string[]
  var: VaR | null
  volatility: Volatility | null
  ratios: Ratios | null
  drawdown: Drawdown | null
  data_source: string
}

export interface PortfolioRisk {
  portfolio_id: number
  symbols_computed: string[]
  symbols_missing_data: string[]
  active_alerts: string[]
  metrics: Record<string, RiskMetrics | null>
  computed_at: string
}

export interface Position {
  symbol: string
  quantity: number
  avg_cost: number
  current_price: number | null
  market_value: number | null
  cost_basis: number | null
  unrealized_pnl: number | null
  unrealized_pnl_pct: number | null
  weight: number | null
}

export interface Portfolio {
  portfolio_id: number
  name: string
  cash_balance: number
  total_equity_value: number
  total_value: number
  total_unrealized_pnl: number
  total_unrealized_pnl_pct: number
  positions: Position[]
  as_of: string
}

export interface FrontierPoint {
  expected_return: number
  volatility: number
  sharpe: number
}

export interface FrontierPortfolio {
  weights: Record<string, number>
  expected_return: number
  volatility: number
  sharpe: number
}

export interface Frontier {
  symbols: string[]
  frontier: FrontierPoint[]
  min_variance: FrontierPortfolio
  max_sharpe: FrontierPortfolio
  n_simulations: number
  computed_at: string
}

export interface RebalanceOrder {
  symbol: string
  side: 'BUY' | 'SELL'
  quantity: number
  target_value: number
  current_value: number
  drift_pct: number
}

export interface Rebalance {
  needs_rebalancing: boolean
  drift_threshold_pct: number
  drifted_symbols: string[]
  orders: RebalanceOrder[]
  estimated_trades: number
  estimated_turnover_pct: number
  current_weights: Record<string, number>
  target_weights: Record<string, number>
  computed_at: string
}

export interface ServiceStatus {
  status: 'ok' | 'degraded' | 'down'
  latency_ms: number | null
  detail: string | null
}

export interface Health {
  status: string
  version: string
  services: Record<string, ServiceStatus>
  tickers_watched: string[]
  tickers_with_data: number
  uptime_seconds: number
  checked_at: string
}

// WebSocket message shapes
export interface WSPricePayload {
  symbol: string
  price: number
  change_pct: number | null
  volume: number | null
  vwap: number | null
  timestamp: string
}

export interface WSMessage {
  type: 'price_update' | 'risk_alerts' | 'connected' | 'pong'
  payload: WSPricePayload[] | unknown
  timestamp?: string
}
