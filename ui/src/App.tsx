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
  const [dashCacheSize, setDashCacheSize] = useState<number | null>(demo ? 512 : null)
  const [dashCacheHits, setDashCacheHits] = useState<number | null>(demo ? 0 : null)
  const [logLines, setLogLines] = useState<string[]>(demo ? DEMO_LOG_LINES : [])
  const [logAutoScroll, setLogAutoScroll] = useState(true)
  const [logLimit, setLogLimit] = useState(500)
  const logEndRef = useRef<HTMLDivElement>(null)
  const sseRef = useRef<EventSource | null>(null)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAll = useCallback(async () => {
    if (demo) return
    try {
      const h = await api.dashboard()
      setHealth(h)
      setDashCacheSize(h.cache_stats?.size ?? null)
      setDashCacheHits(h.cache_stats?.hits ?? null)
      setHistory(prev => {
        const next = [
          ...prev.slice(-29),
          { t: Date.now(), cpu: h.resources.cpu_percent, mem: h.resources.memory_percent },
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

  const fetchTools = useCallback(async () => {
    if (demo) return
    try { const t = await api.tools(); setTools(t.tools) } catch { /* non-critical */ }
  }, [demo])

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

  useEffect(() => {
    if (demo || !authed) return
    setLoading(true)
    fetchAll()
    fetchTools()
    fetchServerRunHistory()
    timerRef.current = setInterval(fetchAll, POLL_MS)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [demo, authed, fetchAll, fetchTools])

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

  // SSE log stream (skipped in demo — logs pre-populated from demo data)
  useEffect(() => {
    if (demo) return
    const es = api.logStream(150)
    sseRef.current = es
    es.onmessage = (e) => {
      setLogLines(prev => {
        const next = [...prev, e.data]
        return next.length > 500 ? next.slice(-500) : next
      })
    }
    return () => { es.close() }
  }, [])

  // Auto-scroll log to bottom
  useEffect(() => {
    if (page === 'logs' && logAutoScroll) logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logLines, page, logAutoScroll])

  if (needsAuth && !authed) {
    return <TokenGate onUnlocked={() => { setAuthed(true); setNeedsAuth(false) }} />
  }

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
          <div className={`status-dot ${health?.status === 'healthy' ? 'online' : error ? 'error' : 'loading'}`} />
          <span className="status-label">{health?.status ? health.status.charAt(0).toUpperCase() + health.status.slice(1) : (loading ? 'connecting…' : error ?? 'unknown')}</span>
          <button className="icon-btn" onClick={fetchAll} title="Refresh now">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
          </button>
          <a
            className="icon-btn"
            href="https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition"
            target="_blank"
            rel="noreferrer"
            title="View on GitHub"
          >
            <Github size={14} />
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
            toolsStatus={health?.tools_status ?? {}}
            runHistory={runHistory}
            setRunHistory={setRunHistory}
            onRefresh={fetchServerRunHistory}
          />
        )}
        {page === 'tasks' && <TasksPage demoData={demo ? { processes: DEMO_PROCESSES } : undefined} />}
        {page === 'tools' && <ToolsPage tools={tools} toolsStatus={health?.tools_status ?? {}} />}
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
                dashCacheSize={dashCacheSize}
                dashCacheHits={dashCacheHits}
                runHistory={runHistory}
                loading={loading}
                error={error}
              />
            )}
          </>
        )}
      </main>
    </div>
  )
}
