import { useState, useEffect, useCallback, useRef } from 'react'
import { FlaskConical } from 'lucide-react'
import {
  api, hasToken,
  type WebDashboardResponse, type Tool, type ToolExecResponse,
  type RunHistoryEntry as ApiRunHistoryEntry,
  type RunHistorySummaryEntry,
} from './api'

// isDemoMode/exitDemo are tiny helpers — import eagerly (no data payload).
import { isDemoMode, exitDemo } from './app/demoUtils'
import { TokenGate } from './components/TokenGate'
import { ToastProvider } from './components/ToastProvider'
import type { RunHistoryEntry } from './shared/types'

/** Extract the `Date: <ISO>` line written by analyze-session into stdout. */
function parseDateFromStdout(stdout: string): Date | null {
  const m = stdout.match(/^Date:\s+(\S+)/m)
  if (!m) return null
  const d = new Date(m[1])
  return isNaN(d.getTime()) ? null : d
}
import { routeFromHash, type Page } from './app/routing'
import { getToolsStatusWithParents } from './app/tools'
import { TopBar } from './app/TopBar'
import { THEME_STORAGE_KEY, isThemeId, type ThemeId } from './app/themes'
import { MainContent } from './app/MainContent'
import { CommandPalette } from './components/CommandPalette'
import { ReportGenerationBubble } from './components/ReportGenerationBubble'
import { ChatWidget } from './components/ChatWidget'
import './App.css'

const POLL_MS = 10_000
const PALETTE_HINT_SEEN_KEY = 'nyxstrike_palette_hint_seen'

