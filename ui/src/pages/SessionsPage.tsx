import { useEffect, useRef, useState } from 'react'
import {
  RefreshCw, XCircle, Activity, Clock, CheckCircle,
  Layers, Target,
} from 'lucide-react'
import {
  api,
  type SessionsResponse,
  type SessionSummary,
  type AttackChainStep,
} from '../api'
import { StatCard } from '../components/StatCard'
import './SessionsPage.css'

interface SessionsPageProps {
  demoData?: { sessions: SessionsResponse }
  onOpenSession: (sessionId: string) => void
}

interface StartMode {
  key: 'comprehensive' | 'reconnaissance' | 'vulnerability_hunting' | 'osint'
  title: string
  description: string
  details: string
  modalDescription: string
  tools: string[]
  placeholder: string
}

const START_MODES: StartMode[] = [
  {
    key: 'comprehensive',
    title: 'Comprehensive Assessment',
    description: 'Balanced full-chain workflow from recon to vulnerability checks.',
    details: 'Best default for unknown targets.',
    modalDescription: 'Builds a broad, practical workflow that starts with target profiling and surface mapping, then moves into prioritized vulnerability validation. This is designed for cases where you want full context and a structured path from discovery to actionable findings.',
    tools: ['nmap', 'httpx', 'katana', 'nuclei', 'nikto', 'ffuf'],
    placeholder: 'Target URL/domain/IP (example.com)',
  },
  {
    key: 'reconnaissance',
    title: 'Reconnaissance',
    description: 'Discovery-first workflow for assets, endpoints, and technologies.',
    details: 'Use when mapping attack surface.',
    modalDescription: 'Focuses on enumeration and intelligence gathering with minimal intrusive testing. It maps hosts, services, paths, and technologies so you can decide where deeper testing should happen next.',
    tools: ['subfinder', 'amass', 'httpx', 'katana', 'waybackurls', 'gau'],
    placeholder: 'Scope target (example.com or 10.0.0.0/24)',
  },
  {
    key: 'vulnerability_hunting',
    title: 'Vulnerability Hunting',
    description: 'Vulnerability-focused chain prioritizing exploitable findings.',
    details: 'Use when recon is already known.',
    modalDescription: 'Runs targeted security checks against known attack surface to quickly identify high-value weaknesses. This mode biases toward validating likely vulnerabilities and producing results you can triage and act on fast.',
    tools: ['nuclei', 'sqlmap', 'dalfox', 'jaeles', 'nikto', 'wpscan'],
    placeholder: 'Web/API target (https://target.tld)',
  },
  {
    key: 'osint',
    title: 'OSINT Collection',
    description: 'Intelligence and external footprint gathering for a target.',
    details: 'Useful before active probing.',
    modalDescription: 'Collects passive intelligence from public sources to understand exposure before active scanning. This includes historical URLs, publicly indexed assets, and reconnaissance artifacts useful for planning follow-up testing.',
    tools: ['theharvester', 'subfinder', 'amass', 'gau', 'waybackurls'],
    placeholder: 'Domain or org target (target.tld)',
  },
]

function fmtTs(ts: number) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString('en-GB')
}

function normalizeStepsFromSession(s: SessionSummary): AttackChainStep[] {
  if (Array.isArray(s.workflow_steps) && s.workflow_steps.length > 0) {
    return s.workflow_steps
  }
  return s.tools_executed.map(tool => ({ tool, parameters: {} }))
}

