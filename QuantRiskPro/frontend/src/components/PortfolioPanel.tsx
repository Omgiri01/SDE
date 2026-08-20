import { useCallback, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import type { Portfolio, Rebalance } from '../types'

function fmt(n: number | null | undefined, dec = 2) {
  if (n == null) return '—'
  return n.toFixed(dec)
}

function fmtDollar(n: number | null | undefined) {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

function PnlBadge({ pnl, pct }: { pnl: number | null; pct: number | null }) {
  if (pnl == null) return <span className="pnl-badge neutral">—</span>
  const cls = pnl >= 0 ? 'positive' : 'negative'
  const sign = pnl >= 0 ? '+' : ''
  return (
    <span className={`pnl-badge ${cls}`}>
      {sign}{fmtDollar(pnl)} ({sign}{fmt(pct, 2)}%)
    </span>
  )
}

function RebalancePanel({ rebalance }: { rebalance: Rebalance }) {
  if (!rebalance.needs_rebalancing) {
    return <div className="rebalance-ok">✓ Portfolio within {rebalance.drift_threshold_pct}% drift threshold — no rebalancing needed</div>
  }
  return (
    <div className="rebalance-orders">
      <div className="rebalance-header">
        ⚡ {rebalance.estimated_trades} trades · ~{rebalance.estimated_turnover_pct}% turnover
        · Drifted: {rebalance.drifted_symbols.join(', ')}
      </div>
      <div className="orders-list">
        {rebalance.orders.map((o, i) => (
          <div key={i} className={`order order--${o.side.toLowerCase()}`}>
            <span className="order__side">{o.side}</span>
            <span className="order__qty">{o.quantity.toFixed(2)} shares</span>
            <span className="order__sym">{o.symbol}</span>
            <span className="order__drift">drift: {o.drift_pct > 0 ? '+' : ''}{fmt(o.drift_pct)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function PortfolioPanel() {
  const portfolioFetcher = useCallback(() => api.getPortfolio(), [])
  const { data: portfolio, loading, error } = useApi<Portfolio>(portfolioFetcher, 15_000)

  const [rebalance, setRebalance] = useState<Rebalance | null>(null)
  const [rebalancing, setRebalancing] = useState(false)

  async function handleRebalance() {
    setRebalancing(true)
    try {
      const result = await api.triggerRebalance()
      setRebalance(result)
    } catch {
      // silently ignore — API might be busy
    } finally {
      setRebalancing(false)
    }
  }

  if (loading) return <section className="panel"><h2>Portfolio</h2><div className="loading">Loading portfolio…</div></section>
  if (error)   return <section className="panel"><h2>Portfolio</h2><div className="error">Portfolio unavailable: {error}</div></section>
  if (!portfolio) return null

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Portfolio</h2>
        <button className="btn" onClick={handleRebalance} disabled={rebalancing}>
          {rebalancing ? 'Analyzing…' : 'Analyze Rebalance'}
        </button>
      </div>

      {/* Summary strip */}
      <div className="portfolio-summary">
        <div className="summary-item">
          <span className="summary-label">Total Value</span>
          <span className="summary-value">{fmtDollar(portfolio.total_value)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Equity</span>
          <span className="summary-value">{fmtDollar(portfolio.total_equity_value)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Cash</span>
          <span className="summary-value">{fmtDollar(portfolio.cash_balance)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Unrealized P&L</span>
          <PnlBadge pnl={portfolio.total_unrealized_pnl} pct={portfolio.total_unrealized_pnl_pct} />
        </div>
      </div>

      {/* Positions table */}
      <div className="table-wrapper">
        <table className="positions-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Qty</th>
              <th>Avg Cost</th>
              <th>Price</th>
              <th>Mkt Value</th>
              <th>P&L</th>
              <th>Weight</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.positions.map((pos) => (
              <tr key={pos.symbol}>
                <td className="sym-cell">{pos.symbol}</td>
                <td>{pos.quantity.toFixed(2)}</td>
                <td>${fmt(pos.avg_cost)}</td>
                <td>{pos.current_price ? `$${fmt(pos.current_price)}` : '—'}</td>
                <td>{fmtDollar(pos.market_value)}</td>
                <td><PnlBadge pnl={pos.unrealized_pnl} pct={pos.unrealized_pnl_pct} /></td>
                <td>{pos.weight != null ? `${pos.weight.toFixed(1)}%` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rebalance && <RebalancePanel rebalance={rebalance} />}
    </section>
  )
}
