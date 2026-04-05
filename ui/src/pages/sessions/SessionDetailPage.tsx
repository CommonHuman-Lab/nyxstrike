import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, Bot, RefreshCw, Target, Activity, Clock } from 'lucide-react'
import { api, type SessionSummary, type AttackChainStep, type Tool, type ToolExecResponse } from '../../api'
import { buildInitialFieldValues, buildRunPayload } from '../../components/tool-run/payload'
import { fmtTs } from '../../shared/utils'
import { SessionDetailWorkbench } from './SessionDetailWorkbench'
import { TemplateModal } from './TemplateModal'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import {
  normalizeStepsFromSession,
  resolveToolForStep,
  type PersistedStepResult,
  type StepState,
} from './sessionDetailUtils'
import './SessionsPage.css'
import '../../components/tool-run/shared.css'

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
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [templateError, setTemplateError] = useState<string | null>(null)
  const [showAddTool, setShowAddTool] = useState(false)
  const [addToolSearch, setAddToolSearch] = useState('')
  const [handoffLoading, setHandoffLoading] = useState(false)
  const [handoffMsg, setHandoffMsg] = useState<string | null>(null)
  const [showCompleteConfirm, setShowCompleteConfirm] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [completeLoading, setCompleteLoading] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)

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
    setCompleteLoading(true)
    try {
      await api.updateSession(session.session_id, { status: 'completed' })
      onBack()
    } catch (e) {
      setHandoffMsg(`Complete failed: ${String(e)}`)
    } finally {
      setCompleteLoading(false)
      setShowCompleteConfirm(false)
    }
  }

  async function deleteSession() {
    if (!session) return
    setDeleteLoading(true)
    try {
      await api.deleteSession(session.session_id)
      onBack()
    } catch (e) {
      setHandoffMsg(`Delete failed: ${String(e)}`)
    } finally {
      setDeleteLoading(false)
      setShowDeleteConfirm(false)
    }
  }

  async function createTemplateFromSession() {
    if (!session) return
    const name = templateName.trim()
    if (!name) {
      setTemplateError('Template name is required')
      return
    }
    try {
      const currentSteps = normalizeStepsFromSession(session)
      if (currentSteps.length === 0) {
        setTemplateError('Session has no tools to save as template')
        return
      }
      try {
        await api.createSessionTemplate({
          name,
          workflow_steps: currentSteps,
          source_session_id: session.session_id,
        })
      } catch {
        await api.createSessionTemplateCompat({
          name,
          workflow_steps: currentSteps,
          source_session_id: session.session_id,
        })
      }
      setTemplateError(null)
      setTemplateName('')
      setShowTemplateModal(false)
      setHandoffMsg(`Template created: ${name}`)
    } catch (e) {
      setTemplateError(String(e))
    }
  }

  const selectedStep = steps[selectedStepIndex] ?? null
  const selectedStepKey = selectedStep && session ? `${session.session_id}:${selectedStepIndex}` : null
  const selectedResult = selectedStepKey ? stepResults[selectedStepKey] : undefined
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
          <button className="session-action-btn" onClick={() => setShowTemplateModal(true)}>
            Create Template
          </button>
          <button className="session-action-btn" onClick={handoverToLlm} disabled={handoffLoading}>
            <Bot size={12} /> {handoffLoading ? 'Handing over…' : 'Handover to LLM'}
          </button>
          {session.status !== 'completed' && <button className="session-complete-btn" onClick={() => setShowCompleteConfirm(true)}>Complete Session</button>}
          <button className="session-delete-btn" onClick={() => setShowDeleteConfirm(true)}>Delete Session</button>
          {handoffMsg && <span className="section-meta">{handoffMsg}</span>}
        </div>

        <TemplateModal
          show={showTemplateModal}
          templateName={templateName}
          templateError={templateError}
          setTemplateName={setTemplateName}
          onClose={() => setShowTemplateModal(false)}
          onSave={createTemplateFromSession}
        />

        <ConfirmActionModal
          isOpen={showCompleteConfirm}
          title="Complete Session"
          description="Mark this session as completed? It will move to Completed Sessions."
          impactItems={[
            `Session ID: ${session.session_id}`,
            'Session will become read-only',
          ]}
          confirmLabel="Yes, complete session"
          cancelLabel="Keep active"
          confirmVariant="danger"
          isConfirming={completeLoading}
          onConfirm={completeSession}
          onClose={() => setShowCompleteConfirm(false)}
        />

        <ConfirmActionModal
          isOpen={showDeleteConfirm}
          title="Delete Session"
          description="Delete this session permanently? This action cannot be undone."
          impactItems={[
            `Session ID: ${session.session_id}`,
            'All workflow state and run metadata will be removed',
          ]}
          confirmLabel="Yes, delete session"
          cancelLabel="Keep session"
          confirmVariant="danger"
          isConfirming={deleteLoading}
          onConfirm={deleteSession}
          onClose={() => setShowDeleteConfirm(false)}
        />
      </section>

      <SessionDetailWorkbench
        isCompleted={isCompleted}
        sessionId={session.session_id}
        steps={steps}
        selectedStep={selectedStep}
        selectedStepIndex={selectedStepIndex}
        setSelectedStepIndex={setSelectedStepIndex}
        selectedStepKey={selectedStepKey}
        selectedTool={selectedTool}
        stepState={stepState}
        runningStepKey={runningStepKey}
        targetValue={targetValue}
        setTargetValue={setTargetValue}
        stepFieldValues={stepFieldValues}
        setStepFieldValues={setStepFieldValues}
        showOptionalByStep={showOptionalByStep}
        setShowOptionalByStep={setShowOptionalByStep}
        selectedResult={selectedResult}
        onRunStep={runStep}
        onRemoveTool={removeToolFromSession}
        showAddTool={showAddTool}
        setShowAddTool={setShowAddTool}
        addToolSearch={addToolSearch}
        setAddToolSearch={setAddToolSearch}
        addCandidates={addCandidates}
        onAddTool={addToolToSession}
      />
    </div>
  )
}
