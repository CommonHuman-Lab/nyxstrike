import { useEffect, useRef, useState } from 'react'
import {
  RefreshCw, XCircle, Activity, CheckCircle, Pencil, Trash2, Play, Clock,
  Layers, Target,
} from 'lucide-react'
import {
  api,
  type AttackChainStep,
  type SessionsResponse,
  type SessionTemplate,
  type Tool,
} from '../../api'
import { StatCard } from '../../components/StatCard'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import { useToast } from '../../components/ToastProvider'
import { fmtTs } from '../../shared/utils'
import { START_MODES, type StartMode } from './constants'
import { SessionListSection, StartSessionModal, StartSessionSection } from './SessionsSections'
import './SessionsPage.css'

interface SessionsPageProps {
  demoData?: { sessions: SessionsResponse }
  onOpenSession: (sessionId: string) => void
}

export default function SessionsPage({ demoData, onOpenSession }: SessionsPageProps) {
  const { pushToast } = useToast()
  const [data, setData] = useState<SessionsResponse | null>(demoData?.sessions ?? null)
  const [creatingSession, setCreatingSession] = useState(false)
  const [tools, setTools] = useState<Tool[]>([])
  const [templates, setTemplates] = useState<SessionTemplate[]>([])
  const [createMsg, setCreateMsg] = useState<string | null>(null)
  const [templateActionError, setTemplateActionError] = useState<string | null>(null)
  const [templateActionBusyId, setTemplateActionBusyId] = useState<string | null>(null)
  const [pendingDeleteTemplate, setPendingDeleteTemplate] = useState<SessionTemplate | null>(null)
  const [startMode, setStartMode] = useState<StartMode | null>(null)
  const [modalTarget, setModalTarget] = useState('')
  const [modalNote, setModalNote] = useState('')
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [modalError, setModalError] = useState<string | null>(null)
  const [editingTemplateId, setEditingTemplateId] = useState('')
  const [editTemplateName, setEditTemplateName] = useState('')
  const [editTemplateSteps, setEditTemplateSteps] = useState<AttackChainStep[]>([])
  const [editToolSearch, setEditToolSearch] = useState('')
  const [editTemplateError, setEditTemplateError] = useState<string | null>(null)
  const [savingTemplate, setSavingTemplate] = useState(false)
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
      .then(([sessionsData, toolsData, templatesData]) => {
        setData(sessionsData)
        setTools(toolsData.tools ?? [])
        setTemplates(templatesData.templates ?? [])
        setError(null)
      })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [demoData])

  async function refreshTemplates() {
    if (demoData) return
    const templatesData = await api.sessionTemplates()
    setTemplates(templatesData.templates ?? [])
  }

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

  function openStartModal(mode: StartMode, templateId = '') {
    setStartMode(mode)
    setModalTarget('')
    setModalNote('')
    setSelectedTemplateId(templateId)
    setModalError(null)
  }

  function closeStartModal() {
    setStartMode(null)
    setModalError(null)
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
          pushToast('error', 'Template is required')
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

      <section className="section">
        <div className="section-header">
          <h3>Custom Templates <span className="badge">{templates.length}</span></h3>
          <span className="section-meta">Reusable user templates for starting sessions quickly.</span>
        </div>

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
                  <span className="session-tool-chip mono">template</span>
                </div>

                <div className="session-card-meta">
                  <span><Activity size={11} /> {template.workflow_steps.length} tools</span>
                  <span><Clock size={11} /> {fmtTs(template.updated_at)}</span>
                </div>

                <div className="session-tools">
                  {template.workflow_steps.map((step, idx) => (
                    <span key={`${template.template_id}:${idx}:${step.tool}`} className="session-tool-chip">
                      {step.tool}
                    </span>
                  ))}
                </div>

                <div className="session-card-footer">
                  <span className="session-id mono">{template.template_id}</span>
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
      </section>

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
