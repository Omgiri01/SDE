import { useCallback } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../api/client'
import type { Health } from '../types'

export function HealthBar() {
  const fetcher = useCallback(() => api.getHealth(), [])
  const { data } = useApi<Health>(fetcher, 30_000)

  if (!data) return null

  const redis = data.services['redis']
  const tsdb  = data.services['timescaledb']

  function dot(status: string) {
    return status === 'ok' ? '●' : '○'
  }
  function cls(status: string) {
    return status === 'ok' ? 'health-ok' : 'health-down'
  }

  return (
    <div className="health-bar">
      <span className={cls(redis?.status ?? 'down')}>
        {dot(redis?.status ?? 'down')} Redis {redis?.latency_ms != null ? `${redis.latency_ms.toFixed(1)}ms` : ''}
      </span>
      <span className={cls(tsdb?.status ?? 'down')}>
        {dot(tsdb?.status ?? 'down')} TimescaleDB {tsdb?.latency_ms != null ? `${tsdb.latency_ms.toFixed(1)}ms` : ''}
      </span>
      <span className="health-neutral">
        {data.tickers_with_data}/{data.tickers_watched.length} tickers live
      </span>
      <span className="health-neutral">
        uptime {Math.floor(data.uptime_seconds / 60)}m
      </span>
    </div>
  )
}