export default function App() {
  const [demo] = useState(isDemoMode)
  const [authed, setAuthed] = useState(demo || hasToken())
  const [needsAuth, setNeedsAuth] = useState(false)
  const initialRoute = routeFromHash()
  const [page, setPageState] = useState<Page>(initialRoute.page)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(initialRoute.sessionId)

  function setPage(p: Page) {
    if (p === 'session-detail') return
    window.location.hash = `/${p === 'dashboard' ? '' : p}`
    setPageState(p)
    setActiveSessionId(null)
  }

  function openSessionDetail(sessionId: string) {
    window.location.hash = `/sessions/${sessionId}`
    setPageState('session-detail')
    setActiveSessionId(sessionId)
  }

  // Keep state in sync if the user presses Back/Forward
  useEffect(() => {
    function onHashChange() {
      const route = routeFromHash()
      setPageState(route.page)
      setActiveSessionId(route.sessionId)
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const [health, setHealth] = useState<WebDashboardResponse | null>(null)
  const [tools, setTools] = useState<Tool[]>([])
  // Lazy-load large demo data only when in demo mode; otherwise fetch from server.
  useEffect(() => {
    if (demo) {
      import('./app/demo').then(m => {
        setHealth(m.DEMO_HEALTH)
        setTools(m.DEMO_TOOLS)
        setRunHistory(m.DEMO_RUN_HISTORY)
        setLogLines(m.DEMO_LOG_LINES)
        setDemoProcesses(m.DEMO_PROCESSES)
        setDemoSessions(m.DEMO_SESSIONS)
        setDemoCpuHistory(m.demoCpuMemHistory())
        setLastRefresh(new Date())
        setLoading(false)
      })
    } else {
      api.tools().then(r => setTools(r.tools)).catch(() => {})
    }
  }, [demo])
  const [runHistory, setRunHistory] = useState<RunHistoryEntry[]>([])
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logLines, setLogLines] = useState<string[]>([])
  // Demo-mode data (null until the lazy demo chunk loads)
  const [demoProcesses, setDemoProcesses] = useState<unknown>(null)
  const [demoSessions, setDemoSessions] = useState<unknown>(null)
  const [demoCpuHistory, setDemoCpuHistory] = useState<unknown>(null)
  const [logAutoScroll, setLogAutoScroll] = useState(true)
  const [logLimit, setLogLimit] = useState(500)
  const logEndRef = useRef<HTMLDivElement>(null)
  const sseRef = useRef<EventSource | null>(null)

  // Streaming state for dashboard
  const dashboardStreamRef = useRef<EventSource | null>(null)
  const dashboardPollTimer = useRef<number | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingError, setStreamingError] = useState<string | null>(null)
  const [toolCategories, setToolCategories] = useState<Record<string, string[]>>({});
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [commandToolRequest, setCommandToolRequest] = useState<{ toolName: string; requestId: number } | null>(null)
  const [showPaletteHint, setShowPaletteHint] = useState(() => {
    try {
      return localStorage.getItem(PALETTE_HINT_SEEN_KEY) !== '1'
    } catch {
      return true
    }
  })
  const [themeId, setThemeId] = useState<ThemeId>(() => {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY)
      if (stored && isThemeId(stored)) return stored
    } catch { /* ignored */ }
    return 'dark'
  })
  const [reduceTextureEffects, setReduceTextureEffects] = useState<boolean>(() => {
    try {
      return localStorage.getItem('nyxstrike_reduce_texture_effects') === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', themeId)
    if (reduceTextureEffects) {
      document.documentElement.setAttribute('data-reduce-textures', '1')
    } else {
      document.documentElement.removeAttribute('data-reduce-textures')
    }
    try {
      localStorage.setItem(THEME_STORAGE_KEY, themeId)
      localStorage.setItem('nyxstrike_reduce_texture_effects', reduceTextureEffects ? '1' : '0')
    } catch { /* ignored */ }
  }, [themeId, reduceTextureEffects])

  useEffect(() => {
    function onGlobalKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', onGlobalKeyDown)
    return () => window.removeEventListener('keydown', onGlobalKeyDown)
  }, [])

  function handleCommandSelectTool(tool: Tool) {
    setPage('run')
    setCommandToolRequest({ toolName: tool.name, requestId: Date.now() })
  }

  function dismissPaletteHint() {
    setShowPaletteHint(false)
    try {
      localStorage.setItem(PALETTE_HINT_SEEN_KEY, '1')
    } catch {
      // ignore storage failures
    }
  }

  function openCommandPalette() {
    setPaletteOpen(true)
    if (showPaletteHint) dismissPaletteHint()
  }

  const addBrowserRunEntry = useCallback((tool: string, params: Record<string, unknown>, result: ToolExecResponse) => {
    setRunHistory(prev => {
      const entry: RunHistoryEntry = {
        id: Date.now(),
        tool,
        params,
        result,
        ts: new Date(),
        source: 'browser',
      }
      return [entry, ...prev].slice(0, 200)
    })
  }, [])

  const fetchAll = useCallback(async () => {
    if (demo) return
    try {
      const h = await api.dashboard()
      setHealth(h)
      setLastRefresh(new Date())
      setError(null)
    } catch (e: unknown) {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        setNeedsAuth(true)
        setAuthed(false)
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


  /** Lightweight: fetches only id/tool/timestamp/success — used on mount and periodic refresh.
   * Keeps the dashboard KPI count accurate without pulling stdout/stderr/params.
   */
  const fetchRunHistorySummary = useCallback(async () => {
    if (demo) return
    try {
      const r = await api.runHistorySummary()
      if (!r.success) return
      setRunHistory(prev => {
        const existingServerIds = new Set(prev.filter(e => e.source === 'server').map(e => e.serverId))
        const newEntries: RunHistoryEntry[] = (r.runs as RunHistorySummaryEntry[])
          .filter(e => !existingServerIds.has(e.id))
          .map(e => ({
            id: -(e.id),
            serverId: e.id,
            source: 'server' as const,
            tool: e.tool,
            params: {},
            ts: e.timestamp ? new Date(e.timestamp) : new Date(),
            result: {
              stdout: '',
              stderr: '',
              return_code: 0,
              success: e.success,
              timed_out: false,
              partial_results: false,
              execution_time: e.execution_time,
              timestamp: e.timestamp,
            },
          }))
        if (newEntries.length === 0) return prev
        const merged = [...prev, ...newEntries].sort((a, b) => b.ts.getTime() - a.ts.getTime())
        return merged
      })
    } catch { /* non-critical */ }
  }, [demo])

  /** Full fetch: includes stdout/stderr/params — called explicitly from the RunPage refresh button. */
  const fetchServerRunHistory = useCallback(async () => {
    if (demo) return
    try {
      const r = await api.runHistory()
      if (!r.success) return
      setRunHistory(prev => {
        // Replace all server entries with the full payload.
        const browserEntries = prev.filter(e => e.source !== 'server')
        const fullEntries: RunHistoryEntry[] = r.runs
          .filter((e: ApiRunHistoryEntry) => {
            // Skip server entries that match a local browser run (same tool, within 10s)
            const serverTs = e.timestamp ? new Date(e.timestamp).getTime() : 0
            return !browserEntries.some(local =>
              local.source === 'browser' &&
              local.tool === e.tool &&
              serverTs > 0 &&
              Math.abs(local.ts.getTime() - serverTs) < 10_000
            )
          })
          .map((e: ApiRunHistoryEntry) => ({
            id: -(e.id),
            serverId: e.id,
            source: 'server' as const,
            tool: e.tool,
            params: e.params,
            ts: e.timestamp ? new Date(e.timestamp) : (parseDateFromStdout(e.stdout ?? '') ?? new Date()),
            result: {
              stdout: e.stdout,
              stderr: e.stderr,
              return_code: e.return_code,
              success: e.success,
              timed_out: e.timed_out,
              partial_results: e.partial_results,
              execution_time: e.execution_time,
              timestamp: e.timestamp,
            },
          }))
        const merged = [...browserEntries, ...fullEntries].sort((a, b) => b.ts.getTime() - a.ts.getTime())
        return merged
      })
    } catch { /* non-critical */ }
  }, [demo])

  const clearServerRunHistory = useCallback(async () => {
    if (demo) {
      setRunHistory([])
      return
    }
    const r = await api.clearRunHistory()
    if (r.success) setRunHistory([])
  }, [demo])

  useEffect(() => {
    if (demo || !authed) return
    // Use the lightweight summary endpoint on mount — no stdout/stderr/params payload.
    // The full fetch is triggered explicitly from the RunPage refresh button.
    fetchRunHistorySummary().catch(() => {})
  }, [demo, authed, fetchRunHistorySummary])
  // Try without token first (skipped in demo)
  useEffect(() => {
    if (demo || hasToken()) return
    api.dashboard().then(h => {
      setHealth(h)
      setAuthed(true)
      setLoading(false)
    }).catch(e => {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        setNeedsAuth(true)
      } else {
        setAuthed(true)
      }
      setLoading(false)
    })
  }, [])

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

  // SSE log stream — only active in logs tab
  useEffect(() => {
    if (demo || page !== 'logs') return

    let es: EventSource | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let unmounted = false

    function connect() {
      if (unmounted) return
      es = api.logStream(150)
      sseRef.current = es

      es.onmessage = (e) => {
        setLogLines(prev => {
          const next = [...prev, e.data]
          return next.length > 500 ? next.slice(-500) : next
        })
      }

      es.onerror = () => {
        es?.close()
        es = null
        if (!unmounted) {
          // simple fixed 3 s reconnect — log stream is low-stakes and lazy
          reconnectTimer = setTimeout(connect, 3_000)
        }
      }
    }

    connect()

    return () => {
      unmounted = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      es?.close()
    }
  }, [demo, page])

  // Auto-scroll log to bottom
  useEffect(() => {
    if (page === 'logs' && logAutoScroll) logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logLines, page, logAutoScroll])

  if (needsAuth && !authed) {
    return <TokenGate onUnlocked={() => { setAuthed(true); setNeedsAuth(false) }} />
  }

  const toolsStatusWithParents = getToolsStatusWithParents(tools, health?.tools_status ?? {})

  return (
    <ToastProvider>
      <div className={demo ? 'layout layout--demo' : 'layout'}>
        <CommandPalette
          open={paletteOpen}
          onClose={() => setPaletteOpen(false)}
          setPage={setPage}
          tools={tools}
          onSelectTool={handleCommandSelectTool}
        />
        <ReportGenerationBubble />
        <ChatWidget
          llmAvailable={health?.llm_status?.available ?? false}
          currentPage={page}
          currentSessionId={activeSessionId}
        />
        {demo && (
          <div className="demo-banner">
            <FlaskConical size={13} />
            <span>Demo mode — all data is synthetic</span>
            <button onClick={() => { exitDemo(); window.location.href = window.location.pathname + window.location.hash }}>Exit demo</button>
          </div>
        )}

        <TopBar
          page={page}
          setPage={setPage}
          lastRefresh={lastRefresh}
          demo={demo}
          isStreaming={isStreaming}
          streamingError={streamingError}
          health={health}
          error={error}
          loading={loading}
          fetchAll={fetchAll}
          themeId={themeId}
          setThemeId={setThemeId}
          reduceTextureEffects={reduceTextureEffects}
          setReduceTextureEffects={setReduceTextureEffects}
          onOpenCommandPalette={openCommandPalette}
          onSignOut={() => { setAuthed(false); setNeedsAuth(true) }}
        />

        {showPaletteHint && (
          <div className="palette-hint-floating" role="status" aria-live="polite">
            <button className="palette-hint-main" onClick={openCommandPalette} title="Open command palette">
              <span className="palette-hint-title">Try Command Palette</span>
              <span className="palette-hint-kbd mono">Ctrl/Cmd + K</span>
            </button>
            <button className="palette-hint-close" onClick={dismissPaletteHint} title="Dismiss hint">x</button>
          </div>
        )}

        <MainContent
          page={page}
          demo={demo}
          tools={tools}
          health={health}
          toolsStatusWithParents={toolsStatusWithParents}
          runHistory={runHistory}
          setRunHistory={setRunHistory}
          fetchServerRunHistory={fetchServerRunHistory}
          clearServerRunHistory={clearServerRunHistory}
          commandToolRequest={commandToolRequest}
          onCommandToolHandled={() => setCommandToolRequest(null)}
          openSessionDetail={openSessionDetail}
          activeSessionId={activeSessionId}
          setPage={setPage}
          addBrowserRunEntry={addBrowserRunEntry}
          logLines={logLines}
          logAutoScroll={logAutoScroll}
          setLogAutoScroll={setLogAutoScroll}
          logLimit={logLimit}
          setLogLimit={setLogLimit}
          logEndRef={logEndRef}
          loading={loading}
          error={error}
          toolCategories={toolCategories}
          themeId={themeId}
          setThemeId={setThemeId}
          reduceTextureEffects={reduceTextureEffects}
          setReduceTextureEffects={setReduceTextureEffects}
          demoProcesses={demoProcesses}
          demoSessions={demoSessions}
          demoCpuHistory={demoCpuHistory}
        />
      </div>
    </ToastProvider>
  )
}
