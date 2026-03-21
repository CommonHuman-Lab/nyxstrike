import { useState, useEffect, useCallback, useRef } from 'react'
import faviconUrl from './favicon-16x16.png'
import {
  Clock, RefreshCw, Lock, Github,
  LayoutDashboard, Terminal, Play,
  Settings as SettingsIcon, HelpCircle,
  ListTodo, Wrench, FileText, Layers,
} from 'lucide-react'
import {
  api, clearToken, hasToken,
  type WebDashboardResponse, type Tool,
  type RunHistoryEntry as ApiRunHistoryEntry,
} from './api'
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
  const [authed, setAuthed] = useState(hasToken())
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

  const [health, setHealth] = useState<WebDashboardResponse | null>(null)
  const [tools, setTools] = useState<Tool[]>([])
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [runHistory, setRunHistory] = useState<RunHistoryEntry[]>(() => {
    try {
      const raw = localStorage.getItem('hexstrike_run_history')
      if (!raw) return []
      const parsed = JSON.parse(raw) as RunHistoryEntry[]
      return parsed.map(e => ({ ...e, ts: new Date(e.ts as unknown as string) }))
    } catch { return [] }
  })
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashCacheSize, setDashCacheSize] = useState<number | null>(null)
  const [dashCacheTtl, setDashCacheTtl] = useState<number | null>(null)
  const [logLines, setLogLines] = useState<string[]>([])
  const [logAutoScroll, setLogAutoScroll] = useState(true)
  const [logLimit, setLogLimit] = useState(500)
  const logEndRef = useRef<HTMLDivElement>(null)
  const sseRef = useRef<EventSource | null>(null)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const h = await api.dashboard()
      setHealth(h)
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
    try {
      const t = await api.tools()
      setTools(t.tools)
    } catch { /* non-critical */ }
  }, [])

  const fetchDashSettings = useCallback(async () => {
    try {
      const r = await api.getSettings()
      setDashCacheSize(r.settings.runtime.cache_size)
      setDashCacheTtl(r.settings.runtime.cache_ttl)
    } catch { /* non-critical */ }
  }, [])

  const fetchServerRunHistory = useCallback(async () => {
    try {
      const r = await api.runHistory()
      if (!r.success) return
      setRunHistory(prev => {
        const existingServerIds = new Set(prev.filter(e => e.source === 'server').map(e => e.serverId))
        const newEntries: RunHistoryEntry[] = r.runs
          .filter((e: ApiRunHistoryEntry) => !existingServerIds.has(e.id))
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

  // Persist run history to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem('hexstrike_run_history', JSON.stringify(runHistory.slice(0, 200)))
    } catch { /* quota exceeded — ignore */ }
  }, [runHistory])

  useEffect(() => {
    if (!authed) return
    setLoading(true)
    fetchAll()
    fetchTools()
    fetchDashSettings()
    fetchServerRunHistory()
    timerRef.current = setInterval(fetchAll, POLL_MS)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [authed, fetchAll, fetchTools, fetchDashSettings])

  // Try without token first
  useEffect(() => {
    if (hasToken()) return
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

  // SSE log stream
  useEffect(() => {
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
    <div className="layout">
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
        {page === 'tasks' && <TasksPage />}
        {page === 'tools' && <ToolsPage tools={tools} toolsStatus={health?.tools_status ?? {}} />}
        {page === 'reports' && <ReportsPage runHistory={runHistory} />}
        {page === 'sessions' && <SessionsPage />}
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
                dashCacheTtl={dashCacheTtl}
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
