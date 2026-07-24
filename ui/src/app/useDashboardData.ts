import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type WebDashboardResponse, type Tool } from '../api'

const POLL_MS = 10_000

interface UseDashboardDataOptions {
  demo: boolean
  authed: boolean
  onUnauthorized: () => void
}

export function useDashboardData({ demo, authed, onUnauthorized }: UseDashboardDataOptions) {
  const [health, setHealth] = useState<WebDashboardResponse | null>(null)
  const [tools, setTools] = useState<Tool[]>([])
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingError, setStreamingError] = useState<string | null>(null)
  const [toolCategories, setToolCategories] = useState<Record<string, string[]>>({})

  const dashboardStreamRef = useRef<EventSource | null>(null)
  const dashboardPollTimer = useRef<number | null>(null)

  // Live tools fetch (demo mode gets its tools from the demo bootstrap instead)
  useEffect(() => {
    if (demo) return
    api.tools().then(r => setTools(r.tools)).catch(() => {})
  }, [demo])

  const fetchAll = useCallback(async () => {
    if (demo) return
    try {
      const h = await api.dashboard()
      setHealth(h)
      setLastRefresh(new Date())
      setError(null)
    } catch (e: unknown) {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        onUnauthorized()
      } else {
        setError('Server unreachable')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (demo || !authed) return;
    (async () => {
      try {
        const t = await api.getToolCategories();
        setToolCategories(t.categories);
      } catch (e) {
        // Optionally handle error
      }
    })();
  }, [demo, authed]);

  // Dashboard SSE with fallback to polling
  useEffect(() => {
    if (demo || !authed) return
    // Clean up any previous sources or timers
    if (dashboardStreamRef.current) dashboardStreamRef.current.close()
    if (dashboardPollTimer.current) {
      clearInterval(dashboardPollTimer.current)
      dashboardPollTimer.current = null
    }

    function startPolling() {
      // Defensive: clear any previous timers
      if (dashboardPollTimer.current) clearInterval(dashboardPollTimer.current)
      dashboardPollTimer.current = window.setInterval(() => {
        fetchAll()
      }, POLL_MS)
    }

    // Connect to SSE stream
    const es = api.dashboardStream()
    dashboardStreamRef.current = es

    es.onmessage = (e) => {
      try {
        const h = JSON.parse(e.data)
        setHealth(h)
        setLastRefresh(new Date())
        setLoading(false)
        setError(null)
        setIsStreaming(true)
        setStreamingError(null)
        if (dashboardPollTimer.current) {
          clearInterval(dashboardPollTimer.current)
          dashboardPollTimer.current = null
        }
      } catch (err) {
        setStreamingError('Malformed dashboard data')
      }
    }
    es.onerror = () => {
      setIsStreaming(false)
      setStreamingError('Dashboard stream disconnected; using polling.')
      if (!dashboardPollTimer.current) startPolling()
    }

    return () => {
      es.close()
      if (dashboardPollTimer.current) clearInterval(dashboardPollTimer.current)
    }
  }, [demo, authed, fetchAll])

  const applyDemoSnapshot = useCallback((demoHealth: WebDashboardResponse, demoTools: Tool[]) => {
    setHealth(demoHealth)
    setTools(demoTools)
    setLastRefresh(new Date())
    setLoading(false)
  }, [])

  const onProbeSuccess = useCallback((h: WebDashboardResponse) => {
    setHealth(h)
    setLoading(false)
  }, [])

  const onProbeLoadingDone = useCallback(() => {
    setLoading(false)
  }, [])

  return {
    health, tools, lastRefresh, loading, error, isStreaming, streamingError, toolCategories,
    fetchAll, applyDemoSnapshot, onProbeSuccess, onProbeLoadingDone,
  }
}
