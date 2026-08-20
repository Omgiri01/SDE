import { PriceCard } from './PriceCard'
import type { LiveTick } from '../hooks/useWebSocket'

const TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'GS', 'BAC']

interface Props {
  prices: Record<string, LiveTick>
  connected: boolean
}

export function PriceGrid({ prices, connected }: Props) {
  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Live Prices</h2>
        <span className={`ws-badge ${connected ? 'ws-badge--live' : 'ws-badge--offline'}`}>
          {connected ? '● LIVE' : '○ CONNECTING…'}
        </span>
      </div>
      <div className="price-grid">
        {TICKERS.map((sym) => (
          <PriceCard key={sym} symbol={sym} tick={prices[sym]} />
        ))}
      </div>
    </section>
  )
}
