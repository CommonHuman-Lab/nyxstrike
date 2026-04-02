import { useState, useEffect, useRef } from 'react'
import {
  RefreshCw, XCircle, Activity, Clock, CheckCircle,
  Layers, Target, Play, Bot, ChevronDown, ChevronUp,
} from 'lucide-react'
import {
  api,
  type SessionsResponse,
  type SessionSummary,
  type AttackChainStep,
  type Tool,
  type ToolExecResponse,
} from '../api'
import { StatCard } from '../components/StatCard'
import './SessionsPage.css'

interface SessionsPageProps {
  demoData?: { sessions: SessionsResponse }
}

interface StartMode {
  key: 'comprehensive' | 'reconnaissance' | 'vulnerability_hunting' | 'osint'
  title: string
  description: string
  details: string
  icon: 'shield' | 'radar' | 'bug' | 'search'
  placeholder: string
}

const START_MODES: StartMode[] = [
  {
    key: 'comprehensive',
    title: 'Comprehensive Assessment',
    description: 'Balanced full-chain workflow from recon to vulnerability checks.',
    details: 'Best default for unknown targets.',
    icon: 'shield',
    placeholder: 'Target URL/domain/IP (example.com)',
  },
  {
    key: 'reconnaissance',
    title: 'Reconnaissance',
    description: 'Discovery-first workflow for assets, endpoints, and technologies.',
    details: 'Use when mapping attack surface.',
    icon: 'radar',
    placeholder: 'Scope target (example.com or 10.0.0.0/24)',
  },
  {
    key: 'vulnerability_hunting',
    title: 'Vulnerability Hunting',
    description: 'Vulnerability-focused chain prioritizing exploitable findings.',
    details: 'Use when recon is already known.',
    icon: 'bug',
    placeholder: 'Web/API target (https://target.tld)',
  },
  {
    key: 'osint',
    title: 'OSINT Collection',
    description: 'Intelligence and external footprint gathering for a target.',
    details: 'Useful before active probing.',
    icon: 'search',
    placeholder: 'Domain or org target (target.tld)',
  },
]

function fmtTs(ts: number) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString('en-GB')
}

