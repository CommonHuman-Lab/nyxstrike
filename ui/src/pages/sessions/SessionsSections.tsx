import { Layers, RefreshCw, Target } from 'lucide-react'
import type { KeyboardEvent, ReactNode } from 'react'
import type { SessionSummary } from '../../api'
import { SessionCard } from './SessionCard'
import type { StartMode } from './constants'

export function StartSessionSection({
  startModes,
  onOpenStartMode,
  createMsg,
}: {
  startModes: StartMode[]
  onOpenStartMode: (mode: StartMode) => void
  createMsg: string | null
}) {
  return (
    <section className="section">
      <div className="section-header">
        <h3>Start Session</h3>
        <span className="section-meta">Choose a workflow type, then provide target details.</span>
      </div>
      <div className="registry-grid registry-grid--wider start-mode-grid">
        {startModes.map(mode => (
          <div key={mode.key} className="registry-card registry-card--clickable start-mode-card" onClick={() => onOpenStartMode(mode)}>
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
  )
}

export function SessionListSection({
  title,
  sessions,
  emptyText,
  onOpenSession,
  headerRight,
  onHeaderClick,
}: {
  title: string
  sessions: SessionSummary[]
  emptyText: string
  onOpenSession: (sessionId: string) => void
  headerRight?: ReactNode
  onHeaderClick?: () => void
}) {
  const interactiveHeaderProps = onHeaderClick
    ? {
      role: 'button' as const,
      tabIndex: 0,
      onClick: onHeaderClick,
      onKeyDown: (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onHeaderClick()
        }
      },
    }
    : {}

  return (
    <section className="section">
      <div className={`section-header${onHeaderClick ? ' sessions-collapsed-toggle' : ''}`} {...interactiveHeaderProps}>
        <h3>{title} <span className="badge">{sessions.length}</span></h3>
        {headerRight}
      </div>

      {sessions.length === 0 ? (
        <div className="tasks-empty">
          <Layers size={28} color="var(--text-dim)" />
          <p>{emptyText}</p>
        </div>
      ) : (
        <div className="sessions-grid">
          {sessions.map(session => <SessionCard key={session.session_id} session={session} onOpen={onOpenSession} />)}
        </div>
      )}
    </section>
  )
}

export function StartSessionModal({
  startMode,
  templates,
  selectedTemplateId,
  setSelectedTemplateId,
  modalTarget,
  setModalTarget,
  modalNote,
  setModalNote,
  modalError,
  creatingSession,
  onClose,
  onSubmit,
}: {
  startMode: StartMode
  templates: Array<{ template_id: string; name: string }>
  selectedTemplateId: string
  setSelectedTemplateId: (value: string) => void
  modalTarget: string
  setModalTarget: (value: string) => void
  modalNote: string
  setModalNote: (value: string) => void
  modalError: string | null
  creatingSession: boolean
  onClose: () => void
  onSubmit: () => void
}) {
  return (
    <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-name">Start {startMode.title}</span>
          </div>
          <button className="modal-close" onClick={onClose}>x</button>
        </div>
        <div className="modal-body">
          <p className="modal-desc">{startMode.modalDescription}</p>
          <div className="modal-section">
            <span className="modal-label">Typical Tooling</span>
            <div className="modal-params">
              {startMode.tools.length === 0 && <span className="modal-param mono">none preloaded</span>}
              {startMode.tools.map(tool => (
                <span key={tool} className="modal-param mono">{tool}</span>
              ))}
            </div>
          </div>
          {startMode.key === 'from_template' && (
            <div className="session-start-form">
              <label className="mono">Template *</label>
              <select
                className="session-objective-select"
                value={selectedTemplateId}
                onChange={e => setSelectedTemplateId(e.target.value)}
              >
                <option value="">Select template</option>
                {templates.map(template => (
                  <option key={template.template_id} value={template.template_id}>{template.name}</option>
                ))}
              </select>
            </div>
          )}
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
              <button className="session-action-btn" onClick={onClose}>Cancel</button>
              <button
                className="session-run-btn"
                onClick={onSubmit}
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
  )
}