function SessionCard({ s, onOpen }: { s: SessionSummary; onOpen: (sessionId: string) => void }) {
  const toolStatus = (s.metadata?.tool_status ?? {}) as Record<string, string>
  const lastRun = ((s.metadata?.last_run ?? null) as {
    tool?: string
    success?: boolean
    return_code?: number
    execution_time?: number
  } | null)
  const toolCount = normalizeStepsFromSession(s).length

  return (
    <div className="session-card session-card--compact registry-card--clickable" onClick={() => onOpen(s.session_id)}>
      <div className="session-card-header">
        <div className="session-target">
          <Target size={13} color="var(--blue)" />
          <span className="mono">{s.target}</span>
        </div>
        {s.status && (
          <span className={`session-status session-status--${s.status}`}>{s.status}</span>
        )}
      </div>

      <div className="session-card-meta">
        <span><Activity size={11} /> {s.total_findings} findings</span>
        <span><RefreshCw size={11} /> {s.iterations} iterations</span>
        <span><Clock size={11} /> {fmtTs(s.updated_at)}</span>
      </div>

      <div className="session-tools">
        {s.tools_executed.slice(0, 8).map(t => (
          <span
            key={t}
            className={`session-tool-chip mono session-tool-chip--${toolStatus[t] === 'success' ? 'success' : toolStatus[t] === 'failed' ? 'failed' : 'idle'}`}
          >
            {t}
          </span>
        ))}
        {s.tools_executed.length > 8 && (
          <span className="session-tool-chip session-tool-chip--more">+{s.tools_executed.length - 8}</span>
        )}
      </div>

      <div className="session-card-footer">
        <span className="session-id mono">{s.session_id}</span>
        <span className="session-open-hint">Open ({toolCount} tools)</span>
      </div>
      {lastRun?.tool && (
        <div className="session-last-run mono">
          last: {lastRun.tool} | {lastRun.success ? 'OK' : 'FAIL'} | exit {lastRun.return_code ?? 0} | {(lastRun.execution_time ?? 0).toFixed(2)}s
        </div>
      )}
    </div>
  )
}

