import { useState, useEffect, useCallback, useRef } from 'react'
import faviconUrl from './favicon-16x16.png'
import {
  Clock, RefreshCw, Lock, Github,
  LayoutDashboard, Terminal, Play,
  Settings as SettingsIcon, HelpCircle,
  ListTodo, Wrench, FileText, Layers,
  FlaskConical,
} from 'lucide-react'
import {
  api, clearToken, hasToken,
  type WebDashboardResponse, type Tool,
  type RunHistoryEntry as ApiRunHistoryEntry,
} from './api'
import {
  isDemoMode, exitDemo,
  DEMO_HEALTH, DEMO_TOOLS, DEMO_RUN_HISTORY, DEMO_LOG_LINES,
  DEMO_SESSIONS, DEMO_PROCESSES,
  demoCpuMemHistory,
} from './demo'
import { TokenGate } from './components/TokenGate'
import { DashboardPage } from './pages/DashboardPage'
import { RunPage } from './pages/RunPage'
import LogsPage from './pages/LogsPage'
import SettingsPage from './pages/SettingsPage'
import HelpPage from './pages/HelpPage'
import TasksPage from './pages/TasksPage'
import ToolsPage from './pages/ToolsPage'
import ReportsPage from './pages/ReportsPage'
import SessionsPage from './pages/SessionsPage'
import type { RunHistoryEntry, HistoryPoint } from './types'
import './App.css'

// ─── Routing ─────────────────────────────────────────────────────────────────

const POLL_MS = 10_000
type Page = 'dashboard' | 'settings' | 'help' | 'logs' | 'run' | 'tasks' | 'tools' | 'reports' | 'sessions'

const VALID_PAGES = new Set<Page>(['dashboard', 'settings', 'help', 'logs', 'run', 'tasks', 'tools', 'reports', 'sessions'])