function inferTargetValue(paramName: string, target: string): string | undefined {
  const k = paramName.toLowerCase()
  if (k === 'target' || k === 'host' || k === 'query') return target
  if (k === 'url' || k === 'endpoint') {
    if (target.startsWith('http://') || target.startsWith('https://')) return target
    return `https://${target}`
  }
  if (k === 'domain') {
    return target.replace(/^https?:\/\//, '').replace(/\/.*/, '')
  }
  return undefined
}

function normalizeStepsFromSession(s: SessionSummary): AttackChainStep[] {
  if (Array.isArray(s.workflow_steps) && s.workflow_steps.length > 0) {
    return s.workflow_steps
  }
  return s.tools_executed.map(tool => ({ tool, parameters: {} }))
}

interface SessionCardProps {
  s: SessionSummary
  expanded: boolean
  sessionTargetValue: string
  onToggleExpand: () => void
  onTargetChange: (v: string) => void
  steps: AttackChainStep[]
  toolMap: Record<string, Tool>
  stepDrafts: Record<string, string>
  runningStepKey: string | null
  stepResults: Record<string, { result?: ToolExecResponse; error?: string }>
  onStepDraftChange: (stepKey: string, next: string) => void
  onRunStep: (session: SessionSummary, step: AttackChainStep, index: number) => void
  handoffPending: boolean
  handoffResult: string | null
  onHandover: () => void
}

function SessionCard({
  s,
  expanded,
  sessionTargetValue,
  onToggleExpand,
  onTargetChange,
  steps,
  toolMap,
  stepDrafts,
  runningStepKey,
  stepResults,
  onStepDraftChange,
  onRunStep,
  handoffPending,
  handoffResult,
  onHandover,
}: SessionCardProps) {
  return (
    <div className="session-card">
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

      {s.tools_executed.length > 0 && (
        <div className="session-tools">
          {s.tools_executed.slice(0, 8).map(t => (
            <span key={t} className="session-tool-chip mono">{t}</span>
          ))}
          {s.tools_executed.length > 8 && (
            <span className="session-tool-chip session-tool-chip--more">+{s.tools_executed.length - 8}</span>
          )}
        </div>
      )}

      <div className="session-id mono">{s.session_id}</div>

      <div className="session-actions">
        <button className="session-action-btn" onClick={onToggleExpand}>
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Collapse' : 'Expand'}
        </button>
        <button className="session-action-btn" onClick={onHandover} disabled={handoffPending}>
          <Bot size={12} />
          {handoffPending ? 'Handing over…' : 'Handover to LLM'}
        </button>
      </div>

      {handoffResult && <div className="session-handoff-note">{handoffResult}</div>}

      {expanded && (
        <div className="session-expanded">
          <div className="session-target-override">
            <label className="mono">Target</label>
            <input
              className="search-input mono"
              value={sessionTargetValue}
              onChange={e => onTargetChange(e.target.value)}
              placeholder="Target to run this session against"
            />
          </div>

          <div className="session-step-list">
            {steps.length === 0 ? (
              <p className="empty-state">No tool calls in this session.</p>
            ) : (
              steps.map((step, idx) => {
                const stepKey = `${s.session_id}:${idx}`
                const r = stepResults[stepKey]
                const isRunning = runningStepKey === stepKey
                const hasTool = !!toolMap[step.tool]

                return (
                  <div key={stepKey} className="session-step-row">
                    <div className="session-step-head">
                      <span className="session-tool-chip mono">{step.tool}</span>
                      <button
                        className="session-run-btn"
                        onClick={() => onRunStep(s, step, idx)}
                        disabled={isRunning || !hasTool}
                        title={!hasTool ? 'Tool endpoint not found in catalog' : 'Run this tool now'}
                      >
                        {isRunning ? <RefreshCw size={12} className="spin" /> : <Play size={12} />}
                        {isRunning ? 'Running…' : 'Run'}
                      </button>
                    </div>

                    <textarea
                      className="session-step-params mono"
                      value={stepDrafts[stepKey] ?? JSON.stringify(step.parameters ?? {}, null, 2)}
                      onChange={e => onStepDraftChange(stepKey, e.target.value)}
                      rows={3}
                    />

                    {r?.error && <div className="run-error">{r.error}</div>}
                    {r?.result && (
                      <div className="session-step-result mono">
                        {r.result.success ? 'OK' : 'FAIL'} | exit {r.result.return_code} | {r.result.execution_time.toFixed(2)}s
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function SessionsPage({ demoData }: SessionsPageProps) {
  const [data, setData] = useState<SessionsResponse | null>(demoData?.sessions ?? null)
  const [tools, setTools] = useState<Tool[]>([])
  const [expandedSessions, setExpandedSessions] = useState<Record<string, boolean>>({})
  const [sessionTargets, setSessionTargets] = useState<Record<string, string>>({})
  const [stepDrafts, setStepDrafts] = useState<Record<string, string>>({})
  const [runningStepKey, setRunningStepKey] = useState<string | null>(null)
  const [stepResults, setStepResults] = useState<Record<string, { result?: ToolExecResponse; error?: string }>>({})
  const [handoffLoading, setHandoffLoading] = useState<Record<string, boolean>>({})
  const [handoffState, setHandoffState] = useState<Record<string, string>>({})
  const [creatingSession, setCreatingSession] = useState(false)
  const [createMsg, setCreateMsg] = useState<string | null>(null)
  const [startMode, setStartMode] = useState<StartMode | null>(null)
  const [modalTarget, setModalTarget] = useState('')
  const [modalNote, setModalNote] = useState('')
  const [modalError, setModalError] = useState<string | null>(null)
  const [loading, setLoading] = useState(!demoData)
  const [error, setError] = useState<string | null>(null)
  const [streamStatus, setStreamStatus] = useState<'streaming' | 'polling' | 'error'>(demoData ? 'polling' : 'streaming')
  const streamRef = useRef<EventSource | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)

  useEffect(() => {
    if (demoData) return
    Promise.all([api.sessions(), api.tools()])
      .then(([sessionsData, toolData]) => {
        setData(sessionsData)
        setTools(toolData.tools)
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
      setExpandedSessions(prev => ({ ...prev, [sid]: true }))
      setSessionTargets(prev => ({ ...prev, [sid]: target }))
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

  async function handoverToLlm(s: SessionSummary, steps: AttackChainStep[]) {
    setHandoffLoading(prev => ({ ...prev, [s.session_id]: true }))
    try {
      const note = `Tools: ${steps.map(step => step.tool).join(', ')}`
      const r = await api.handoverSession(s.session_id, note)
      const category = r.handover?.category ?? 'unknown'
      const confidence = r.handover?.confidence ?? 0
      setHandoffState(prev => ({
        ...prev,
        [s.session_id]: `LLM handoff done for ${s.session_id} -> ${category} (${(confidence * 100).toFixed(0)}% confidence)`,
      }))
    } catch (e) {
      setHandoffState(prev => ({ ...prev, [s.session_id]: `Handover failed: ${String(e)}` }))
    } finally {
      setHandoffLoading(prev => ({ ...prev, [s.session_id]: false }))
    }
  }

  async function runStep(s: SessionSummary, step: AttackChainStep, index: number) {
    const stepKey = `${s.session_id}:${index}`
    const tool = tools.find(t => t.name === step.tool)
    if (!tool) {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: `Tool ${step.tool} not found in tool catalog` } }))
      return
    }

    let manualParams: Record<string, unknown> = {}
    const raw = stepDrafts[stepKey] ?? JSON.stringify(step.parameters ?? {}, null, 2)
    try {
      const parsed = JSON.parse(raw)
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        setStepResults(prev => ({ ...prev, [stepKey]: { error: 'Parameters must be a JSON object' } }))
        return
      }
      manualParams = parsed as Record<string, unknown>
    } catch {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: 'Invalid JSON in parameters editor' } }))
      return
    }

    const target = (sessionTargets[s.session_id] ?? s.target ?? '').trim()
    const payload: Record<string, unknown> = { ...manualParams }
    const missing: string[] = []
    for (const req of Object.keys(tool.params)) {
      const current = payload[req]
      if (current !== undefined && String(current).trim() !== '') continue
      const guessed = inferTargetValue(req, target)
      if (guessed !== undefined && guessed !== '') payload[req] = guessed
    }
    for (const req of Object.keys(tool.params)) {
      const current = payload[req]
      if (current === undefined || String(current).trim() === '') missing.push(req)
    }

    if (missing.length > 0) {
      setStepResults(prev => ({
        ...prev,
        [stepKey]: { error: `Missing required params: ${missing.join(', ')}` },
      }))
      return
    }

    const editedSteps = normalizeStepsFromSession(s).map((existingStep, i) => {
      if (i !== index) return existingStep
      return { ...existingStep, parameters: payload }
    })

    try {
      await api.updateSession(s.session_id, {
        target,
        workflow_steps: editedSteps,
      })
      refresh()
    } catch {
      // non-fatal for local execution flow
    }

    setRunningStepKey(stepKey)
    setStepResults(prev => ({ ...prev, [stepKey]: {} }))
    try {
      const result = await api.runTool(tool.endpoint, payload)
      setStepResults(prev => ({ ...prev, [stepKey]: { result } }))
    } catch (e) {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: String(e) } }))
    } finally {
      setRunningStepKey(null)
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

  const active = data?.active ?? []
  const completed = data?.completed ?? []
  const allFindings = [...active, ...completed].reduce((sum, s) => sum + s.total_findings, 0)
  const uniqueTargets = new Set([...active, ...completed].map(s => s.target)).size
  const toolMap = Object.fromEntries(tools.map(t => [t.name, t]))

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
              <p className="modal-desc">{startMode.description} {startMode.details}</p>
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
                    {creatingSession ? <RefreshCw size={13} className="spin" /> : <Play size={13} />}
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
            <span className={`sessions-stream-status sessions-stream-status--${streamStatus}`}>
              {streamStatus === 'streaming' ? 'Live' : streamStatus === 'polling' ? 'Polling' : 'Offline'}
            </span>
            <button className="icon-btn" onClick={() => refresh()} title="Refresh">
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>
        {active.length === 0 ? (
          <div className="tasks-empty">
            <Layers size={28} color="var(--text-dim)" />
            <p>No active sessions. Start a session from target to run tools manually.</p>
          </div>
        ) : (
          <div className="sessions-grid">
            {active.map(s => {
              const steps = normalizeStepsFromSession(s)
              return (
                <SessionCard
                  key={s.session_id}
                  s={s}
                  expanded={!!expandedSessions[s.session_id]}
                  sessionTargetValue={sessionTargets[s.session_id] ?? s.target}
                  onToggleExpand={() => setExpandedSessions(prev => ({ ...prev, [s.session_id]: !prev[s.session_id] }))}
                  onTargetChange={v => setSessionTargets(prev => ({ ...prev, [s.session_id]: v }))}
                  steps={steps}
                  toolMap={toolMap}
                  stepDrafts={stepDrafts}
                  runningStepKey={runningStepKey}
                  stepResults={stepResults}
                  onStepDraftChange={(stepKey, next) => setStepDrafts(prev => ({ ...prev, [stepKey]: next }))}
                  onRunStep={runStep}
                  handoffPending={!!handoffLoading[s.session_id]}
                  handoffResult={handoffState[s.session_id] ?? null}
                  onHandover={() => handoverToLlm(s, steps)}
                />
              )
            })}
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
            {completed.map(s => {
              const steps = normalizeStepsFromSession(s)
              return (
                <SessionCard
                  key={s.session_id}
                  s={s}
                  expanded={!!expandedSessions[s.session_id]}
                  sessionTargetValue={sessionTargets[s.session_id] ?? s.target}
                  onToggleExpand={() => setExpandedSessions(prev => ({ ...prev, [s.session_id]: !prev[s.session_id] }))}
                  onTargetChange={v => setSessionTargets(prev => ({ ...prev, [s.session_id]: v }))}
                  steps={steps}
                  toolMap={toolMap}
                  stepDrafts={stepDrafts}
                  runningStepKey={runningStepKey}
                  stepResults={stepResults}
                  onStepDraftChange={(stepKey, next) => setStepDrafts(prev => ({ ...prev, [stepKey]: next }))}
                  onRunStep={runStep}
                  handoffPending={!!handoffLoading[s.session_id]}
                  handoffResult={handoffState[s.session_id] ?? null}
                  onHandover={() => handoverToLlm(s, steps)}
                />
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
