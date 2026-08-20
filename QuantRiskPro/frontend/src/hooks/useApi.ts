// Generic polling hook — fetches data on mount and every `intervalMs`.
// Returns { data, loading, error, refetch }.

import { useState, useEffect, useCallback, useRef } from 'react'

export function useApi<T>(
  fetcher: () => Promise<T>,
  intervalMs: number | null = null,
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  const fetch_ = useCallback(async () => {
    try {
      const result = await fetcher()
      if (mountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (e) {
      if (mountedRef.current) {
        setError(e instanceof Error ? e.message : 'Unknown error')
      }
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [fetcher])

  useEffect(() => {
    mountedRef.current = true
    fetch_()

    if (intervalMs) {
      const id = setInterval(fetch_, intervalMs)
      return () => {
        clearInterval(id)
        mountedRef.current = false
      }
    }
    return () => { mountedRef.current = false }
  }, [fetch_, intervalMs])

  return { data, loading, error, refetch: fetch_ }
}
