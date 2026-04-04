import { useEffect, useRef, useState } from 'react'
import {
  RefreshCw, XCircle, Activity, CheckCircle,
  Layers, Target,
} from 'lucide-react'
import {
  api,
  type SessionsResponse,
  type SessionTemplate,
} from '../../api'
import { StatCard } from '../../components/StatCard'
import { START_MODES, type StartMode } from './constants'
import { SessionListSection, StartSessionModal, StartSessionSection } from './SessionsSections'
import './SessionsPage.css'

interface SessionsPageProps {
  demoData?: { sessions: SessionsResponse }
  onOpenSession: (sessionId: string) => void
}

export default function SessionsPage({ demoData, onOpenSession }: SessionsPageProps) {
  const [data, setData] = useState<SessionsResponse | null>(demoData?.sessions ?? null)
  const [creatingSession, setCreatingSession] = useState(false)
  const [templates, setTemplates] = useState<SessionTemplate[]>([])
  const [createMsg, setCreateMsg] = useState<string | null>(null)
  const [startMode, setStartMode] = useState<StartMode | null>(null)
  const [modalTarget, setModalTarget] = useState('')
  const [modalNote, setModalNote] = useState('')
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
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
    Promise.all([api.sessions(), api.tools(), api.sessionTemplates()])
      .then(([sessionsData, _toolsData, templatesData]) => {
        setData(sessionsData)
        setTemplates(templatesData.templates ?? [])
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
    setSelectedTemplateId('')
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
      let sessionRes
      let stepCount = 0
      if (mode.key === 'manual') {
        sessionRes = await api.createSession({
          target,
          workflow_steps: [],
          source: 'web',
          objective: mode.key,
          metadata: { origin: 'ui/sessions/create', mode: mode.key, note: noteValue, session_name: 'Manual session' },
        })
      } else if (mode.key === 'from_template') {
        const tpl = templates.find(t => t.template_id === selectedTemplateId)
        if (!tpl) {
          setModalError('Template is required')
          return
        }
        stepCount = tpl.workflow_steps.length
        sessionRes = await api.createSessionFromTemplate({
          target,
          template_id: tpl.template_id,
          source: 'web',
          objective: 'from_template',
          metadata: {
            origin: 'ui/sessions/create',
            mode: 'from_template',
            note: noteValue,
            template_id: tpl.template_id,
            session_name: `Template: ${tpl.name}`,
          },
        })
      } else {
        const chain = await api.createAttackChain(target, mode.key)
        stepCount = chain.attack_chain.steps.length
        sessionRes = await api.createSession({
          target,
          workflow_steps: chain.attack_chain.steps,
          source: 'web',
          objective: mode.key,
          session_id: chain.session_id,
          metadata: { origin: 'ui/sessions/create', mode: mode.key, note: noteValue },
        })
      }
      const sid = sessionRes.session.session_id
      setCreateMsg(mode.key === 'manual'
        ? `Session created: ${sid} (empty workflow, add tools manually).`
        : mode.key === 'from_template'
          ? `Session created: ${sid} (${stepCount} template tool calls loaded).`
        : `Session created: ${sid} (${stepCount} tool calls ready).`)
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

      <StartSessionSection
        startModes={START_MODES}
        onOpenStartMode={openStartModal}
        createMsg={createMsg}
      />

      {startMode && (
        <StartSessionModal
          startMode={startMode}
          templates={templates}
          selectedTemplateId={selectedTemplateId}
          setSelectedTemplateId={setSelectedTemplateId}
          modalTarget={modalTarget}
          setModalTarget={setModalTarget}
          modalNote={modalNote}
          setModalNote={setModalNote}
          modalError={modalError}
          creatingSession={creatingSession}
          onClose={closeStartModal}
          onSubmit={() => createSessionFromTarget(startMode, modalTarget, modalNote)}
        />
      )}

      <SessionListSection
        title="Active Sessions"
        sessions={active}
        emptyText="No active sessions. Start a session from target to run tools manually."
        onOpenSession={onOpenSession}
        headerRight={(
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
        )}
      />

      {showHandoverHelp && (
        <section className="section">
          <div className="session-help-box">
            <p><strong>Web handover:</strong> open a session and click <span className="mono">Handover to LLM</span>.</p>
            <p><strong>MCP handover:</strong> call <span className="mono">handover_session("&lt;session_id&gt;", "optional note")</span>.</p>
            <p><strong>Tip:</strong> update target/step parameters before handover so the LLM gets the latest context.</p>
          </div>
        </section>
      )}

      <SessionListSection
        title="Completed Sessions"
        sessions={completed}
        emptyText="No completed sessions yet."
        onOpenSession={onOpenSession}
      />
    </div>
  )
}
