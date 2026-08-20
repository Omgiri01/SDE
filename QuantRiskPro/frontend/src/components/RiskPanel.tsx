import { useCallback } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import type { PortfolioRisk, RiskMetrics } from '../types'

function fmt(n: number | null | undefined, dec = 2) {
  if (n == null) return '—'
  return n.toFixed(dec)
}

function Gauge({ label, value, unit, color }: { label: string; value: string; unit?: string; color: string }) {
  return (
    <div className="gauge" style={{ borderColor: color }}>
      <div className="gauge__value" style={{ color }}>{value}{unit}</div>
      <div className="gauge__label">{label}</div>
    </div>
  )
}

function SymbolRisk({ symbol, metrics }: { symbol: string; metrics: RiskMetrics }) {
  const sharpe = metrics.ratios?.sharpe
  const vol20d = metrics.volatility?.vol_20d
  const var95 = metrics.var?.var_95
  const drawdown = metrics.drawdown?.current_drawdown

  const sharpeColor = sharpe == null ? '#888' : sharpe > 1 ? '#22c55e' : sharpe > 0 ? '#eab308' : '#ef4444'
  const volColor = vol20d == null ? '#888' : vol20d < 20 ? '#22c55e' : vol20d < 40 ? '#eab308' : '#ef4444'
  const varColor = var95 == null ? '#888' : var95 < 2 ? '#22c55e' : var95 < 3 ? '#eab308' : '#ef4444'
  const ddColor = drawdown == null ? '#888' : drawdown > -5 ? '#22c55e' : drawdown > -10 ? '#eab308' : '#ef4444'

  return (
    <div className="symbol-risk">
      <div className="symbol-risk__header">
        <span className="symbol-risk__name">{symbol}</span>
        <span className="symbol-risk__price">${fmt(metrics.current_price)}</span>
      </div>
      <div className="symbol-risk__gauges">
        <Gauge label="Sharpe"   value={fmt(sharpe, 2)}   color={sharpeColor} />
        <Gauge label="Vol 20d"  value={fmt(vol20d, 1)}  unit="%" color={volColor} />
        <Gauge label="VaR 95%"  value={fmt(var95, 2)}   unit="%" color={varColor} />
        <Gauge label="Drawdown" value={fmt(drawdown, 1)} unit="%" color={ddColor} />
      </div>
      {metrics.alerts.length > 0 && (
        <div className="symbol-risk__alerts">
          {metrics.alerts.map((a, i) => <div key={i} className="inline-alert">⚠ {a}</div>)}
        </div>
      )}
    </div>
  )
}

export function RiskPanel() {
  const fetcher = useCallback(() => api.getPortfolioRisk(), [])
  const { data, loading, error } = useApi<PortfolioRisk>(fetcher, 30_000)

  if (loading) return <section className="panel"><h2>Risk Metrics</h2><div className="loading">Loading risk data…</div></section>
  if (error)   return <section className="panel"><h2>Risk Metrics</h2><div className="error">Risk engine offline: {error}</div></section>
  if (!data)   return null

  const symbols = data.symbols_computed

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Risk Metrics</h2>
        <span className="panel__sub">
          {symbols.length}/{symbols.length + data.symbols_missing_data.length} symbols computed · refreshes every 30s
        </span>
      </div>

      {symbols.length === 0 && (
        <div className="empty-state">
          Risk engine not running. Start it with: <code>python -m risk.engine</code>
        </div>
      )}

      <div className="risk-grid">
        {symbols.map((sym) => {
          const m = data.metrics[sym]
          return m ? <SymbolRisk key={sym} symbol={sym} metrics={m} /> : null
        })}
      </div>

      {data.symbols_missing_data.length > 0 && (
        <div className="missing-note">
          No data yet for: {data.symbols_missing_data.join(', ')}
        </div>
      )}
    </section>
  )
}
