import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, Brain, RefreshCw, Target, Activity, Clock, Download, FileText, Shield, List } from 'lucide-react'
import { api, type SessionSummary, type AttackChainStep, type Tool, type ToolExecResponse } from '../../api'
import { buildInitialFieldValues, buildRunPayload, inferTargetValue } from '../../components/tool-run/payload'
import { fmtTs } from '../../shared/utils'
import { SessionDetailWorkbench } from './SessionDetailWorkbench'
import { SessionNotes } from './SessionNotes'
import { SessionFindings } from './SessionFindings'
import { SessionTimeline } from './SessionTimeline'
import { SessionReportModal } from './SessionReportModal'
import { TemplateModal } from './TemplateModal'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import { InformationModal } from '../../components/InformationModal'
import { useToast } from '../../components/ToastProvider'
import { registerReportNavigation, reportGenStart, reportGenDone, reportGenError } from '../../app/reportGeneration'
import {
  buildStepChainSuggestion,
  type ChainMappingPreference,
  extractStepArtifacts,
  normalizeStepsFromSession,
  resolveToolForStep,
  normalizePersistedResults,
  type PersistedStepResult,
  type StepArtifacts,
  type StepState,
} from './sessionDetailUtils'
import './SessionsPage.css'
import './SessionNotes.css'
import './SessionFindings.css'
import '../../components/tool-run/shared.css'

