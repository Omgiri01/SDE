// REST API client. All endpoints talk to /api/* which Vite proxies to :8000.

import type { LivePrice, RiskMetrics, PortfolioRisk, Portfolio, Frontier, Rebalance, Health } from '../types'

const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  getLivePrice:       (symbol: string)  => get<LivePrice>(`/prices/${symbol}`),
  getPriceHistory:    (symbol: string, days = 5) => get<{ bars: unknown[] }>(`/prices/${symbol}/history?days=${days}`),
  getRiskMetrics:     (symbol: string)  => get<RiskMetrics>(`/risk/${symbol}`),
  getPortfolioRisk:   ()               => get<PortfolioRisk>('/risk/portfolio/aggregate'),
  getPortfolio:       ()               => get<Portfolio>('/portfolio'),
  getFrontier:        ()               => get<Frontier>('/portfolio/frontier'),
  triggerRebalance:   ()               => post<Rebalance>('/portfolio/rebalance'),
  getHealth:          ()               => get<Health>('/health'),
}
