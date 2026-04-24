import { useEffect, useRef, useState } from 'react'
import { useSessionsStream } from './useSessionsStream'
import {
  RefreshCw, XCircle, Activity, CheckCircle, Pencil, Trash2, Play, Clock,
  Layers, Target, Info,
} from 'lucide-react'
import {
  api,
  type AttackChainStep,
  type CreateAttackChainResponse,
  type SessionsResponse,
  type SessionTemplate,
  type Tool,
} from '../../api'
import { CollapsibleSection } from '../../components/CollapsibleSection'
import { StatCard } from '../../components/StatCard'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import { InformationModal } from '../../components/InformationModal'
import { useToast } from '../../components/ToastProvider'
import { useEscapeClose } from '../../hooks/useEscapeClose'
import { fmtTs } from '../../shared/utils'
import { START_MODES, type StartMode } from './constants'
import { StartSessionModal, StartSessionSection } from './SessionsSections'
import { SessionCard } from './SessionCard'
import './SessionsPage.css'
import './SessionNotes.css'
import './SessionFindings.css'

interface SessionsPageProps {
  demoData?: { sessions: SessionsResponse }
  onOpenSession: (sessionId: string) => void
}

let sessionsBootstrapped = false
let sessionsCacheData: SessionsResponse | null = null
let sessionsCacheTools: Tool[] = []
let sessionsCacheTemplates: SessionTemplate[] = []
let sessionsCacheSections: {
  showActive: boolean
  showCompleted: boolean
  showTemplates: boolean
} | null = null