function pageFromHash(): Page {
  const hash = window.location.hash.replace(/^#\/?/, '')
  return VALID_PAGES.has(hash as Page) ? (hash as Page) : 'dashboard'
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [demo] = useState(isDemoMode)
  const [authed, setAuthed] = useState(demo || hasToken())
  const [needsAuth, setNeedsAuth] = useState(false)
  const [page, setPageState] = useState<Page>(pageFromHash)

  function setPage(p: Page) {
    window.location.hash = p === 'dashboard' ? '' : `/${p}`
    setPageState(p)
  }

  // Keep state in sync if the user presses Back/Forward
  useEffect(() => {
    function onHashChange() { setPageState(pageFromHash()) }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const [health, setHealth] = useState<WebDashboardResponse | null>(demo ? DEMO_HEALTH : null)
  const [tools, setTools] = useState<Tool[]>(demo ? DEMO_TOOLS : [])
  const [history, setHistory] = useState<HistoryPoint[]>(demo ? demoCpuMemHistory() : [])
  useEffect(() => {
    if (demo) return
    api.tools().then(r => setTools(r.tools)).catch(() => {})
  }, [demo])
  const [runHistory, setRunHistory] = useState<RunHistoryEntry[]>(() => {
    if (demo) return DEMO_RUN_HISTORY
    try {
      const raw = localStorage.getItem('hexstrike_run_history')
      if (!raw) return []
      const parsed = JSON.parse(raw) as RunHistoryEntry[]
      return parsed.map(e => ({ ...e, ts: new Date(e.ts as unknown as string) }))
    } catch { return [] }
  })
  const [lastRefresh, setLastRefresh] = useState<Date | null>(demo ? new Date() : null)
  const [loading, setLoading] = useState(!demo)
  const [error, setError] = useState<string | null>(null)
  const [logLines, setLogLines] = useState<string[]>(demo ? DEMO_LOG_LINES : [])
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

  const fetchAll = useCallback(async () => {
    if (demo) return
    try {
      const h = await api.dashboard()
      setHealth(h)
      setHistory(prev => {
        const next = [
          ...prev.slice(-29),
          { t: Date.now(), cpu: h.resources.cpu_percent, mem: h.resources.memory_percent, network_bytes_sent: h.resources.network_bytes_sent, network_bytes_recv: h.resources.network_bytes_recv },
        ]
        return next
      })
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


  const fetchServerRunHistory = useCallback(async () => {
    if (demo) return
    try {
      const r = await api.runHistory()
      if (!r.success) return
      setRunHistory(prev => {
        const existingServerIds = new Set(prev.filter(e => e.source === 'server').map(e => e.serverId))
        const newEntries: RunHistoryEntry[] = r.runs
          .filter((e: ApiRunHistoryEntry) => {
            if (existingServerIds.has(e.id)) return false
            // Skip server entries that match a local browser run (same tool, within 10s)
            const serverTs = e.timestamp ? new Date(e.timestamp).getTime() : 0
            return !prev.some(local =>
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
            ts: e.timestamp ? new Date(e.timestamp) : new Date(),
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
        if (newEntries.length === 0) return prev
        const merged = [...prev, ...newEntries].sort((a, b) => b.ts.getTime() - a.ts.getTime())
        return merged
      })
    } catch { /* non-critical */ }
  }, [])

  // Persist run history to localStorage whenever it changes (not in demo mode)
  useEffect(() => {
    if (demo) return
    try {
      localStorage.setItem('hexstrike_run_history', JSON.stringify(runHistory.slice(0, 200)))
    } catch { /* quota exceeded — ignore */ }
  }, [demo, runHistory])

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
        setHistory(prev => {
          const next = [
            ...prev.slice(-29),
            { t: Date.now(), cpu: h.resources.cpu_percent, mem: h.resources.memory_percent, network_bytes_sent: h.resources.network_bytes_sent, network_bytes_recv: h.resources.network_bytes_recv },
          ]
          return next
        })
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
    const es = api.logStream(150)
    sseRef.current = es
    es.onmessage = (e) => {
      setLogLines(prev => {
        const next = [...prev, e.data]
        return next.length > 500 ? next.slice(-500) : next
      })
    }
    return () => { es.close() }
  }, [demo, page])

  // Auto-scroll log to bottom
  useEffect(() => {
    if (page === 'logs' && logAutoScroll) logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logLines, page, logAutoScroll])

  if (needsAuth && !authed) {
    return <TokenGate onUnlocked={() => { setAuthed(true); setNeedsAuth(false) }} />
  }

  function getToolsStatusWithParents(
    tools: Tool[],
    toolsStatus: Record<string, boolean>
  ): Record<string, boolean> {
    const result = { ...toolsStatus }
    for (const tool of tools) {
      if (tool.parent_tool && toolsStatus[tool.parent_tool]) {
        // Add tool if not already present
        if (!(tool.name in result)) {
          result[tool.name] = true
        }
      }
    }
    return result
  }

  const toolsStatusWithParents = getToolsStatusWithParents(tools, health?.tools_status ?? {})

  return (
    <div className={demo ? 'layout layout--demo' : 'layout'}>
      {/* ── Demo banner ── */}
      {demo && (
        <div className="demo-banner">
          <FlaskConical size={13} />
          <span>Demo mode — all data is synthetic</span>
          <button onClick={() => { exitDemo(); window.location.href = window.location.pathname + window.location.hash }}>Exit demo</button>
        </div>
      )}
      {/* ── Top Bar ── */}
      <header className="topbar">
        <div className="topbar-brand">
          <img src={faviconUrl} width={18} height={18} alt="" />
          <span className="brand-text">HexStrike Community Edition</span>
          <span className="brand-version mono">{health?.version ?? '…'}</span>
        </div>

        {/* ── Nav Tabs ── */}
        <nav className="topbar-nav">
          <button className={`nav-tab ${page === 'dashboard' ? 'active' : ''}`} onClick={() => setPage('dashboard')}>
            <LayoutDashboard size={13} /> Dashboard
          </button>
          <button className={`nav-tab ${page === 'run' ? 'active' : ''}`} onClick={() => setPage('run')}>
            <Play size={13} /> Run
          </button>
          <button className={`nav-tab ${page === 'logs' ? 'active' : ''}`} onClick={() => setPage('logs')}>
            <Terminal size={13} /> Logs
          </button>
          <button className={`nav-tab ${page === 'settings' ? 'active' : ''}`} onClick={() => setPage('settings')}>
            <SettingsIcon size={13} /> Settings
          </button>
          <button className={`nav-tab ${page === 'help' ? 'active' : ''}`} onClick={() => setPage('help')}>
            <HelpCircle size={13} /> Help
          </button>
          <button className={`nav-tab ${page === 'tasks' ? 'active' : ''}`} onClick={() => setPage('tasks')}>
            <ListTodo size={13} /> Tasks
          </button>
          <button className={`nav-tab ${page === 'tools' ? 'active' : ''}`} onClick={() => setPage('tools')}>
            <Wrench size={13} /> Tools
          </button>
          <button className={`nav-tab ${page === 'reports' ? 'active' : ''}`} onClick={() => setPage('reports')}>
            <FileText size={13} /> Reports
          </button>
          <button className={`nav-tab ${page === 'sessions' ? 'active' : ''}`} onClick={() => setPage('sessions')}>
            <Layers size={13} /> Sessions
          </button>
        </nav>

        <div className="topbar-right">
          {lastRefresh && (
            <span className="topbar-meta">
              <Clock size={12} /> {lastRefresh.toLocaleTimeString('en-GB')}
            </span>
          )}
          {/* Dashboard stream status indicator */}
          {demo ? null : (
            <>
              <div
                className={`status-dot ${
                  isStreaming
                    ? 'online'
                    : streamingError
                      ? 'error'
                      : 'loading'
                }`}
                title={isStreaming ? 'Live (streaming)' : streamingError ? streamingError : 'Idle'}
                style={{ marginRight: 4 }}
              />
              <span className="status-label" style={{ fontSize: 12 }}>
                {isStreaming ? 'Live' : streamingError ? 'Polling' : 'N/A'}
              </span>
            </>
          )}
          <div className={`status-dot ${health?.status === 'healthy' ? 'online' : error ? 'error' : 'loading'}`} />
          <span className="status-label">{health?.status ? health.status.charAt(0).toUpperCase() + health.status.slice(1) : (loading ? 'connecting…' : error ?? 'unknown')}</span>
          {!isStreaming && (
            <button className="icon-btn" onClick={fetchAll} title="Refresh now">
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
            </button>
          )}
          <a
            className="icon-btn"
            href="https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition"
            target="_blank"
            rel="noreferrer"
            title="View on GitHub"
          >
            <Github size={14} />
          </a>
          <a
            className="icon-btn"
            href="https://discord.gg/sZZVmaJACd"
            target="_blank"
            rel="noreferrer"
            title="Join Discord community"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 245 240" width={14} height={14}>
              <g>
                <path d="M216.856339,16.5966031 C200.285002,8.84328665 182.566144,3.2084988 164.041564,0 C161.766523,4.11318106 159.108624,9.64549908 157.276099,14.0464379 C137.583995,11.0849896 118.072967,11.0849896 98.7430163,14.0464379 C96.9108417,9.64549908 94.1925838,4.11318106 91.8971895,0 C73.3526068,3.2084988 55.6133949,8.86399117 39.0420583,16.6376612 C5.61752293,67.146514 -3.4433191,116.400813 1.08711069,164.955721 C23.2560196,181.510915 44.7403634,191.567697 65.8621325,198.148576 C71.0772151,190.971126 75.7283628,183.341335 79.7352139,175.300261 C72.104019,172.400575 64.7949724,168.822202 57.8887866,164.667963 C59.7209612,163.310589 61.5131304,161.891452 63.2445898,160.431257 C105.36741,180.133187 151.134928,180.133187 192.754523,160.431257 C194.506336,161.891452 196.298154,163.310589 198.110326,164.667963 C191.183787,168.842556 183.854737,172.420929 176.223542,175.320965 C180.230393,183.341335 184.861538,190.991831 190.096624,198.16893 C211.238746,191.588051 232.743023,181.531619 254.911949,164.955721 C260.227747,108.668201 245.831087,59.8662432 216.856339,16.5966031 Z M85.4738752,135.09489 C72.8290281,135.09489 62.4592217,123.290155 62.4592217,108.914901 C62.4592217,94.5396472 72.607595,82.7145587 85.4738752,82.7145587 C98.3405064,82.7145587 108.709962,94.5189427 108.488529,108.914901 C108.508531,123.290155 98.3405064,135.09489 85.4738752,135.09489 Z M170.525237,135.09489 C157.88039,135.09489 147.510584,123.290155 147.510584,108.914901 C147.510584,94.5396472 157.658606,82.7145587 170.525237,82.7145587 C183.391518,82.7145587 193.761324,94.5189427 193.539891,108.914901 C193.539891,123.290155 183.391518,135.09489 170.525237,135.09489 Z" fill="#5865F2" fill-rule="nonzero"></path>
              </g>
            </svg>
          </a>
          {hasToken() && (
            <button className="icon-btn" onClick={() => { clearToken(); setAuthed(false); setNeedsAuth(true) }} title="Sign out">
              <Lock size={14} />
            </button>
          )}
        </div>
      </header>

      <main className={`main${page === 'run' ? ' main--flush' : ''}`}>
        {page === 'settings' && <SettingsPage />}
        {page === 'help' && <HelpPage />}
        {page === 'run' && (
          <RunPage
            tools={tools}
            toolsStatus={toolsStatusWithParents ?? {}}
            runHistory={runHistory}
            setRunHistory={setRunHistory}
            onRefresh={fetchServerRunHistory}
          />
        )}
        {page === 'tasks' && <TasksPage demoData={demo ? { processes: DEMO_PROCESSES } : undefined} />}
        {page === 'tools' && health && (
          <ToolsPage health={health} tools={tools} toolsStatus={toolsStatusWithParents ?? {}} />
        )}
        {page === 'reports' && <ReportsPage runHistory={runHistory} />}
        {page === 'sessions' && <SessionsPage demoData={demo ? { sessions: DEMO_SESSIONS } : undefined} />}
        {page === 'logs' && (
          <LogsPage
            logLines={logLines}
            logAutoScroll={logAutoScroll}
            setLogAutoScroll={setLogAutoScroll}
            logLimit={logLimit}
            setLogLimit={setLogLimit}
            logEndRef={logEndRef}
          />
        )}
        {page === 'dashboard' && (
          <>
            {loading && !health && (
              <div className="loading-state">
                <RefreshCw size={24} className="spin" color="var(--green)" />
                <p>Connecting to server…</p>
              </div>
            )}
            {error && !health && (
              <div className="error-banner">
                {error} — is the server running on port 8888?
              </div>
            )}
            {health && (
              <DashboardPage
                health={health}
                tools={tools}
                history={history}
                runHistory={runHistory}
                loading={loading}
                error={error}
                toolCategories={toolCategories}
              />
            )}
          </>
        )}
      </main>
    </div>
  )
}