export default function SessionDetailPage({
  sessionId,
  tools,
  onBack,
  onToolRun,
  llmAvailable = false,
}: {
  sessionId: string
  tools: Tool[]
  onBack: () => void
  onToolRun?: (tool: string, params: Record<string, unknown>, result: ToolExecResponse) => void
  llmAvailable?: boolean
}) {
  const { pushToast } = useToast()
  const [session, setSession] = useState<SessionSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [targetValue, setTargetValue] = useState('')
  const [stepFieldValues, setStepFieldValues] = useState<Record<string, Record<string, string>>>({})
  const [showOptionalByStep, setShowOptionalByStep] = useState<Record<string, boolean>>({})
  const [runningStepKey, setRunningStepKey] = useState<string | null>(null)
  const [stepResults, setStepResults] = useState<Record<string, { result?: ToolExecResponse; error?: string; priorResults?: ToolExecResponse[] }>>({})
  const [stepArtifacts, setStepArtifacts] = useState<Record<string, StepArtifacts>>({})
  const [stepState, setStepState] = useState<Record<string, StepState>>({})
  const [selectedStepIndex, setSelectedStepIndex] = useState(0)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [templateError, setTemplateError] = useState<string | null>(null)
  const [showAddTool, setShowAddTool] = useState(false)
  const [addToolSearch, setAddToolSearch] = useState('')
  const [showCompleteConfirm, setShowCompleteConfirm] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [completeLoading, setCompleteLoading] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [analyzeLoading, setAnalyzeLoading] = useState(false)
  const [followUpLoading, setFollowUpLoading] = useState(false)
  const [selectedChainFields, setSelectedChainFields] = useState<Record<string, boolean>>({})
  const [chainPreferences, setChainPreferences] = useState<ChainMappingPreference[]>([])
  const [showChainPrefModal, setShowChainPrefModal] = useState(false)
  const [activeTab, setActiveTab] = useState<'workflow' | 'notes' | 'findings' | 'timeline'>('workflow')
  const [showReportModal, setShowReportModal] = useState(false)
  const [notesInitialOpenPath, setNotesInitialOpenPath] = useState<string | undefined>(undefined)

  const toolMap = useMemo(() => Object.fromEntries(tools.map(t => [t.name, t])), [tools])
  const toolRequestInFlight = useRef(false)
  const steps = session ? normalizeStepsFromSession(session) : []
  const prefStorageKey = `nyxstrike:chain-prefs:${sessionId}`

  // Register the report-bubble navigation callback for this session page.
  const handleReportNav = useCallback((savedPath: string) => {
    // savedPath: "notes/reports/report-ai-2026-04-13.md"
    // Strip leading "notes/" prefix if present, then split into folder/filename
    const relativePath = savedPath.startsWith('notes/') ? savedPath.slice('notes/'.length) : savedPath
    const withoutExt = relativePath.replace(/\.md$/i, '')
    const slashIdx = withoutExt.indexOf('/')
    const folder = slashIdx !== -1 ? withoutExt.slice(0, slashIdx) : ''
    const filename = slashIdx !== -1 ? withoutExt.slice(slashIdx + 1) : withoutExt
    setNotesInitialOpenPath(`${folder}/${filename}`)
    setActiveTab('notes')
  }, [])

  useEffect(() => {
    return registerReportNavigation(handleReportNav)
  }, [handleReportNav])

  useEffect(() => {
    try {
      const raw = localStorage.getItem(prefStorageKey)
      if (!raw) {
        setChainPreferences([])
        return
      }
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        setChainPreferences(parsed.filter(item => !!item && typeof item === 'object'))
      } else {
        setChainPreferences([])
      }
    } catch {
      setChainPreferences([])
    }
  }, [prefStorageKey])

  useEffect(() => {
    try {
      localStorage.setItem(prefStorageKey, JSON.stringify(chainPreferences))
    } catch {
      // ignore storage failures
    }
  }, [chainPreferences, prefStorageKey])

  async function loadSession() {
    setLoading(true)
    try {
      const r = await api.session(sessionId)
      setSession(r.session)
      setTargetValue(r.session.target)

      const meta = (r.session.metadata ?? {}) as Record<string, unknown>
      const storedStatus = (meta.tool_status ?? {}) as Record<string, string>
      const storedResults = (meta.step_results ?? {}) as Record<string, unknown>
      const storedArtifacts = (meta.step_artifacts ?? {}) as Record<string, StepArtifacts>
      const storedRunningStepKey = typeof meta.running_step_key === 'string' ? meta.running_step_key : null

      const hydratedState: Record<string, StepState> = {}
      const hydratedResults: Record<string, { result?: ToolExecResponse; error?: string; priorResults?: ToolExecResponse[] }> = {}
      for (const [k, v] of Object.entries(storedStatus)) {
        if (v === 'success' || v === 'failed') hydratedState[k] = v
      }
      for (const [k, raw] of Object.entries(storedResults)) {
        const runs = normalizePersistedResults(raw)
        if (runs.length === 0) continue
        const toToolExecResponse = (v: PersistedStepResult): ToolExecResponse => ({
          success: !!v.success,
          return_code: Number(v.return_code ?? 0),
          execution_time: Number(v.execution_time ?? 0),
          timed_out: false,
          partial_results: false,
          stdout: String(v.stdout ?? ''),
          stderr: String(v.stderr ?? ''),
          timestamp: String(v.timestamp ?? new Date().toISOString()),
        })
        hydratedResults[k] = {
          result: toToolExecResponse(runs[0]),
          priorResults: runs.slice(1).map(toToolExecResponse),
        }
      }
      setStepState(hydratedState)
      setStepResults(hydratedResults)
      setStepArtifacts(storedArtifacts)

      try {
        const processList = await api.processList()
        const activeEntries = Object.values(processList.active_processes ?? {})
        const hasSessionProcess = storedRunningStepKey && activeEntries.some(
          p => p.session_id === sessionId
        )
        if (hasSessionProcess && storedRunningStepKey) {
          hydratedState[storedRunningStepKey] = 'running'
          setRunningStepKey(storedRunningStepKey)
          setStepState({ ...hydratedState })
        } else {
          setRunningStepKey(null)
        }
      } catch {
        // non-fatal: process list unavailable
      }

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

  useEffect(() => {
    if (!runningStepKey) return

    const clearRunning = (key: string) => {
      setRunningStepKey(null)
      setStepState(prev => {
        if (prev[key] !== 'running') return prev
        const next = { ...prev }
        delete next[key]
        return next
      })
    }

    const checkProcesses = (processes: Record<string, { session_id?: string }>) => {
      if (toolRequestInFlight.current) return
      const stillRunning = Object.values(processes).some(p => p.session_id === sessionId)
      if (!stillRunning) clearRunning(runningStepKey)
    }

    // Use the structured SSE stream — no polling fallback needed.
    // /api/processes/stream emits { processes: { [pid]: { session_id, ... } } }
    // and sends a keepalive comment when nothing changes, so the connection
    // stays alive through proxies without any extra polling.
    let source: EventSource | null = null
    try {
      source = api.processesStream()

      source.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as { processes?: Record<string, { session_id?: string }> }
          if (data.processes && typeof data.processes === 'object') {
            checkProcesses(data.processes)
          }
        } catch {
          // malformed frame — ignore
        }
      }

      source.onerror = () => {
        // SSE connection dropped — close and let the effect re-run if
        // runningStepKey is still set (React will re-execute the effect
        // on the next render that touches its deps).
        source?.close()
        source = null
      }
    } catch {
      // EventSource not supported — nothing we can do without polling,
      // but this environment always has it.
    }

    return () => {
      source?.close()
    }
  }, [runningStepKey, sessionId])

  function analyzeSession() {
    if (!session) return
    const label = `AI Analysis — ${session.target}`
    setAnalyzeLoading(true)
    reportGenStart(label)
    const run = async () => {
      try {
        const res = await api.analyzeSession(session.session_id)
        if (!res.success) {
          reportGenError(label, res.error ?? 'Analysis failed.')
          return
        }
        reportGenDone(label, res.saved_path ?? 'notes/analysis/')
        // Refresh session so risk_level badge updates
        await loadSession()
      } catch (e) {
        reportGenError(label, String(e))
      } finally {
        setAnalyzeLoading(false)
      }
    }
    run()
  }

  function followUpSession() {
    if (!session) return
    const label = `AI Follow-up — ${session.target}`
    setFollowUpLoading(true)
    reportGenStart(label)
    const run = async () => {
      try {
        const res = await api.followUpSession(session.session_id)
        if (!res.success) {
          reportGenError(label, res.error ?? 'Follow-up failed.')
          return
        }
        reportGenDone(label, res.saved_path ?? 'notes/follow-up/')
      } catch (e) {
        reportGenError(label, String(e))
      } finally {
        setFollowUpLoading(false)
      }
    }
    run()
  }

  async function completeSession() {
    if (!session) return
    setCompleteLoading(true)
    try {
      await api.updateSession(session.session_id, { status: 'completed' })
      onBack()
    } catch (e) {
      pushToast('error', `Complete failed: ${String(e)}`)
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
      pushToast('error', `Delete failed: ${String(e)}`)
    } finally {
      setDeleteLoading(false)
      setShowDeleteConfirm(false)
    }
  }

  function exportToolLogs() {
    if (!session) return
    try {
      const meta = (session.metadata ?? {}) as Record<string, unknown>
      const storedStatus = (meta.tool_status && typeof meta.tool_status === 'object')
        ? (meta.tool_status as Record<string, string>)
        : {}
      const storedResults = (meta.step_results && typeof meta.step_results === 'object')
        ? (meta.step_results as Record<string, unknown>)
        : {}

      const logs = steps.map((step, index) => {
        const stepKey = `${session.session_id}:${index}`
        const liveResult = stepResults[stepKey]?.result
        const livePriors = stepResults[stepKey]?.priorResults ?? []
        // Normalise persisted runs (newest-first array, or legacy single object)
        const persistedRuns = normalizePersistedResults(storedResults[stepKey])
        const persistedLatest = persistedRuns[0] ?? null

        const toResultShape = (r: ToolExecResponse) => ({
          success: r.success,
          return_code: r.return_code,
          execution_time: r.execution_time,
          timestamp: r.timestamp,
          stdout: r.stdout,
          stderr: r.stderr,
          timed_out: r.timed_out,
          partial_results: r.partial_results,
        })
        const toPersistedShape = (v: PersistedStepResult) => ({
          success: v.success,
          return_code: v.return_code,
          execution_time: v.execution_time,
          timestamp: v.timestamp ?? '',
          stdout: v.stdout ?? '',
          stderr: v.stderr ?? '',
          timed_out: false,
          partial_results: false,
        })

        const result = liveResult ? toResultShape(liveResult) : (persistedLatest ? toPersistedShape(persistedLatest) : null)
        const prior_results = livePriors.length > 0
          ? livePriors.map(toResultShape)
          : persistedRuns.slice(1).map(toPersistedShape)

        return {
          step_index: index,
          step_key: stepKey,
          tool: step.tool,
          parameters: step.parameters ?? {},
          status: stepState[stepKey] ?? storedStatus[stepKey] ?? 'idle',
          result,
          prior_results,
        }
      })

      const payload = {
        session_id: session.session_id,
        target: session.target,
        status: session.status ?? 'active',
        exported_at: new Date().toISOString(),
        logs,
      }

      const content = JSON.stringify(payload, null, 2)
      const blob = new Blob([content], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${session.session_id}_tool_logs.json`
      a.click()
      URL.revokeObjectURL(url)
      pushToast('success', 'Tool logs exported')
    } catch (e) {
      pushToast('error', `Export failed: ${String(e)}`)
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
      pushToast('success', `Template created: ${name}`)
    } catch (e) {
      setTemplateError(String(e))
    }
  }

  const selectedStep = steps[selectedStepIndex] ?? null
  const selectedStepKey = selectedStep && session ? `${session.session_id}:${selectedStepIndex}` : null
  const selectedResult = selectedStepKey ? stepResults[selectedStepKey] : undefined
  const selectedTool = selectedStep ? toolMap[selectedStep.tool] : null
  const selectedStepValuesReady = !!(selectedStepKey && stepFieldValues[selectedStepKey])
  const selectedDefaultValues = useMemo(() => {
    if (!session || !selectedStep || !selectedTool) return {}
    return buildInitialFieldValues(selectedTool, selectedStep, targetValue.trim() || session.target)
  }, [session, selectedStep, selectedTool, targetValue])
  const selectedFieldValues = selectedStepKey ? (stepFieldValues[selectedStepKey] ?? {}) : {}

  const chainSuggestion = (() => {
    if (!session || !selectedTool || !selectedStepKey || !selectedStep || !selectedStepValuesReady) return null
    return buildStepChainSuggestion({
      steps,
      selectedStepIndex,
      selectedTool,
      sessionId: session.session_id,
      target: targetValue.trim() || session.target,
      stepResults,
      stepArtifacts,
      currentValues: selectedFieldValues,
      baselineValues: selectedDefaultValues,
      preferences: chainPreferences,
    })
  })()

  useEffect(() => {
    if (!chainSuggestion || !selectedStepKey) {
      setSelectedChainFields({})
      return
    }
    setSelectedChainFields(prev => {
      const next: Record<string, boolean> = {}
      for (const field of chainSuggestion.fields) {
        next[field.param] = prev[field.param] ?? true
      }
      return next
    })
  }, [chainSuggestion, selectedStepKey])

  function applyChainSuggestion() {
    if (!selectedStepKey || !chainSuggestion) return
    const chosen = chainSuggestion.fields.filter(field => selectedChainFields[field.param] !== false)
    if (chosen.length === 0) {
      pushToast('info', 'No chain fields selected')
      return
    }
    const updates = Object.fromEntries(chosen.map(field => [field.param, field.value]))
    setStepFieldValues(prev => ({
      ...prev,
      [selectedStepKey]: {
        ...(prev[selectedStepKey] ?? {}),
        ...updates,
      },
    }))
    pushToast('success', `Applied ${chosen.length} chained field${chosen.length === 1 ? '' : 's'} from ${chainSuggestion.sourceTool}`)
  }

  function setChainFieldSelected(param: string, enabled: boolean) {
    setSelectedChainFields(prev => ({ ...prev, [param]: enabled }))
  }

  function pinChainField(param: string) {
    if (!selectedTool || !chainSuggestion) return
    const field = chainSuggestion.fields.find(f => f.param === param)
    if (!field) return
    const preference: ChainMappingPreference = {
      targetTool: selectedTool.name,
      param,
      sourceTool: field.sourceTool,
      sourceArtifact: field.sourceArtifact,
    }
    setChainPreferences(prev => {
      const next = prev.filter(item => !(item.targetTool === preference.targetTool && item.param === preference.param))
      next.push(preference)
      return next
    })
    pushToast('success', `Pinned mapping ${selectedTool.name}.${param} -> ${field.sourceTool}/${field.sourceArtifact}`)
  }

  function removePinnedPreference(index: number) {
    setChainPreferences(prev => prev.filter((_, i) => i !== index))
    pushToast('success', 'Pinned mapping removed')
  }

  function clearPinnedPreferences() {
    setChainPreferences([])
    pushToast('success', 'Cleared all pinned mappings')
  }

  function handleTargetValueChange(nextTarget: string) {
    setTargetValue(nextTarget)
    if (!session) return

    setStepFieldValues(prev => {
      let anyChanged = false
      const next = { ...prev }

      for (let idx = 0; idx < steps.length; idx += 1) {
        const step = steps[idx]
        const tool = resolveToolForStep(step.tool, tools)
        if (!tool) continue

        const stepKey = `${session.session_id}:${idx}`
        const current = prev[stepKey] ?? buildInitialFieldValues(tool, step, nextTarget, sessionId)
        let stepChanged = false
        const updated = { ...current }

        for (const key of [...Object.keys(tool.params), ...Object.keys(tool.optional)]) {
          const inferred = inferTargetValue(key, nextTarget, sessionId)
          if (inferred === undefined || updated[key] === inferred) continue
          updated[key] = inferred
          stepChanged = true
        }

        if (stepChanged || !prev[stepKey]) {
          next[stepKey] = updated
          anyChanged = true
        }
      }

      return anyChanged ? next : prev
    })
  }

  useEffect(() => {
    if (!session || !selectedStep || !selectedStepKey || !selectedTool) return
    setStepFieldValues(prev => {
      if (prev[selectedStepKey]) return prev
      return {
        ...prev,
        [selectedStepKey]: buildInitialFieldValues(selectedTool, selectedStep, targetValue.trim() || session.target, sessionId),
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
    const fieldValues = stepFieldValues[stepKey] ?? buildInitialFieldValues(tool, step, target || sessionRef.target, sessionId)
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

    const existingMetaBeforeRun = (sessionRef.metadata ?? {}) as Record<string, unknown>
    try {
      await api.updateSession(sessionRef.session_id, {
        metadata: {
          ...existingMetaBeforeRun,
          running_step_key: stepKey,
          running_tool: step.tool,
          running_started_at: new Date().toISOString(),
        },
      })
    } catch {
      // non-fatal
    }

    setRunningStepKey(stepKey)
    setStepState(prev => ({ ...prev, [stepKey]: 'running' }))
    // Capture any current successful result into priorResults before clearing
    setStepResults(prev => {
      const existing = prev[stepKey]
      const prevResult = existing?.result
      const prevPriors = existing?.priorResults ?? []
      const newPriors = prevResult ? [prevResult, ...prevPriors] : prevPriors
      return { ...prev, [stepKey]: { priorResults: newPriors } }
    })
    toolRequestInFlight.current = true
    try {
      const result = await api.runTool(tool.endpoint, payload)
      setStepResults(prev => ({ ...prev, [stepKey]: { result, priorResults: prev[stepKey]?.priorResults ?? [] } }))
      setStepState(prev => ({ ...prev, [stepKey]: result.success ? 'success' : 'failed' }))
      if (onToolRun) onToolRun(step.tool, payload, result)

      const existingMeta = (sessionRef.metadata ?? {}) as Record<string, unknown>
      const existingToolStatus = (existingMeta.tool_status && typeof existingMeta.tool_status === 'object') ? (existingMeta.tool_status as Record<string, string>) : {}
      const existingStepResults = (existingMeta.step_results && typeof existingMeta.step_results === 'object') ? (existingMeta.step_results as Record<string, unknown>) : {}
      const existingArtifacts = (existingMeta.step_artifacts && typeof existingMeta.step_artifacts === 'object') ? (existingMeta.step_artifacts as Record<string, StepArtifacts>) : {}
      const extractedArtifacts = result.success
        ? extractStepArtifacts({ step: { ...step, parameters: payload }, result, target: target || sessionRef.target })
        : undefined
      // Prepend new result to the existing runs array (newest first)
      const previousRuns = normalizePersistedResults(existingStepResults[stepKey])
      const newRunEntry: PersistedStepResult = {
        success: result.success,
        return_code: result.return_code,
        execution_time: result.execution_time,
        timestamp: result.timestamp,
        stdout: result.stdout,
        stderr: result.stderr,
      }
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
            [stepKey]: [newRunEntry, ...previousRuns],
          },
          step_artifacts: extractedArtifacts
            ? {
              ...existingArtifacts,
              [stepKey]: extractedArtifacts,
            }
            : existingArtifacts,
          last_run: {
            step_key: stepKey,
            tool: step.tool,
            success: result.success,
            return_code: result.return_code,
            execution_time: result.execution_time,
            timestamp: result.timestamp,
          },
          running_step_key: null,
          running_tool: null,
          running_started_at: null,
        },
      })
      if (extractedArtifacts) {
        setStepArtifacts(prev => ({ ...prev, [stepKey]: extractedArtifacts }))
      }
      await loadSession()
    } catch (e) {
      setStepResults(prev => ({ ...prev, [stepKey]: { error: String(e), priorResults: prev[stepKey]?.priorResults ?? [] } }))
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      try {
        const existingMeta = (sessionRef.metadata ?? {}) as Record<string, unknown>
        await api.updateSession(sessionRef.session_id, {
          metadata: {
            ...existingMeta,
            running_step_key: null,
            running_tool: null,
            running_started_at: null,
          },
        })
      } catch {
        // non-fatal
      }
    } finally {
      toolRequestInFlight.current = false
      setRunningStepKey(null)
    }
  }

  async function stopRunningStep() {
    const stepKey = runningStepKey
    if (!stepKey) return

    try {
      const payload = await api.processList()
      const active = payload.active_processes ?? {}
      const candidates = Object.values(active)
        .filter(p => p && typeof p.command === 'string' && p.command.trim() !== '')
        .map(p => p.pid)
        .filter((pid): pid is number => typeof pid === 'number')

      if (candidates.length === 0) {
        pushToast('error', 'No active process found to terminate')
        setRunningStepKey(null)
        return
      }

      const pid = Math.max(...candidates)
      await api.terminateProcess(pid)
      
      pushToast('success', `Stopped running process ${pid}`)
      setRunningStepKey(null)
      setStepState(prev => ({ ...prev, [stepKey]: 'failed' }))
      setStepResults(prev => ({
        ...prev,
        [stepKey]: {
          ...(prev[stepKey] ?? {}),
          error: `Process ${pid} terminated by user`,
        },
      }))
      if (session) {
        try {
          const existingMeta = (session.metadata ?? {}) as Record<string, unknown>
          await api.updateSession(session.session_id, {
            metadata: {
              ...existingMeta,
              running_step_key: null,
              running_tool: null,
              running_started_at: null,
            },
          })
        } catch {
          // non-fatal
        }
      }
    } catch (e) {
      pushToast('error', `Stop failed: ${String(e)}`)
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
      pushToast('error', `Add tool failed: ${String(e)}`)
    }
  }

  async function applyAttackChainFromSelectedResult() {
    if (!session || !selectedStepKey || !selectedResult?.result) return

    const result = selectedResult.result
    let parsed: unknown = null
    try {
      parsed = result.stdout ? JSON.parse(result.stdout) : null
    } catch {
      parsed = null
    }

    const payload = (parsed && typeof parsed === 'object') ? (parsed as Record<string, unknown>) : null
    const attackChain = payload?.attack_chain
    const attackStepsRaw = (attackChain && typeof attackChain === 'object')
      ? (attackChain as Record<string, unknown>).steps
      : null
    const attackSteps = Array.isArray(attackStepsRaw)
      ? attackStepsRaw.filter((step): step is AttackChainStep => !!step && typeof step === 'object' && typeof (step as AttackChainStep).tool === 'string')
      : []

    if (attackSteps.length === 0) {
      pushToast('error', 'No attack-chain steps found in result output')
      return
    }

    const existingKey = new Set(steps.map(step => `${step.tool}::${JSON.stringify(step.parameters ?? {})}`))
    const toAdd = attackSteps.filter(step => {
      const key = `${step.tool}::${JSON.stringify(step.parameters ?? {})}`
      if (existingKey.has(key)) return false
      existingKey.add(key)
      return true
    })

    if (toAdd.length === 0) {
      pushToast('error', 'All attack-chain tools are already present in manual execution')
      return
    }

    const nextSteps = [...steps, ...toAdd]
    try {
      await api.updateSession(session.session_id, { workflow_steps: nextSteps })
      await loadSession()
      setSelectedStepIndex(Math.max(0, nextSteps.length - toAdd.length))
      pushToast('success', `Added ${toAdd.length} tool(s) from attack chain`)
    } catch (e) {
      pushToast('error', `Apply attack chain failed: ${String(e)}`)
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
      pushToast('error', `Remove tool failed: ${String(e)}`)
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
          {session.risk_level && session.risk_level !== 'unknown' && (
            <span
              className={`session-risk session-risk--${session.risk_level.toLowerCase()}`}
              title={`Risk level: ${session.risk_level.toLowerCase()}`}
            >
              {session.risk_level.toLowerCase()}
            </span>
          )}
        </div>
        <div className="session-detail-actions">
          <button className="session-action-btn" onClick={() => setShowReportModal(true)}>
            <><FileText size={12} /> Generate Report</>
          </button>
          <button
            className="session-action-btn"
            onClick={analyzeSession}
            disabled={analyzeLoading || !llmAvailable}
            title={!llmAvailable ? 'No LLM configured — start server with -ai or -ai-small' : undefined}
          >
            <Brain size={12} /> {analyzeLoading ? 'Analysing…' : 'Analyze Session'}
          </button>
          <button
            className="session-action-btn"
            onClick={followUpSession}
            disabled={followUpLoading || !llmAvailable}
            title={!llmAvailable ? 'No LLM configured — start server with -ai or -ai-small' : undefined}
          >
            <Brain size={12} /> {followUpLoading ? 'Planning…' : 'AI Follow-up'}
          </button>
          <button className="session-action-btn" onClick={() => setShowTemplateModal(true)}>
            Create Template
          </button>
          <button className="session-action-btn" onClick={exportToolLogs}>
            <Download size={12} /> Export Tool Logs
          </button>
          <button className="session-action-btn" onClick={() => setShowChainPrefModal(true)}>
            Manage Chain Pins ({chainPreferences.length})
          </button>
          {session.status !== 'completed' && <button className="session-complete-btn" onClick={() => setShowCompleteConfirm(true)}>Complete Session</button>}
          <button className="session-delete-btn" onClick={() => setShowDeleteConfirm(true)}>Delete Session</button>
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

        <InformationModal
          isOpen={showChainPrefModal}
          title="Pinned Chain Mappings"
          description="Review, remove, or clear your pinned chain mappings for this session."
          primaryLabel="Clear All"
          secondaryLabel="Close"
          primaryVariant="danger"
          onPrimary={chainPreferences.length > 0 ? clearPinnedPreferences : undefined}
          onSecondary={() => setShowChainPrefModal(false)}
          onClose={() => setShowChainPrefModal(false)}
        >
          {chainPreferences.length === 0 ? (
            <p className="section-meta">No pinned mappings yet.</p>
          ) : (
            <div className="session-chain-pref-list">
              {chainPreferences.map((pref, idx) => (
                <div key={`${pref.targetTool}:${pref.param}:${pref.sourceArtifact}:${idx}`} className="session-chain-pref-row">
                  <div className="session-chain-pref-text">
                    <span className="mono">{pref.targetTool}.{pref.param}</span>
                    <span className="section-meta">{pref.sourceTool ?? 'any tool'} / {pref.sourceArtifact}</span>
                  </div>
                  <button className="session-chain-pin-btn" onClick={() => removePinnedPreference(idx)}>
                    Unpin
                  </button>
                </div>
              ))}
            </div>
          )}
        </InformationModal>
      </section>

      <div className="session-detail-tabs">
        <button
          className={`session-tab-btn${activeTab === 'workflow' ? ' session-tab-btn--active' : ''}`}
          onClick={() => setActiveTab('workflow')}
        >
          Workflow
        </button>
        <button
          className={`session-tab-btn${activeTab === 'findings' ? ' session-tab-btn--active' : ''}`}
          onClick={() => setActiveTab('findings')}
        >
          <Shield size={12} /> Findings ({session.findings?.length ?? session.total_findings})
        </button>
        <button
          className={`session-tab-btn${activeTab === 'notes' ? ' session-tab-btn--active' : ''}`}
          onClick={() => setActiveTab('notes')}
        >
          <FileText size={12} /> Notes
        </button>
        <button
          className={`session-tab-btn${activeTab === 'timeline' ? ' session-tab-btn--active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          <List size={12} /> Timeline
        </button>
      </div>

      {activeTab === 'notes' && <SessionNotes sessionId={session.session_id} initialOpenPath={notesInitialOpenPath} onInitialOpenConsumed={() => setNotesInitialOpenPath(undefined)} />}
      {activeTab === 'findings' && <SessionFindings session={session} onUpdate={loadSession} />}
      {activeTab === 'timeline' && <SessionTimeline session={session} />}

      <SessionReportModal
        isOpen={showReportModal}
        session={session}
        onClose={() => setShowReportModal(false)}
        llmAvailable={llmAvailable}
      />

      {activeTab === 'workflow' && <SessionDetailWorkbench
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
        setTargetValue={handleTargetValueChange}
        stepFieldValues={stepFieldValues}
        setStepFieldValues={setStepFieldValues}
        showOptionalByStep={showOptionalByStep}
        setShowOptionalByStep={setShowOptionalByStep}
        selectedResult={selectedResult}
        chainSuggestion={chainSuggestion}
        selectedChainFields={selectedChainFields}
        onSetChainFieldSelected={setChainFieldSelected}
        onPinChainField={pinChainField}
        onApplyChainSuggestion={applyChainSuggestion}
        onRunStep={runStep}
        onStopRunningStep={stopRunningStep}
        onApplyAttackChainFromResult={applyAttackChainFromSelectedResult}
        onRemoveTool={removeToolFromSession}
        showAddTool={showAddTool}
        setShowAddTool={setShowAddTool}
        addToolSearch={addToolSearch}
        setAddToolSearch={setAddToolSearch}
        addCandidates={addCandidates}
        onAddTool={addToolToSession}
      />}
    </div>
  )
}