export default function SessionsPage({ demoData, onOpenSession }: SessionsPageProps) {
  const [data, setData] = useState<SessionsResponse | null>(demoData?.sessions ?? null)
  const [creatingSession, setCreatingSession] = useState(false)
  const [createMsg, setCreateMsg] = useState<string | null>(null)
  const [startMode, setStartMode] = useState<StartMode | null>(null)
  const [modalTarget, setModalTarget] = useState('')
  const [modalNote, setModalNote] = useState('')
  const [modalError, setModalError] = useState<string | null>(null)
  const [loading, setLoading] = useState(!demoData)
  const [error, setError] = useState<string | null>(null)
  const [showHandoverHelp, setShowHandoverHelp] = useState(false)
  const [streamStatus, setStreamStatus] = useState<'streaming' | 'polling' | 'error'>(demoData ? 'polling' : 'streaming')
  const streamRef = useRef<EventSource | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)

  useEffect(() => {
    if (demoData) return
    Promise.all([api.sessions(), api.tools()])
      .then(([sessionsData]) => {
        setData(sessionsData)
        setError(null)
      })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [demoData])

  function fetchSessions(silent = false) {
    if (demoData) return
    if (!silent) setLoading(true)
    api.sessions()
      .then(sessionsData => {
        setData(sessionsData)
        setError(null)
      })
      .catch(e => setError(String(e)))
      .finally(() => {
        if (!silent) setLoading(false)
      })
  }

  function refresh(silent = false) {
    if (demoData) return
    fetchSessions(silent)
  }

  useEffect(() => {
    if (demoData) return

    let source: EventSource | null = null
    let unmounted = false

    function cleanupStream() {
      if (source) source.close()
      source = null
      streamRef.current = null
    }
    function cleanupPoll() {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
    function cleanupReconnect() {
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current)
        reconnectRef.current = null
      }
    }
    function startPolling() {
      cleanupPoll()
      setStreamStatus('polling')
      refresh(true)
      pollRef.current = setInterval(() => refresh(true), 5000)
    }
    function scheduleReconnect(connectFn: () => void) {
      cleanupReconnect()
      const attempt = reconnectAttemptsRef.current + 1
      reconnectAttemptsRef.current = attempt
      const delayMs = Math.min(30000, 1000 * (2 ** Math.max(0, attempt - 1)))
      reconnectRef.current = setTimeout(() => {
        if (unmounted) return
        connectFn()
      }, delayMs)
    }

    function connectStream() {
      cleanupStream()
      try {
        source = api.sessionsStream()
        streamRef.current = source
        source.onopen = () => {
          reconnectAttemptsRef.current = 0
          cleanupReconnect()
          cleanupPoll()
          setStreamStatus('streaming')
        }
        source.onmessage = e => {
          try {
            const sessionsData = JSON.parse(e.data) as SessionsResponse
            if (sessionsData?.success) {
              setData(sessionsData)
              setError(null)
              setLoading(false)
            }
          } catch {
            setError('Session stream parse error')
          }
        }
        source.onerror = () => {
          if (unmounted) return
          setStreamStatus('error')
          cleanupStream()
          startPolling()
          scheduleReconnect(connectStream)
        }
      } catch {
        if (unmounted) return
        setStreamStatus('error')
        startPolling()
        scheduleReconnect(connectStream)
      }
    }

    connectStream()

    return () => {
      unmounted = true
      cleanupStream()
      cleanupPoll()
      cleanupReconnect()
    }
  }, [demoData])

  function openStartModal(mode: StartMode) {
    setStartMode(mode)
    setModalTarget('')
    setModalNote('')
    setModalError(null)
  }

  function closeStartModal() {
    setStartMode(null)
    setModalError(null)
  }

  async function createSessionFromTarget(mode: StartMode, targetValue: string, noteValue: string) {
    if (!targetValue.trim()) {
      setModalError('Target is required')
      return
    }

    setCreateMsg(null)
    setModalError(null)
    setCreatingSession(true)
    try {
      const target = targetValue.trim()
      const chain = await api.createAttackChain(target, mode.key)
      const sessionRes = await api.createSession({
        target,
        workflow_steps: chain.attack_chain.steps,
        source: 'web',
        objective: mode.key,
        session_id: chain.session_id,
        metadata: { origin: 'ui/sessions/create', mode: mode.key, note: noteValue },
      })
      const sid = sessionRes.session.session_id
      setCreateMsg(`Session created: ${sid} (${chain.attack_chain.steps.length} tool calls ready).`)
      closeStartModal()
      refresh()
    } catch (e) {
      const msg = String(e)
      setModalError(msg)
      setCreateMsg(msg)
    } finally {
      setCreatingSession(false)
    }
  }

  if (loading) return (
    <div className="loading-state">
      <RefreshCw size={20} className="spin" color="var(--green)" />
      <p>Loading sessions…</p>
    </div>
  )
  if (error) return (
    <div className="error-banner"><XCircle size={16} /> {error}</div>
  )

  const rawActive = data?.active ?? []
  const active = rawActive.filter(s => (s.status ?? 'active') !== 'completed')
  const completed = [
    ...(data?.completed ?? []),
    ...rawActive.filter(s => (s.status ?? 'active') === 'completed'),
  ].filter((s, idx, arr) => arr.findIndex(x => x.session_id === s.session_id) === idx)
  const allFindings = [...active, ...completed].reduce((sum, s) => sum + s.total_findings, 0)
  const uniqueTargets = new Set([...active, ...completed].map(s => s.target)).size

  return (
    <div className="page-content">
      <div className="kpi-row">
        <StatCard
          icon={<Layers size={20} />}
          label="Active Sessions"
          value={active.length}
          sub="in progress"
          accent={active.length > 0 ? 'var(--green)' : 'var(--text-dim)'}
        />
        <StatCard icon={<CheckCircle size={20} />} label="Completed" value={completed.length} sub="archived" accent="var(--blue)" />
        <StatCard
          icon={<Activity size={20} />}
          label="Total Findings"
          value={allFindings}
          sub="across all sessions"
          accent="var(--amber)"
        />
        <StatCard
          icon={<Target size={20} />}
          label="Unique Targets"
          value={uniqueTargets}
          sub="scanned"
          accent="var(--purple)"
        />
      </div>

      <section className="section">
        <div className="section-header">
          <h3>Start Session</h3>
          <span className="section-meta">Choose a workflow type, then provide target details.</span>
        </div>
        <div className="registry-grid registry-grid--wide start-mode-grid">
          {START_MODES.map(mode => (
            <div key={mode.key} className="registry-card registry-card--clickable start-mode-card" onClick={() => openStartModal(mode)}>
              <div className="registry-card-top">
                <span className="registry-name">{mode.title}</span>
                <span className="registry-cat">{mode.key.replace(/_/g, ' ')}</span>
              </div>
              <p className="registry-desc">{mode.description}</p>
              <p className="start-mode-detail">{mode.details}</p>
            </div>
          ))}
        </div>
        {createMsg && <p className="section-meta">{createMsg}</p>}
      </section>

      {startMode && (
        <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) closeStartModal() }}>
          <div className="modal">
            <div className="modal-header">
              <div className="modal-title-row">
                <span className="modal-name">Start {startMode.title}</span>
              </div>
              <button className="modal-close" onClick={closeStartModal}><XCircle size={18} /></button>
            </div>
            <div className="modal-body">
              <p className="modal-desc">{startMode.modalDescription}</p>
              <div className="modal-section">
                <span className="modal-label">Typical Tooling</span>
                <div className="modal-params">
                  {startMode.tools.map(tool => (
                    <span key={tool} className="modal-param mono">{tool}</span>
                  ))}
                </div>
              </div>
              <div className="session-start-form">
                <label className="mono" htmlFor="session-target-input">Target *</label>
                <input
                  id="session-target-input"
                  className="search-input mono"
                  value={modalTarget}
                  onChange={e => setModalTarget(e.target.value)}
                  placeholder={startMode.placeholder}
                />
                <label className="mono" htmlFor="session-note-input">Note (optional)</label>
                <textarea
                  id="session-note-input"
                  className="session-step-params mono"
                  rows={3}
                  value={modalNote}
                  onChange={e => setModalNote(e.target.value)}
                  placeholder="Context for this run"
                />
                {modalError && <div className="run-error">{modalError}</div>}
                <div className="session-start-actions">
                  <button className="session-action-btn" onClick={closeStartModal}>Cancel</button>
                  <button
                    className="session-run-btn"
                    onClick={() => createSessionFromTarget(startMode, modalTarget, modalNote)}
                    disabled={creatingSession}
                  >
                    {creatingSession ? <RefreshCw size={13} className="spin" /> : <Target size={13} />}
                    {creatingSession ? 'Starting…' : 'Start Session'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <section className="section">
        <div className="section-header">
          <h3>Active Sessions <span className="badge">{active.length}</span></h3>
          <div className="sessions-header-actions">
            <button className="session-help-btn" onClick={() => setShowHandoverHelp(v => !v)}>
              {showHandoverHelp ? 'Hide handover help' : 'Handover help'}
            </button>
            <span className={`sessions-stream-status sessions-stream-status--${streamStatus}`}>
              {streamStatus === 'streaming' ? 'Live' : streamStatus === 'polling' ? 'Polling' : 'Offline'}
            </span>
            <button className="icon-btn" onClick={() => refresh()} title="Refresh">
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>
        {showHandoverHelp && (
          <div className="session-help-box">
            <p><strong>Web handover:</strong> open a session and click <span className="mono">Handover to LLM</span>.</p>
            <p><strong>MCP handover:</strong> call <span className="mono">handover_session("&lt;session_id&gt;", "optional note")</span>.</p>
            <p><strong>Tip:</strong> update target/step parameters before handover so the LLM gets the latest context.</p>
          </div>
        )}
        {active.length === 0 ? (
          <div className="tasks-empty">
            <Layers size={28} color="var(--text-dim)" />
            <p>No active sessions. Start a session from target to run tools manually.</p>
          </div>
        ) : (
          <div className="sessions-grid">
            {active.map(s => <SessionCard key={s.session_id} s={s} onOpen={onOpenSession} />)}
          </div>
        )}
      </section>

      <section className="section">
        <div className="section-header">
          <h3>Completed Sessions <span className="badge">{completed.length}</span></h3>
        </div>
        {completed.length === 0 ? (
          <p className="empty-state">No completed sessions yet.</p>
        ) : (
          <div className="sessions-grid">
            {completed.map(s => <SessionCard key={s.session_id} s={s} onOpen={onOpenSession} />)}
          </div>
        )}
      </section>
    </div>
  )
}
