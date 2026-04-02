import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, Bot, Play, RefreshCw, Target, Activity, Clock, ChevronDown, ChevronUp, Trash2, Download } from 'lucide-react'
import { api, type SessionSummary, type AttackChainStep, type Tool, type ToolExecResponse } from '../api'
import { ParamField } from '../components/tool-run/ParamField'
import { buildInitialFieldValues, buildRunPayload } from '../components/tool-run/payload'
import { exportEntry } from '../utils'
import type { RunHistoryEntry } from '../types'
import './SessionsPage.css'
import '../components/tool-run/shared.css'

function fmtTs(ts: number) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString('en-GB')
}

function normalizeStepsFromSession(s: SessionSummary): AttackChainStep[] {
  if (Array.isArray(s.workflow_steps) && s.workflow_steps.length > 0) return s.workflow_steps
  return s.tools_executed.map(tool => ({ tool, parameters: {} }))
}

function normalizeToken(v: string): string {
  return v.toLowerCase().replace(/[^a-z0-9]/g, '')
}

function resolveToolForStep(stepTool: string, tools: Tool[]): Tool | null {
  const step = stepTool.trim()
  if (!step) return null

  const directByName = tools.find(t => t.name === step)
  if (directByName) return directByName

  const directByEndpoint = tools.find(t => t.endpoint === step)
  if (directByEndpoint) return directByEndpoint

  const directByParent = tools.find(t => t.parent_tool === step)
  if (directByParent) return directByParent

  const ns = normalizeToken(step)
  let best: { tool: Tool; score: number } | null = null
  for (const t of tools) {
    const name = normalizeToken(t.name)
    const parent = normalizeToken(t.parent_tool ?? '')
    const endpoint = normalizeToken(t.endpoint)
    let score = 0
    if (name === ns) score = Math.max(score, 80)
    if (parent === ns) score = Math.max(score, 75)
    if (endpoint === ns) score = Math.max(score, 70)
    if (name.includes(ns)) score = Math.max(score, 62)
    if (endpoint.includes(ns)) score = Math.max(score, 58)
    if (parent && parent.includes(ns)) score = Math.max(score, 56)
    if (ns.includes(name)) score = Math.max(score, 52)
    if (score === 0) continue
    if (!best || score > best.score) best = { tool: t, score }
  }
  return best?.tool ?? null
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
  onToolRun,
}: {
  sessionId: string
  tools: Tool[]
  onBack: () => void
  onToolRun?: (tool: string, params: Record<string, unknown>, result: ToolExecResponse) => void
}) {
  const [session, setSession] = useState<SessionSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [targetValue, setTargetValue] = useState('')
  const [stepFieldValues, setStepFieldValues] = useState<Record<string, Record<string, string>>>({})
  const [showOptionalByStep, setShowOptionalByStep] = useState<Record<string, boolean>>({})
  const [runningStepKey, setRunningStepKey] = useState<string | null>(null)
  const [stepResults, setStepResults] = useState<Record<string, { result?: ToolExecResponse; error?: string }>>({})
  const [stepState, setStepState] = useState<Record<string, StepState>>({})
  const [selectedStepIndex, setSelectedStepIndex] = useState(0)
  const [showAddTool, setShowAddTool] = useState(false)
  const [addToolSearch, setAddToolSearch] = useState('')
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

  async function deleteSession() {
    if (!session) return
    try {
      await api.deleteSession(session.session_id)
      onBack()
    } catch (e) {
      setHandoffMsg(`Delete failed: ${String(e)}`)
    }
  }

  const selectedStep = steps[selectedStepIndex] ?? null
  const selectedStepKey = selectedStep && session ? `${session.session_id}:${selectedStepIndex}` : null
  const selectedResult = selectedStepKey ? stepResults[selectedStepKey] : undefined
  const resultData = selectedResult?.result
  const selectedRunning = selectedStepKey ? runningStepKey === selectedStepKey : false
  const selectedTool = selectedStep ? toolMap[selectedStep.tool] : null

  useEffect(() => {
    if (!session || !selectedStep || !selectedStepKey || !selectedTool) return
    setStepFieldValues(prev => {
      if (prev[selectedStepKey]) return prev
      return {
        ...prev,
        [selectedStepKey]: buildInitialFieldValues(selectedTool, selectedStep, targetValue.trim() || session.target),
      }
    })
    setShowOptionalByStep(prev => ({ ...prev, [selectedStepKey]: prev[selectedStepKey] ?? false }))
  }, [session, selectedStep, selectedStepKey, selectedTool, targetValue])

  async function runStep(step: AttackChainStep, index: number) {
    if (!session) return
    const sessionRef = session
    const stepKey = `${sessionRef.session_id}:${index}`
    const tool = resolveToolForStep(step.tool, tools)
    if (!tool) {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: `Tool ${step.tool} could not be mapped to registry` } }))
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      return
    }

    const target = targetValue.trim()
    const fieldValues = stepFieldValues[stepKey] ?? buildInitialFieldValues(tool, step, target || sessionRef.target)
    const { payload, missing } = buildRunPayload(tool, fieldValues)
    if (missing.length > 0) {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: `Missing required: ${missing.join(', ')}` } }))
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      return
    }

    const editedSteps = steps.map((existingStep, i) => (i === index ? { ...existingStep, parameters: payload } : existingStep))
    try {
      await api.updateSession(sessionRef.session_id, { target, workflow_steps: editedSteps })
    } catch {
      // non-fatal
    }

    setRunningStepKey(stepKey)
    setStepResults(prev => ({ ...prev, [stepKey]: {} }))
    try {
      const result = await api.runTool(tool.endpoint, payload)
      setStepResults(prev => ({ ...prev, [stepKey]: { result } }))
      setStepState(prev => ({ ...prev, [stepKey]: result.success ? 'success' : 'failed' }))
      if (onToolRun) onToolRun(step.tool, payload, result)

      const existingMeta = (sessionRef.metadata ?? {}) as Record<string, unknown>
      const existingToolStatus = (existingMeta.tool_status && typeof existingMeta.tool_status === 'object') ? (existingMeta.tool_status as Record<string, string>) : {}
      const existingStepResults = (existingMeta.step_results && typeof existingMeta.step_results === 'object') ? (existingMeta.step_results as Record<string, PersistedStepResult>) : {}
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
    } finally {
      setRunningStepKey(null)
    }
  }

  async function addToolToSession(tool: Tool) {
    if (!session) return
    const nextSteps = [...steps, { tool: tool.name, parameters: {} }]
    try {
      await api.updateSession(session.session_id, { workflow_steps: nextSteps })
      setShowAddTool(false)
      setAddToolSearch('')
      await loadSession()
      setSelectedStepIndex(Math.max(0, nextSteps.length - 1))
    } catch (e) {
      setHandoffMsg(`Add tool failed: ${String(e)}`)
    }
  }

  async function removeToolFromSession(index: number) {
    if (!session) return
    const nextSteps = steps.filter((_, i) => i !== index)
    try {
      await api.updateSession(session.session_id, { workflow_steps: nextSteps })
      await loadSession()
      setSelectedStepIndex(prev => {
        if (nextSteps.length === 0) return 0
        if (prev > index) return prev - 1
        return Math.min(prev, nextSteps.length - 1)
      })
    } catch (e) {
      setHandoffMsg(`Remove tool failed: ${String(e)}`)
    }
  }

  if (loading) return (
    <div className="loading-state">
      <RefreshCw size={20} className="spin" color="var(--green)" />
      <p>Loading session…</p>
    </div>
  )
  if (error || !session) return <div className="error-banner">{error ?? 'Session not found'}</div>

  const isCompleted = (session.status ?? 'active') === 'completed'
  const addCandidates = tools
    .filter(t => {
      if (!addToolSearch.trim()) return true
      const q = addToolSearch.toLowerCase()
      return t.name.toLowerCase().includes(q) || t.desc.toLowerCase().includes(q) || t.category.toLowerCase().includes(q)
    })
    .slice(0, 12)

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
          {session.status !== 'completed' && <button className="session-complete-btn" onClick={completeSession}>Complete Session</button>}
          <button className="session-delete-btn" onClick={deleteSession}>Delete Session</button>
          {handoffMsg && <span className="section-meta">{handoffMsg}</span>}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h3>Manual Tool Execution <span className="badge">{steps.length}</span></h3>
        </div>
        <div className="session-workbench">
          <aside className="session-workbench-tools">
            {!isCompleted && (
              <div className="session-tool-manage">
                <button className="session-add-tool-btn" onClick={() => setShowAddTool(v => !v)}>+ Add tool</button>
                {showAddTool && (
                  <div className="session-add-tool-panel">
                    <input
                      className="search-input mono"
                      placeholder="Search tool..."
                      value={addToolSearch}
                      onChange={e => setAddToolSearch(e.target.value)}
                    />
                    <div className="session-add-tool-list">
                      {addCandidates.map(t => (
                        <button key={t.name} className="session-add-tool-item" onClick={() => addToolToSession(t)}>
                          <span className="mono">{t.name}</span>
                          <span>{t.category}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {steps.map((step, idx) => {
              const stepKey = `${session.session_id}:${idx}`
              return (
                <button
                  key={stepKey}
                  className={`session-workbench-tool session-workbench-tool--${stepState[stepKey] ?? 'idle'} ${selectedStepIndex === idx ? 'active' : ''}`}
                  onClick={() => setSelectedStepIndex(idx)}
                >
                  <span className="session-workbench-tool-name mono">{step.tool}</span>
                  {!isCompleted && (
                    <button
                      type="button"
                      className="session-remove-tool"
                      onClick={e => {
                        e.stopPropagation()
                        removeToolFromSession(idx)
                      }}
                      title="Remove tool"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </button>
              )
            })}
          </aside>

          <div className="session-workbench-center">
            {!selectedStep || !selectedStepKey || !selectedTool ? (
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
                    <span className={`session-tool-chip mono session-tool-chip--${stepState[selectedStepKey] ?? 'idle'}`}>{selectedStep.tool}</span>
                    <button
                      className="session-run-btn"
                      onClick={() => runStep(selectedStep, selectedStepIndex)}
                      disabled={isCompleted || selectedRunning}
                    >
                      {selectedRunning ? <RefreshCw size={12} className="spin" /> : <Play size={12} />}
                      {isCompleted ? 'Completed' : (selectedRunning ? 'Running…' : `Run ${selectedStep.tool}`)}
                    </button>
                  </div>

                  <div className="session-param-grid">
                    {Object.keys(selectedTool.params).map(k => (
                      <ParamField
                        key={k}
                        name={k}
                        value={stepFieldValues[selectedStepKey]?.[k] ?? ''}
                        onChange={v => setStepFieldValues(prev => ({
                          ...prev,
                          [selectedStepKey]: { ...(prev[selectedStepKey] ?? {}), [k]: v },
                        }))}
                        required
                        disabled={isCompleted}
                      />
                    ))}

                    {Object.keys(selectedTool.optional).length > 0 && (
                      <button
                        className="run-opt-btn"
                        onClick={() => setShowOptionalByStep(prev => ({ ...prev, [selectedStepKey]: !prev[selectedStepKey] }))}
                      >
                        {showOptionalByStep[selectedStepKey] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        Optional parameters ({Object.keys(selectedTool.optional).length})
                      </button>
                    )}

                    {showOptionalByStep[selectedStepKey] && Object.keys(selectedTool.optional).map(k => (
                      <ParamField
                        key={k}
                        name={k}
                        value={stepFieldValues[selectedStepKey]?.[k] ?? ''}
                        onChange={v => setStepFieldValues(prev => ({
                          ...prev,
                          [selectedStepKey]: { ...(prev[selectedStepKey] ?? {}), [k]: v },
                        }))}
                        disabled={isCompleted}
                      />
                    ))}
                  </div>
                </div>

                <div className="session-result-panel">
                  <h4>Result</h4>
                  {isCompleted && <p className="section-meta">Completed session: results are read-only.</p>}
                  {selectedResult?.error && <div className="run-error">{selectedResult.error}</div>}
                  {resultData ? (
                    <>
                      {selectedStepKey && resultData && (
                        <div className="session-result-actions">
                          <button
                            className="run-export-btn"
                            onClick={() => {
                              const entry: RunHistoryEntry = {
                                id: Date.now(),
                                tool: selectedStep.tool,
                                params: stepFieldValues[selectedStepKey] ?? {},
                                result: resultData,
                                ts: new Date(resultData.timestamp),
                                source: 'browser',
                              }
                              exportEntry(entry, 'txt')
                            }}
                            title="Export as .txt"
                          >
                            <Download size={11} /> TXT
                          </button>
                          <button
                            className="run-export-btn"
                            onClick={() => {
                              const entry: RunHistoryEntry = {
                                id: Date.now(),
                                tool: selectedStep.tool,
                                params: stepFieldValues[selectedStepKey] ?? {},
                                result: resultData,
                                ts: new Date(resultData.timestamp),
                                source: 'browser',
                              }
                              exportEntry(entry, 'json')
                            }}
                            title="Export as .json"
                          >
                            <Download size={11} /> JSON
                          </button>
                        </div>
                      )}
                      <div className="session-step-result mono">
                        {resultData.success ? 'OK' : 'FAIL'} | exit {resultData.return_code} | {resultData.execution_time.toFixed(2)}s
                      </div>
                      <pre className="session-result-pre mono">{resultData.stdout || '(no stdout)'}</pre>
                      {resultData.stderr && <pre className="session-result-pre mono">{resultData.stderr}</pre>}
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