export default function SessionsPage({ demoData, onOpenSession }: SessionsPageProps) {
  const { pushToast } = useToast()
  const [data, setData] = useState<SessionsResponse | null>(demoData?.sessions ?? sessionsCacheData)
  const [creatingSession, setCreatingSession] = useState(false)
  const [tools, setTools] = useState<Tool[]>(sessionsCacheTools)
  const [templates, setTemplates] = useState<SessionTemplate[]>(sessionsCacheTemplates)
  const [createMsg, setCreateMsg] = useState<string | null>(null)
  const [templateActionError, setTemplateActionError] = useState<string | null>(null)
  const [templateActionBusyId, setTemplateActionBusyId] = useState<string | null>(null)
  const [pendingDeleteTemplate, setPendingDeleteTemplate] = useState<SessionTemplate | null>(null)
  const [startMode, setStartMode] = useState<StartMode | null>(null)
  const [modalTarget, setModalTarget] = useState('')
  const [modalNote, setModalNote] = useState('')
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [intelligencePrecision, setIntelligencePrecision] = useState<'quick' | 'comprehensive' | 'stealth'>('comprehensive')
  const [modalError, setModalError] = useState<string | null>(null)
  const [pendingPreview, setPendingPreview] = useState<{
    mode: StartMode
    target: string
    note: string
    precision: 'quick' | 'comprehensive' | 'stealth'
    preview: CreateAttackChainResponse
  } | null>(null)
  const [confirmingPreview, setConfirmingPreview] = useState(false)
  const [editingTemplateId, setEditingTemplateId] = useState('')
  const [editTemplateName, setEditTemplateName] = useState('')
  const [editTemplateSteps, setEditTemplateSteps] = useState<AttackChainStep[]>([])
  const [editToolSearch, setEditToolSearch] = useState('')
  const [editTemplateError, setEditTemplateError] = useState<string | null>(null)
  const [savingTemplate, setSavingTemplate] = useState(false)
  const [loading, setLoading] = useState(!demoData && !sessionsBootstrapped)
  const [error, setError] = useState<string | null>(null)
  const [showActiveSessions, setShowActiveSessions] = useState(sessionsCacheSections?.showActive ?? true)
  const [showCompletedSessions, setShowCompletedSessions] = useState(sessionsCacheSections?.showCompleted ?? false)
  const [showCustomTemplates, setShowCustomTemplates] = useState(sessionsCacheSections?.showTemplates ?? true)
  const sectionDefaultsSetRef = useRef(false)
  const templateSectionTouchedRef = useRef(false)

  const { streamStatus } = useSessionsStream({
    enabled: !demoData,
    initialStatus: demoData ? 'polling' : 'streaming',
    onData: sessionsData => {
      setData(sessionsData)
      sessionsCacheData = sessionsData
      setError(null)
    },
    onError: msg => setError(msg),
    onLoadingDone: () => setLoading(false),
  })

  useEscapeClose(Boolean(editingTemplateId), closeTemplateEditor)

  useEffect(() => {
    sessionsCacheSections = {
      showActive: showActiveSessions,
      showCompleted: showCompletedSessions,
      showTemplates: showCustomTemplates,
    }
  }, [showActiveSessions, showCompletedSessions, showCustomTemplates])

  useEffect(() => {
    if (demoData) return
    Promise.all([api.sessions(), api.tools(), api.sessionTemplates()])
      .then(([sessionsData, toolsData, templatesData]) => {
        setData(sessionsData)
        setTools(toolsData.tools ?? [])
        setTemplates(templatesData.templates ?? [])
        sessionsCacheData = sessionsData
        sessionsCacheTools = toolsData.tools ?? []
        sessionsCacheTemplates = templatesData.templates ?? []
        sessionsBootstrapped = true
        setError(null)
      })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [demoData])

  useEffect(() => {
    if (sectionDefaultsSetRef.current || loading || !data) return
    const rawActive = data?.active ?? []
    const activeCount = rawActive.filter(s => (s.status ?? 'active') !== 'completed').length
    setShowActiveSessions(activeCount > 0)
    setShowCustomTemplates(templates.length > 0)
    sectionDefaultsSetRef.current = true
  }, [loading, data, templates.length])

  useEffect(() => {
    if (loading) return
    if (templateSectionTouchedRef.current) return
    if (templates.length > 0) setShowCustomTemplates(true)
  }, [loading, templates.length])

  async function refreshTemplates() {
    if (demoData) return
    const templatesData = await api.sessionTemplates()
    const next = templatesData.templates ?? []
    setTemplates(next)
    sessionsCacheTemplates = next
  }

  function fetchSessions(silent = false) {
    if (demoData) return
    if (!silent) setLoading(true)
    api.sessions()
      .then(sessionsData => {
        setData(sessionsData)
        sessionsCacheData = sessionsData
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

  function openStartModal(mode: StartMode, templateId = '') {
    setStartMode(mode)
    setModalTarget('')
    setModalNote('')
    setSelectedTemplateId(templateId)
    if (mode.key === 'intelligence') {
      setIntelligencePrecision('comprehensive')
    }
    setModalError(null)
  }

  function closeStartModal() {
    setStartMode(null)
    setModalError(null)
    setPendingPreview(null)
  }

  function openTemplateEditor(template: SessionTemplate) {
    setEditingTemplateId(template.template_id)
    setEditTemplateName(template.name)
    setEditTemplateSteps(template.workflow_steps ?? [])
    setEditToolSearch('')
    setEditTemplateError(null)
    setTemplateActionError(null)
  }

  function closeTemplateEditor() {
    setEditingTemplateId('')
    setEditTemplateName('')
    setEditTemplateSteps([])
    setEditToolSearch('')
    setEditTemplateError(null)
  }

  function useTemplate(templateId: string) {
    const mode = START_MODES.find(m => m.key === 'from_template')
    if (!mode) return
    openStartModal(mode, templateId)
  }

  async function deleteTemplate(templateId: string) {
    if (demoData) return
    setTemplateActionBusyId(templateId)
    setTemplateActionError(null)
    try {
      await api.deleteSessionTemplate(templateId)
      setTemplates(prev => prev.filter(t => t.template_id !== templateId))
      if (selectedTemplateId === templateId) setSelectedTemplateId('')
      setCreateMsg('Template deleted.')
      pushToast('success', 'Template deleted')
    } catch (e) {
      const msg = String(e)
      setTemplateActionError(msg)
      pushToast('error', `Delete failed: ${msg}`)
    } finally {
      setTemplateActionBusyId(null)
      setPendingDeleteTemplate(null)
    }
  }

  function addToolToEditedTemplate(toolName: string) {
    setEditTemplateSteps(prev => ([...prev, { tool: toolName, parameters: {} }]))
  }

  function removeToolFromEditedTemplate(index: number) {
    setEditTemplateSteps(prev => prev.filter((_, i) => i !== index))
  }

  async function saveTemplateEdits() {
    if (!editingTemplateId) return
    const name = editTemplateName.trim()
    if (!name) {
      setEditTemplateError('Template name is required')
      pushToast('error', 'Template name is required')
      return
    }
    if (editTemplateSteps.length === 0) {
      setEditTemplateError('Template must include at least one tool')
      pushToast('error', 'Template must include at least one tool')
      return
    }

    setSavingTemplate(true)
    setEditTemplateError(null)
    setTemplateActionError(null)
    try {
      await api.updateSessionTemplate(editingTemplateId, {
        name,
        workflow_steps: editTemplateSteps,
      })
      await refreshTemplates()
      setCreateMsg('Template updated.')
      pushToast('success', 'Template updated')
      closeTemplateEditor()
    } catch (e) {
      const msg = String(e)
      setEditTemplateError(msg)
      pushToast('error', `Save failed: ${msg}`)
    } finally {
      setSavingTemplate(false)
    }
  }

  async function createSessionFromTarget(mode: StartMode, targetValue: string, noteValue: string) {
    if (!targetValue.trim()) {
      setModalError('Target is required')
      pushToast('error', 'Target is required')
      return
    }

    setCreateMsg(null)
    setModalError(null)
    setCreatingSession(true)
    try {
      const target = targetValue.trim()
      let sessionRes
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
          pushToast('error', 'Template is required')
          return
        }
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
      } else if (mode.key === 'ai_recon') {
        const recon = await api.aiReconSession(target)
        if (!recon.success) throw new Error(recon.error ?? 'AI Recon session creation failed')
        sessionRes = await api.createSession({
          target,
          workflow_steps: recon.steps,
          source: 'web',
          objective: 'ai_recon',
          metadata: {
            origin: 'ui/sessions/create',
            mode: 'ai_recon',
            note: noteValue,
            session_name: recon.session_name,
          },
        })
      } else if (mode.key === 'ai_profiling') {
        const profiling = await api.aiProfilingSession(target)
        if (!profiling.success) throw new Error(profiling.error ?? 'AI Profiling session creation failed')
        sessionRes = await api.createSession({
          target,
          workflow_steps: profiling.steps,
          source: 'web',
          objective: 'ai_profiling',
          metadata: {
            origin: 'ui/sessions/create',
            mode: 'ai_profiling',
            note: noteValue,
            session_name: profiling.session_name,
            target_type: profiling.target_type,
          },
        })
      } else if (mode.key === 'ai_vuln') {
        const vuln = await api.aiVulnSession(target)
        if (!vuln.success) throw new Error(vuln.error ?? 'AI Vuln Scan session creation failed')
        sessionRes = await api.createSession({
          target,
          workflow_steps: vuln.steps,
          source: 'web',
          objective: 'ai_vuln',
          metadata: {
            origin: 'ui/sessions/create',
            mode: 'ai_vuln',
            note: noteValue,
            session_name: vuln.session_name,
          },
        })
      } else if (mode.key === 'ai_osint') {
        const osint = await api.aiOsintSession(target)
        if (!osint.success) throw new Error(osint.error ?? 'AI OSINT session creation failed')
        sessionRes = await api.createSession({
          target,
          workflow_steps: osint.steps,
          source: 'web',
          objective: 'ai_osint',
          metadata: {
            origin: 'ui/sessions/create',
            mode: 'ai_osint',
            note: noteValue,
            session_name: osint.session_name,
          },
        })
      } else {
        if (mode.key === 'intelligence') {
          const preview = await api.previewAttackChain(target, intelligencePrecision)
          setPendingPreview({ mode, target, note: noteValue, precision: intelligencePrecision, preview })
          return
        }

        const chain = await api.createAttackChain(target, mode.key)
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
      pushToast('success', `Session created: ${sid}`)
      closeStartModal()
      refresh()
    } catch (e) {
      const msg = String(e)
      setModalError(msg)
      setCreateMsg(msg)
      pushToast('error', `Session start failed: ${msg}`)
    } finally {
      setCreatingSession(false)
    }
  }

  async function confirmIntelligencePreview() {
    if (!pendingPreview) return
    setConfirmingPreview(true)
    setModalError(null)
    try {
      const { mode, target, note, precision, preview } = pendingPreview
      const objective = mode.key === 'intelligence' ? precision : mode.key
      const chain = await api.createAttackChain(target, objective)
      const sessionRes = await api.createSession({
        target,
        workflow_steps: preview.attack_chain.steps,
        source: 'web',
        objective,
        session_id: chain.session_id,
        metadata: {
          origin: 'ui/sessions/create',
          mode: mode.key,
          precision: objective,
          note,
          preview_confirmed: true,
          preview_step_count: preview.attack_chain.steps.length,
        },
      })
      const sid = sessionRes.session.session_id
      pushToast('success', `Session created: ${sid}`)
      setPendingPreview(null)
      closeStartModal()
      refresh()
    } catch (e) {
      const msg = String(e)
      setModalError(msg)
      setCreateMsg(msg)
      pushToast('error', `Session start failed: ${msg}`)
    } finally {
      setConfirmingPreview(false)
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
  const active = rawActive
    .filter(s => (s.status ?? 'active') !== 'completed')
    .sort((a, b) => (b.created_at ?? 0) - (a.created_at ?? 0))
  const completed = [
    ...(data?.completed ?? []),
    ...rawActive.filter(s => (s.status ?? 'active') === 'completed'),
  ]
    .filter((s, idx, arr) => arr.findIndex(x => x.session_id === s.session_id) === idx)
    .sort((a, b) => (b.created_at ?? 0) - (a.created_at ?? 0))
  const allFindings = [...active, ...completed].reduce((sum, s) => sum + s.total_findings, 0)
  const uniqueTargets = new Set([...active, ...completed].map(s => s.target)).size
  const editingTemplate = editingTemplateId ? templates.find(t => t.template_id === editingTemplateId) ?? null : null
  const addToolCandidates = tools
    .filter(tool => {
      if (!editToolSearch.trim()) return true
      const q = editToolSearch.toLowerCase()
      return tool.name.toLowerCase().includes(q)
        || tool.desc.toLowerCase().includes(q)
        || tool.category.toLowerCase().includes(q)
    })
    .slice(0, 16)
  const previewSteps = pendingPreview?.preview.attack_chain.steps ?? []
  const previewRisk = pendingPreview?.preview.attack_chain.risk_level ?? 'unknown'
  const previewEstimatedTime = pendingPreview?.preview.attack_chain.estimated_time ?? 0
  const previewTools = Array.from(new Set(previewSteps.map(step => step.tool).filter(Boolean)))
  const previewReasons = previewSteps
    .map(step => ({ tool: step.tool, reason: step.selection_reason }))
    .filter(item => !!item.reason)
  const fmtPercent = (n?: number) => (typeof n === 'number' ? `${Math.round(n * 100)}%` : 'n/a')
  const fmtNumber = (n?: number) => (typeof n === 'number' ? n.toFixed(2) : 'n/a')

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

      {startMode && !pendingPreview && (
        <StartSessionModal
          startMode={startMode}
          templates={templates}
          selectedTemplateId={selectedTemplateId}
          setSelectedTemplateId={setSelectedTemplateId}
          intelligencePrecision={intelligencePrecision}
          setIntelligencePrecision={setIntelligencePrecision}
          modalTarget={modalTarget}
          setModalTarget={setModalTarget}
          modalNote={modalNote}
          setModalNote={setModalNote}
          modalError={modalError}
          creatingSession={creatingSession || confirmingPreview}
          submitLabel={startMode.key === 'intelligence' ? 'Preview Attack Chain' : undefined}
          onClose={closeStartModal}
          onSubmit={() => createSessionFromTarget(startMode, modalTarget, modalNote)}
        />
      )}

      <InformationModal
        isOpen={!!pendingPreview}
        title="Review Intelligence Preview"
        description={pendingPreview
          ? `This preview generated a session workflow for ${pendingPreview.target}. Confirm to persist the session.`
          : ''}
        className="modal--wide intelligence-preview-modal"
        primaryLabel="Create Session from Preview"
        secondaryLabel="Back"
        isPrimaryBusy={confirmingPreview}
        onPrimary={confirmIntelligencePreview}
        onSecondary={() => setPendingPreview(null)}
        onClose={() => {
          if (!confirmingPreview) setPendingPreview(null)
        }}
      >
        <div className="intelligence-preview-summary">
          <p className="intelligence-preview-line"><span className="intelligence-preview-label">Objective:</span> <span className="mono">{pendingPreview?.precision ?? 'n/a'}</span></p>
          <p className="intelligence-preview-line"><span className="intelligence-preview-label">Steps:</span> <span className="mono">{previewSteps.length}</span></p>
          <p className="intelligence-preview-line"><span className="intelligence-preview-label">Unique tools:</span> <span className="mono">{previewTools.length}</span></p>
          <p className="intelligence-preview-line"><span className="intelligence-preview-label">Risk:</span> <span className="mono">{previewRisk}</span></p>
          <p className="intelligence-preview-line"><span className="intelligence-preview-label">Estimated time:</span> <span className="mono">{previewEstimatedTime}s</span></p>
        </div>

        <div className="modal-section">
          <span className="modal-label">Tools to be added</span>
          <div className="modal-params">
            {previewTools.map(tool => (
              <span key={tool} className="modal-param mono">{tool}</span>
            ))}
          </div>
        </div>

        {previewReasons.length > 0 && (
          <div className="modal-section">
            <span className="modal-label">Why selected</span>
            <div className="intelligence-preview-reasons">
              {previewReasons.map((item, idx) => (
                <details key={`${item.tool}:${idx}`} className="intelligence-reason-item">
                  <summary className="intelligence-reason-summary">
                    <span className="intelligence-reason-tool mono">{item.tool}</span>
                    <span className="intelligence-reason-meta mono">{fmtPercent(item.reason?.effective_score)} match</span>
                    <span className="intelligence-reason-toggle">Details</span>
                  </summary>
                  <div className="intelligence-reason-body">
                    <p className="intelligence-preview-line">
                      <span className="intelligence-preview-label">Reason:</span>
                      {item.reason?.summary ?? 'Selected by precision planner.'}
                    </p>
                    <p className="intelligence-preview-line">
                      <span className="intelligence-preview-label">Score:</span>
                      <span className="mono">{fmtPercent(item.reason?.effective_score)}</span>
                    </p>
                    <p className="intelligence-preview-line">
                      <span className="intelligence-preview-label">Noise:</span>
                      <span className="mono">{fmtNumber(item.reason?.noise_score)}</span>
                    </p>
                    <p className="intelligence-preview-line">
                      <span className="intelligence-preview-label">Objective match:</span>
                      <span className="mono">{item.reason?.objective_match ? 'yes' : 'no'}</span>
                    </p>

                    {(item.reason?.new_capabilities_added?.length ?? 0) > 0 && (
                      <div className="intelligence-reason-tags">
                        <span className="intelligence-preview-label">New coverage:</span>
                        {(item.reason?.new_capabilities_added ?? []).map(cap => (
                          <span key={`${item.tool}:${cap}:new`} className="modal-param mono">{cap}</span>
                        ))}
                      </div>
                    )}

                    {(item.reason?.covers_required?.length ?? 0) > 0 && (
                      <div className="intelligence-reason-tags">
                        <span className="intelligence-preview-label">Required capability fit:</span>
                        {(item.reason?.covers_required ?? []).map(cap => (
                          <span key={`${item.tool}:${cap}:req`} className="modal-param mono">{cap}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </details>
              ))}
            </div>
          </div>
        )}

      </InformationModal>

      <CollapsibleSection
        title={<>Active Sessions</>}
        badge={<span className="badge">{active.length}</span>}
        open={showActiveSessions}
        onToggle={setShowActiveSessions}
        headerRight={(
          <div className="sessions-header-actions">
            <span className={`sessions-stream-status sessions-stream-status--${streamStatus}`}>
              {streamStatus === 'streaming' ? 'Live' : streamStatus === 'polling' ? 'Polling' : 'Offline'}
            </span>
          </div>
        )}
      >
        {active.length === 0 ? (
          <div className="tasks-empty">
            <Layers size={28} color="var(--text-dim)" />
            <p>No active sessions. Start a session from target to run tools manually.</p>
          </div>
        ) : (
          <div className="sessions-grid">
            {active.map(session => <SessionCard key={session.session_id} session={session} onOpen={onOpenSession} />)}
          </div>
        )}
        <div className="section-meta session-list-footer-tip">
          <Info size={12} />
          Call MCP tool <span className="mono">handover_session("&lt;session_id&gt;", "optional note")</span> to continue the session with AI.
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title={<>Completed Sessions</>}
        badge={<span className="badge">{completed.length}</span>}
        open={showCompletedSessions}
        onToggle={setShowCompletedSessions}
      >
        {completed.length === 0 ? (
          <div className="tasks-empty">
            <Layers size={28} color="var(--text-dim)" />
            <p>No completed sessions yet.</p>
          </div>
        ) : (
          <div className="sessions-grid">
            {completed.map(session => <SessionCard key={session.session_id} session={session} onOpen={onOpenSession} />)}
          </div>
        )}
      </CollapsibleSection>

      <CollapsibleSection
        title={<>Custom Templates</>}
        badge={<span className="badge">{templates.length}</span>}
        open={showCustomTemplates}
        onToggle={v => {
          templateSectionTouchedRef.current = true
          setShowCustomTemplates(v)
        }}
      >
        {templateActionError && <div className="run-error">{templateActionError}</div>}

        {templates.length === 0 ? (
          <div className="tasks-empty">
            <Layers size={28} color="var(--text-dim)" />
            <p>No custom templates yet. Open a session and click Create Template.</p>
          </div>
        ) : (
          <div className="sessions-grid">
            {templates.map(template => (
              <div key={template.template_id} className="session-card session-card--compact template-session-card">
                <div className="session-card-header">
                  <div className="session-target">
                    <Layers size={13} color="var(--blue)" />
                    <span className="mono">{template.name}</span>
                  </div>
                  <span className="session-tool-chip mono">Custom Template</span>
                </div>

                <div className="session-card-meta">
                  <span><Activity size={11} /> {template.workflow_steps.length} tools</span>
                  <span><Clock size={11} /> {fmtTs(template.updated_at)}</span>
                </div>

                <div className="session-tools">
                  {template.workflow_steps.slice(0, 7).map((step, idx) => (
                    <span key={`${template.template_id}:${idx}:${step.tool}`} className="session-tool-chip">
                      {step.tool}
                    </span>
                  ))}
                  {template.workflow_steps.length > 7 && (
                    <span className="session-tool-chip">+{template.workflow_steps.length - 7}</span>
                  )}
                </div>

                <div className="session-card-footer">
                  <div className="template-card-actions">
                    <button className="session-action-btn" onClick={() => useTemplate(template.template_id)}>
                      <Play size={12} /> Use
                    </button>
                    <button className="session-action-btn" onClick={() => openTemplateEditor(template)}>
                      <Pencil size={12} /> Edit
                    </button>
                    <button
                      className="session-delete-btn"
                      onClick={() => setPendingDeleteTemplate(template)}
                      disabled={templateActionBusyId === template.template_id}
                    >
                      <Trash2 size={12} /> {templateActionBusyId === template.template_id ? 'Deleting…' : 'Delete'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>

      {editingTemplate && (
        <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) closeTemplateEditor() }}>
          <div className="modal modal--wide">
            <div className="modal-header">
              <div className="modal-title-row">
                <span className="modal-name">Edit Template</span>
              </div>
              <button className="modal-close" onClick={closeTemplateEditor}>x</button>
            </div>
            <div className="modal-body">
              <div className="session-start-form">
                <label className="mono" htmlFor="template-name-input">Template name *</label>
                <input
                  id="template-name-input"
                  className="search-input mono"
                  value={editTemplateName}
                  onChange={e => setEditTemplateName(e.target.value)}
                  placeholder="Template name"
                />
              </div>

              <div className="template-editor-grid">
                <div className="template-editor-col">
                  <span className="modal-label">Tools in template</span>
                  {editTemplateSteps.length === 0 ? (
                    <div className="tasks-empty tasks-empty--compact">
                      <p>No tools selected yet.</p>
                    </div>
                  ) : (
                    <div className="template-step-list">
                      {editTemplateSteps.map((step, idx) => (
                        <div key={`${step.tool}:${idx}`} className="template-step-row">
                          <span className="mono">{step.tool}</span>
                          <button className="session-remove-tool" onClick={() => removeToolFromEditedTemplate(idx)}>x</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="template-editor-col">
                  <span className="modal-label">Add tools</span>
                  <input
                    className="search-input mono"
                    value={editToolSearch}
                    onChange={e => setEditToolSearch(e.target.value)}
                    placeholder="Search tools"
                  />
                  <div className="session-add-tool-list">
                    {addToolCandidates.map(tool => (
                      <button
                        key={`edit-template-tool:${tool.name}`}
                        className="session-add-tool-item"
                        onClick={() => addToolToEditedTemplate(tool.name)}
                      >
                        <span className="mono">{tool.name}</span>
                        <span>{tool.category}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {editTemplateError && <div className="run-error">{editTemplateError}</div>}

              <div className="session-start-actions">
                <button className="session-action-btn" onClick={closeTemplateEditor}>Cancel</button>
                <button className="session-run-btn" onClick={saveTemplateEdits} disabled={savingTemplate}>
                  {savingTemplate ? <RefreshCw size={13} className="spin" /> : <Pencil size={13} />}
                  {savingTemplate ? 'Saving…' : 'Save Template'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <ConfirmActionModal
        isOpen={!!pendingDeleteTemplate}
        title="Delete Template"
        description={pendingDeleteTemplate
          ? `Delete template "${pendingDeleteTemplate.name}"? This action cannot be undone.`
          : 'Delete template?'}
        impactItems={pendingDeleteTemplate
          ? [
            `Template ID: ${pendingDeleteTemplate.template_id}`,
            `Tools in template: ${pendingDeleteTemplate.workflow_steps.length}`,
            'Future sessions can no longer use this template',
          ]
          : []}
        confirmLabel="Yes, delete template"
        cancelLabel="Keep template"
        confirmVariant="danger"
        isConfirming={!!pendingDeleteTemplate && templateActionBusyId === pendingDeleteTemplate.template_id}
        onConfirm={async () => {
          if (!pendingDeleteTemplate) return
          await deleteTemplate(pendingDeleteTemplate.template_id)
        }}
        onClose={() => {
          if (!templateActionBusyId) setPendingDeleteTemplate(null)
        }}
      />
    </div>
  )
}
