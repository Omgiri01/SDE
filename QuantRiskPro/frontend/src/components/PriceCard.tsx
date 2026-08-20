import type { LiveTick } from '../hooks/useWebSocket'

interface Props {
  symbol: string
  tick: LiveTick | undefined
}

function fmt(n: number | null | undefined, decimals = 2) {
  if (n == null) return '—'
  return n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export function PriceCard({ symbol, tick }: Props) {
  const change = tick?.change_pct ?? null
  const isUp = change !== null && change > 0
  const isDown = change !== null && change < 0

  return (
    <div className={`price-card ${isUp ? 'up' : isDown ? 'down' : ''}`}>
      <div className="price-card__symbol">{symbol}</div>

      <div className="price-card__price">
        {tick ? `$${fmt(tick.price)}` : <span className="no-data">No data</span>}
      </div>

      {change !== null && (
        <div className={`price-card__change ${isUp ? 'positive' : 'negative'}`}>
          {isUp ? '▲' : '▼'} {Math.abs(change).toFixed(3)}%
        </div>
      )}

      {tick && (
        <div className="price-card__meta">
          <span>Vol: {tick.volume ? (tick.volume / 1e6).toFixed(1) + 'M' : '—'}</span>
          <span>VWAP: {tick.vwap ? `$${fmt(tick.vwap)}` : '—'}</span>
        </div>
      )}

      {!tick && <div className="price-card__meta">Awaiting data…</div>}
    </div>
  )
}
