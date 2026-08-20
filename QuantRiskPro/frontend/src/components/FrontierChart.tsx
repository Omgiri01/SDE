import { useCallback } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceDot, Legend,
} from 'recharts'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import type { Frontier } from '../types'

function SharpeTooltip({ active, payload }: { active?: boolean; payload?: { payload: { expected_return: number; volatility: number; sharpe: number } }[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="chart-tooltip">
      <div>Return: <strong>{d.expected_return.toFixed(2)}%</strong></div>
      <div>Volatility: <strong>{d.volatility.toFixed(2)}%</strong></div>
      <div>Sharpe: <strong>{d.sharpe.toFixed(3)}</strong></div>
    </div>
  )
}

// Color each point by Sharpe ratio: red (low) → yellow → green (high)
function sharpeToColor(sharpe: number): string {
  if (sharpe > 1.5) return '#22c55e'
  if (sharpe > 0.5) return '#84cc16'
  if (sharpe > 0)   return '#eab308'
  if (sharpe > -0.5) return '#f97316'
  return '#ef4444'
}

export function FrontierChart() {
  const fetcher = useCallback(() => api.getFrontier(), [])
  const { data, loading, error } = useApi<Frontier>(fetcher, null)  // compute once

  if (loading) return (
    <section className="panel">
      <h2>Efficient Frontier</h2>
      <div className="loading">Computing 10,000 portfolio simulations…</div>
    </section>
  )

  if (error) return (
    <section className="panel">
      <h2>Efficient Frontier</h2>
      <div className="error">Frontier unavailable: {error}</div>
    </section>
  )

  if (!data) return null

  // Downsample scatter to 2000 points for smooth rendering
  const step = Math.max(1, Math.floor(data.frontier.length / 2000))
  const scatter = data.frontier
    .filter((_, i) => i % step === 0)
    .map((p) => ({ ...p, fill: sharpeToColor(p.sharpe) }))

  const mv = data.min_variance
  const ms = data.max_sharpe

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Efficient Frontier</h2>
        <span className="panel__sub">{data.n_simulations.toLocaleString()} simulated portfolios · {data.symbols.join(', ')}</span>
      </div>

      <div className="frontier-legend">
        <span className="legend-dot" style={{ background: '#22c55e' }} /> High Sharpe
        <span className="legend-dot" style={{ background: '#eab308' }} /> Neutral
        <span className="legend-dot" style={{ background: '#ef4444' }} /> Negative Sharpe
        <span className="legend-star">★</span> Min Variance
        <span className="legend-star" style={{ color: '#a855f7' }}>★</span> Max Sharpe
      </div>

      <ResponsiveContainer width="100%" height={380}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
          <XAxis
            dataKey="volatility"
            type="number"
            name="Volatility"
            label={{ value: 'Volatility (%)', position: 'insideBottom', offset: -10, fill: '#888' }}
            tick={{ fill: '#888', fontSize: 11 }}
            domain={['auto', 'auto']}
          />
          <YAxis
            dataKey="expected_return"
            type="number"
            name="Expected Return"
            label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft', offset: 10, fill: '#888' }}
            tick={{ fill: '#888', fontSize: 11 }}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<SharpeTooltip />} cursor={{ strokeDasharray: '3 3' }} />

          <Scatter
            data={scatter}
            name="Portfolios"
            shape={(props: { cx?: number; cy?: number; fill?: string }) => (
              <circle
                cx={props.cx}
                cy={props.cy}
                r={2.5}
                fill={props.fill ?? '#4f7cff'}
                fillOpacity={0.6}
              />
            )}
          />

          {/* Min Variance star */}
          <ReferenceDot
            x={mv.volatility}
            y={mv.expected_return}
            r={8}
            fill="#facc15"
            stroke="#fff"
            strokeWidth={1.5}
            label={{ value: '★ MinVol', position: 'top', fill: '#facc15', fontSize: 11 }}
          />

          {/* Max Sharpe star */}
          <ReferenceDot
            x={ms.volatility}
            y={ms.expected_return}
            r={8}
            fill="#a855f7"
            stroke="#fff"
            strokeWidth={1.5}
            label={{ value: '★ MaxSharpe', position: 'top', fill: '#a855f7', fontSize: 11 }}
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Optimal portfolio summary */}
      <div className="frontier-summary">
        <div className="frontier-portfolio">
          <div className="fp-title" style={{ color: '#facc15' }}>Min Variance</div>
          <div className="fp-stats">
            Return: {mv.expected_return.toFixed(2)}% · Vol: {mv.volatility.toFixed(2)}% · Sharpe: {mv.sharpe.toFixed(3)}
          </div>
          <div className="fp-weights">
            {Object.entries(mv.weights)
              .filter(([, w]) => w > 0.01)
              .sort(([, a], [, b]) => b - a)
              .map(([sym, w]) => (
                <span key={sym} className="weight-chip">{sym} {(w * 100).toFixed(1)}%</span>
              ))}
          </div>
        </div>

        <div className="frontier-portfolio">
          <div className="fp-title" style={{ color: '#a855f7' }}>Max Sharpe (Tangency)</div>
          <div className="fp-stats">
            Return: {ms.expected_return.toFixed(2)}% · Vol: {ms.volatility.toFixed(2)}% · Sharpe: {ms.sharpe.toFixed(3)}
          </div>
          <div className="fp-weights">
            {Object.entries(ms.weights)
              .filter(([, w]) => w > 0.01)
              .sort(([, a], [, b]) => b - a)
              .map(([sym, w]) => (
                <span key={sym} className="weight-chip">{sym} {(w * 100).toFixed(1)}%</span>
              ))}
          </div>
        </div>
      </div>
    </section>
  )
}
