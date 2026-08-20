// Manages the WebSocket connection to ws://localhost:8000/ws/live.
// Reconnects automatically on close/error with exponential backoff.
// Exposes live prices as a map: symbol → { price, change_pct, timestamp }.

import { useEffect, useRef, useState, useCallback } from 'react'
import type { WSPricePayload } from '../types'

export interface LiveTick {
  price: number
  change_pct: number | null
  volume: number | null
  vwap: number | null
  timestamp: string
}

type PriceMap = Record<string, LiveTick>

export function useWebSocket() {
  const [prices, setPrices] = useState<PriceMap>({})
  const [alerts, setAlerts] = useState<{ symbol: string; alert: string }[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectDelay = useRef(1000)
  const unmounted = useRef(false)

  const connect = useCallback(() => {
    if (unmounted.current) return

    const ws = new WebSocket(`ws://${window.location.host}/ws/live`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      reconnectDelay.current = 1000
    }

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)

        if (msg.type === 'price_update') {
          const updates = msg.payload as WSPricePayload[]
          setPrices((prev) => {
            const next = { ...prev }
            for (const u of updates) {
              next[u.symbol] = {
                price: u.price,
                change_pct: u.change_pct,
                volume: u.volume,
                vwap: u.vwap,
                timestamp: u.timestamp,
              }
            }
            return next
          })
        }

        if (msg.type === 'risk_alerts') {
          const incoming = msg.payload as { symbol: string; alert: string }[]
          setAlerts(incoming)
        }
      } catch {
        // ignore malformed frames
      }
    }

    ws.onerror = () => {
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
      if (!unmounted.current) {
        setTimeout(connect, reconnectDelay.current)
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30_000)
      }
    }
  }, [])

  useEffect(() => {
    unmounted.current = false
    connect()
    return () => {
      unmounted.current = true
      wsRef.current?.close()
    }
  }, [connect])

  return { prices, alerts, connected }
}
