import { useEscapeClose } from '../../hooks/useEscapeClose'

interface TemplateModalProps {
  show: boolean
  templateName: string
  templateError: string | null
  setTemplateName: (value: string) => void
  onClose: () => void
  onSave: () => void
}

export function TemplateModal({
  show,
  templateName,
  templateError,
  setTemplateName,
  onClose,
  onSave,
}: TemplateModalProps) {
  useEscapeClose(show, onClose)

  if (!show) return null

  return (
    <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title-row"><span className="modal-name">Create Template</span></div>
          <button className="modal-close" onClick={onClose}>x</button>
        </div>
        <div className="modal-body">
          <div className="session-start-form">
            <label className="mono">Template Name *</label>
            <input
              className="search-input mono"
              placeholder="e.g. SMB Enumeration Pack"
              value={templateName}
              onChange={e => setTemplateName(e.target.value)}
            />
            {templateError && <div className="run-error">{templateError}</div>}
            <div className="session-start-actions">
              <button className="session-action-btn" onClick={onClose}>Cancel</button>
              <button className="session-run-btn" onClick={onSave}>Save Template</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
