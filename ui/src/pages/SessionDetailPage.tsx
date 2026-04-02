import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, Bot, Play, RefreshCw, Target, Activity, Clock } from 'lucide-react'
import { api, type SessionSummary, type AttackChainStep, type Tool, type ToolExecResponse } from '../api'
import './SessionsPage.css'

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
  if (Array.isArray(s.workflow_steps) && s.workflow_steps.length > 0) return s.workflow_steps
  return s.tools_executed.map(tool => ({ tool, parameters: {} }))
}

type StepState = 'idle' | 'success' | 'failed'

type PersistedStepResult = {
  success: boolean
  return_code: number
  execution_time: number
  timestamp?: string
  stdout?: string
  stderr?: string
}

export default function SessionDetailPage({
  sessionId,
  tools,
  onBack,
}: {
  sessionId: string
  tools: Tool[]
  onBack: () => void
}) {
  const [session, setSession] = useState<SessionSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [targetValue, setTargetValue] = useState('')
  const [stepDrafts, setStepDrafts] = useState<Record<string, string>>({})
  const [runningStepKey, setRunningStepKey] = useState<string | null>(null)
  const [stepResults, setStepResults] = useState<Record<string, { result?: ToolExecResponse; error?: string }>>({})
  const [stepState, setStepState] = useState<Record<string, StepState>>({})
  const [selectedStepIndex, setSelectedStepIndex] = useState(0)
  const [handoffLoading, setHandoffLoading] = useState(false)
  const [handoffMsg, setHandoffMsg] = useState<string | null>(null)

  const toolMap = useMemo(() => Object.fromEntries(tools.map(t => [t.name, t])), [tools])
  const steps = session ? normalizeStepsFromSession(session) : []

  async function loadSession() {
    setLoading(true)
    try {
      const r = await api.session(sessionId)
      setSession(r.session)
      setTargetValue(r.session.target)

      const meta = (r.session.metadata ?? {}) as Record<string, unknown>
      const storedStatus = (meta.tool_status ?? {}) as Record<string, string>
      const storedResults = (meta.step_results ?? {}) as Record<string, PersistedStepResult>

      const hydratedState: Record<string, StepState> = {}
      const hydratedResults: Record<string, { result?: ToolExecResponse; error?: string }> = {}
      for (const [k, v] of Object.entries(storedStatus)) {
        if (v === 'success' || v === 'failed') hydratedState[k] = v
      }
      for (const [k, v] of Object.entries(storedResults)) {
        if (!v || typeof v !== 'object') continue
        hydratedResults[k] = {
          result: {
            success: !!v.success,
            return_code: Number(v.return_code ?? 0),
            execution_time: Number(v.execution_time ?? 0),
            timed_out: false,
            partial_results: false,
            stdout: String(v.stdout ?? ''),
            stderr: String(v.stderr ?? ''),
            timestamp: String(v.timestamp ?? new Date().toISOString()),
          },
        }
      }

      setStepState(hydratedState)
      setStepResults(hydratedResults)
      setError(null)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSession()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  async function handoverToLlm() {
    if (!session) return
    setHandoffLoading(true)
    try {
      const note = `Tools: ${steps.map(step => step.tool).join(', ')}`
      const r = await api.handoverSession(session.session_id, note)
      const category = r.handover?.category ?? 'unknown'
      const confidence = r.handover?.confidence ?? 0
      setHandoffMsg(`LLM handover done -> ${category} (${(confidence * 100).toFixed(0)}% confidence)`)
      await loadSession()
    } catch (e) {
      setHandoffMsg(`Handover failed: ${String(e)}`)
    } finally {
      setHandoffLoading(false)
    }
  }

  async function completeSession() {
    if (!session) return
    try {
      await api.updateSession(session.session_id, { status: 'completed' })
      onBack()
    } catch (e) {
      setHandoffMsg(`Complete failed: ${String(e)}`)
    }
  }

  async function runStep(step: AttackChainStep, index: number) {
    if (!session) return
    const sessionRef = session
    const stepKey = `${sessionRef.session_id}:${index}`
    const tool = tools.find(t => t.name === step.tool)
    if (!tool) {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: `Tool ${step.tool} not found in tool catalog` } }))
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      return
    }

    let manualParams: Record<string, unknown> = {}
    const raw = stepDrafts[stepKey] ?? JSON.stringify(step.parameters ?? {}, null, 2)
    try {
      const parsed = JSON.parse(raw)
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        setStepResults(prev => ({ ...prev, [stepKey]: { error: 'Parameters must be a JSON object' } }))
        setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
        return
      }
      manualParams = parsed as Record<string, unknown>
    } catch {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: 'Invalid JSON in parameters editor' } }))
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      return
    }

    const target = targetValue.trim()
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
      setStepResults(prev => ({ ...prev, [stepKey]: { error: `Missing required params: ${missing.join(', ')}` } }))
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      return
    }

    const editedSteps = steps.map((existingStep, i) => {
      if (i !== index) return existingStep
      return { ...existingStep, parameters: payload }
    })

    try {
      await api.updateSession(sessionRef.session_id, {
        target,
        workflow_steps: editedSteps,
      })
    } catch {
      // non-fatal
    }

    setRunningStepKey(stepKey)
    setStepResults(prev => ({ ...prev, [stepKey]: {} }))
    try {
      const result = await api.runTool(tool.endpoint, payload)
      setStepResults(prev => ({ ...prev, [stepKey]: { result } }))
      setStepState(prev => ({ ...prev, [stepKey]: result.success ? 'success' : 'failed' }))

      const existingMeta = (sessionRef.metadata ?? {}) as Record<string, unknown>
      const existingToolStatus =
        existingMeta.tool_status && typeof existingMeta.tool_status === 'object'
          ? (existingMeta.tool_status as Record<string, string>)
          : {}
      const existingStepResults =
        existingMeta.step_results && typeof existingMeta.step_results === 'object'
          ? (existingMeta.step_results as Record<string, PersistedStepResult>)
          : {}
      await api.updateSession(sessionRef.session_id, {
        metadata: {
          ...existingMeta,
          tool_status: {
            ...existingToolStatus,
            [step.tool]: result.success ? 'success' : 'failed',
            [stepKey]: result.success ? 'success' : 'failed',
          },
          step_results: {
            ...existingStepResults,
            [stepKey]: {
              success: result.success,
              return_code: result.return_code,
              execution_time: result.execution_time,
              timestamp: result.timestamp,
              stdout: result.stdout,
              stderr: result.stderr,
            },
          },
          last_run: {
            step_key: stepKey,
            tool: step.tool,
            success: result.success,
            return_code: result.return_code,
            execution_time: result.execution_time,
            timestamp: result.timestamp,
          },
        },
      })
      await loadSession()
    } catch (e) {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: String(e) } }))
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      try {
        const existingMeta = (sessionRef.metadata ?? {}) as Record<string, unknown>
        const existingToolStatus =
          existingMeta.tool_status && typeof existingMeta.tool_status === 'object'
            ? (existingMeta.tool_status as Record<string, string>)
            : {}
        await api.updateSession(sessionRef.session_id, {
          metadata: {
            ...existingMeta,
            tool_status: {
              ...existingToolStatus,
              [step.tool]: 'failed',
              [stepKey]: 'failed',
            },
            last_run: {
              step_key: stepKey,
              tool: step.tool,
              success: false,
              return_code: -1,
              execution_time: 0,
              timestamp: new Date().toISOString(),
            },
          },
        })
        await loadSession()
      } catch {
        // non-fatal
      }
    } finally {
      setRunningStepKey(null)
    }
  }

  if (loading) {
    return (
      <div className="loading-state">
        <RefreshCw size={20} className="spin" color="var(--green)" />
        <p>Loading session…</p>
      </div>
    )
  }
  if (error || !session) {
    return <div className="error-banner">{error ?? 'Session not found'}</div>
  }

  const selectedStep = steps[selectedStepIndex] ?? null
  const selectedStepKey = selectedStep ? `${session.session_id}:${selectedStepIndex}` : null
  const selectedResult = selectedStepKey ? stepResults[selectedStepKey] : undefined
  const selectedRunning = selectedStepKey ? runningStepKey === selectedStepKey : false
  const selectedTool = selectedStep ? toolMap[selectedStep.tool] : null
  const isCompleted = (session.status ?? 'active') === 'completed'

  return (
    <div className="page-content">
      <section className="section">
        <div className="section-header">
          <h3>Session Detail</h3>
          <button className="session-action-btn" onClick={onBack}><ArrowLeft size={12} /> Back</button>
        </div>
        <div className="session-detail-meta-row">
          <span><Target size={12} /> <span className="mono">{session.target}</span></span>
          <span><Activity size={12} /> {session.total_findings} findings</span>
          <span><RefreshCw size={12} /> {session.iterations} iterations</span>
          <span><Clock size={12} /> {fmtTs(session.updated_at)}</span>
          <span className={`session-status session-status--${session.status ?? 'active'}`}>{session.status ?? 'active'}</span>
        </div>
        <div className="session-detail-actions">
          <button className="session-action-btn" onClick={handoverToLlm} disabled={handoffLoading}>
            <Bot size={12} /> {handoffLoading ? 'Handing over…' : 'Handover to LLM'}
          </button>
          {session.status !== 'completed' && (
            <button className="session-complete-btn" onClick={completeSession}>
              Complete Session
            </button>
          )}
          {handoffMsg && <span className="section-meta">{handoffMsg}</span>}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h3>Manual Tool Execution <span className="badge">{steps.length}</span></h3>
        </div>
        <div className="session-workbench">
          <aside className="session-workbench-tools">
            {steps.map((step, idx) => {
              const stepKey = `${session.session_id}:${idx}`
              return (
                <button
                  key={stepKey}
                  className={`session-workbench-tool ${selectedStepIndex === idx ? 'active' : ''}`}
                  onClick={() => setSelectedStepIndex(idx)}
                >
                  <span className={`session-tool-chip mono session-tool-chip--${stepState[stepKey] ?? 'idle'}`}>{step.tool}</span>
                </button>
              )
            })}
          </aside>

          <div className="session-workbench-center">
            {!selectedStep ? (
              <p className="empty-state">No tools in this session.</p>
            ) : (
              <>
                <div className="session-target-override">
                  <label className="mono">Target</label>
                  <input
                    className="search-input mono"
                    value={targetValue}
                    onChange={e => setTargetValue(e.target.value)}
                    placeholder="Target to run this session against"
                    disabled={isCompleted}
                  />
                </div>

                <div className="session-step-row">
                  <div className="session-step-head">
                    <span className={`session-tool-chip mono session-tool-chip--${selectedStepKey ? (stepState[selectedStepKey] ?? 'idle') : 'idle'}`}>{selectedStep.tool}</span>
                    <button
                      className="session-run-btn"
                      onClick={() => runStep(selectedStep, selectedStepIndex)}
                      disabled={isCompleted || selectedRunning || !selectedTool}
                      title={
                        isCompleted
                          ? 'Completed sessions are read-only'
                          : (!selectedTool ? 'Tool endpoint not found in catalog' : 'Run this tool now')
                      }
                    >
                      {selectedRunning ? <RefreshCw size={12} className="spin" /> : <Play size={12} />}
                      {isCompleted ? 'Completed' : (selectedRunning ? 'Running…' : 'Run')}
                    </button>
                  </div>
                  <textarea
                    className="session-step-params mono"
                    value={selectedStepKey ? (stepDrafts[selectedStepKey] ?? JSON.stringify(selectedStep.parameters ?? {}, null, 2)) : ''}
                    onChange={e => {
                      if (!selectedStepKey) return
                      setStepDrafts(prev => ({ ...prev, [selectedStepKey]: e.target.value }))
                    }}
                    rows={6}
                    readOnly={isCompleted}
                  />
                </div>

                <div className="session-result-panel">
                  <h4>Result</h4>
                  {isCompleted && <p className="section-meta">Completed session: results are read-only.</p>}
                  {selectedResult?.error && <div className="run-error">{selectedResult.error}</div>}
                  {selectedResult?.result ? (
                    <>
                      <div className="session-step-result mono">
                        {selectedResult.result.success ? 'OK' : 'FAIL'} | exit {selectedResult.result.return_code} | {selectedResult.result.execution_time.toFixed(2)}s
                      </div>
                      <pre className="session-result-pre mono">{selectedResult.result.stdout || '(no stdout)'}</pre>
                      {selectedResult.result.stderr && <pre className="session-result-pre mono">{selectedResult.result.stderr}</pre>}
                    </>
                  ) : (
                    <p className="section-meta">No result yet for this tool.</p>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
