import { useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { Plus, Trash2, Edit2, Shield, Search, X } from 'lucide-react'
import { api } from '../../api'
import type { SessionSummary, SessionFinding, CreateFindingPayload } from '../../api'

const SEVERITIES = ['critical', 'high', 'medium', 'low', 'info'] as const
type Severity = typeof SEVERITIES[number]

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
}

const FINDING_STATUSES = ['open', 'confirmed', 'false_positive', 'resolved'] as const

const emptyForm = (): CreateFindingPayload => ({
  title: '',
  severity: 'info',
  description: '',
  tool: '',
  evidence: '',
  recommendation: '',
  cve: '',
  tags: [],
})

// ── Shared Finding Form ────────────────────────────────────────────────────────

interface FindingFormProps {
  title: string
  severity: Severity | string
  status?: string
  description: string
  tool: string
  cve: string
  evidence: string
  recommendation: string
  tagsInput: string
  saving: boolean
  error: string | null
  showStatus?: boolean
  onChange: (key: string, value: string) => void
  onTagsChange: (value: string) => void
  onSave: () => void
  onCancel: () => void
}

function FindingForm({
  title, severity, status, description, tool, cve, evidence, recommendation,
  tagsInput, saving, error, showStatus = false,
  onChange, onTagsChange, onSave, onCancel,
}: FindingFormProps) {
  return (
    <div className="finding-modal-body">
      <div className="findings-form-row">
        <input
          className="findings-form-input"
          placeholder="Title *"
          value={title}
          onChange={e => onChange('title', e.target.value)}
          autoFocus
        />
        <select
          className="findings-form-select"
          value={severity}
          onChange={e => onChange('severity', e.target.value)}
        >
          {SEVERITIES.map(s => <option key={s} value={s}>{SEVERITY_LABEL[s]}</option>)}
        </select>
        {showStatus && (
          <select
            className="findings-form-select"
            value={status ?? 'open'}
            onChange={e => onChange('status', e.target.value)}
          >
            {FINDING_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        )}
      </div>
      <textarea
        className="findings-form-textarea"
        placeholder="Description"
        rows={3}
        value={description}
        onChange={e => onChange('description', e.target.value)}
      />
      <div className="findings-form-row">
        <input
          className="findings-form-input"
          placeholder="Tool (e.g. nmap)"
          value={tool}
          onChange={e => onChange('tool', e.target.value)}
        />
        <input
          className="findings-form-input"
          placeholder="CVE (e.g. CVE-2021-44228)"
          value={cve}
          onChange={e => onChange('cve', e.target.value)}
        />
      </div>
      <textarea
        className="findings-form-textarea"
        placeholder="Evidence / PoC"
        rows={3}
        value={evidence}
        onChange={e => onChange('evidence', e.target.value)}
      />
      <textarea
        className="findings-form-textarea"
        placeholder="Recommendation"
        rows={2}
        value={recommendation}
        onChange={e => onChange('recommendation', e.target.value)}
      />
      <input
        className="findings-form-input"
        placeholder="Tags (comma separated)"
        value={tagsInput}
        onChange={e => onTagsChange(e.target.value)}
      />
      {error && <div className="findings-error">{error}</div>}
      <div className="findings-form-actions">
        <button
          className="session-action-btn session-action-btn--primary"
          onClick={onSave}
          disabled={saving}
        >
          {saving ? 'Saving…' : 'Save Finding'}
        </button>
        <button className="session-action-btn" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </div>
  )
}

// ── Edit Finding Modal ─────────────────────────────────────────────────────────

interface EditFindingModalProps {
  finding: SessionFinding
  saving: boolean
  error: string | null
  onSave: (findingId: string, form: Partial<SessionFinding>) => void
  onClose: () => void
}

function EditFindingModal({ finding, saving, error, onSave, onClose }: EditFindingModalProps) {
  const [form, setForm] = useState<Partial<SessionFinding>>({
    title: finding.title,
    severity: finding.severity,
    description: finding.description ?? '',
    tool: finding.tool ?? '',
    evidence: finding.evidence ?? '',
    recommendation: finding.recommendation ?? '',
    cve: finding.cve ?? '',
    tags: finding.tags ?? [],
    status: finding.status ?? 'open',
  })
  const [tagsInput, setTagsInput] = useState((finding.tags ?? []).join(', '))

  function handleChange(key: string, value: string) {
    setForm(p => ({ ...p, [key]: value }))
  }

  function handleSave() {
    const payload = {
      ...form,
      tags: tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(Boolean) : [],
    }
    onSave(finding.finding_id, payload)
  }

  return createPortal(
    <div
      className="modal-backdrop finding-modal-backdrop"
      onClick={e => { if (e.target === e.currentTarget && !saving) onClose() }}
    >
      <div className="modal finding-modal" role="dialog" aria-modal="true" aria-label="Edit Finding">
        <div className="modal-header finding-modal-header">
          <div className="modal-title-row">
            <Shield size={13} />
            <span className="modal-name">Edit Finding</span>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}>×</button>
        </div>
        <FindingForm
          title={form.title ?? ''}
          severity={form.severity ?? 'info'}
          status={form.status ?? 'open'}
          description={form.description ?? ''}
          tool={form.tool ?? ''}
          cve={form.cve ?? ''}
          evidence={form.evidence ?? ''}
          recommendation={form.recommendation ?? ''}
          tagsInput={tagsInput}
          saving={saving}
          error={error}
          showStatus
          onChange={handleChange}
          onTagsChange={setTagsInput}
          onSave={handleSave}
          onCancel={onClose}
        />
      </div>
    </div>,
    document.body
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export function SessionFindings({
  session,
  onUpdate,
}: {
  session: SessionSummary
  onUpdate?: () => void
}) {
  const findings: SessionFinding[] = session.findings ?? []
  const [filterSev, setFilterSev] = useState<Severity | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<CreateFindingPayload>(emptyForm())
  const [tagsInput, setTagsInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingFinding, setEditingFinding] = useState<SessionFinding | null>(null)
  const [editError, setEditError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const visible = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    let base = filterSev === 'all' ? findings : findings.filter(f => f.severity === filterSev)
    if (q) {
      base = base.filter(f =>
        f.title.toLowerCase().includes(q) ||
        (f.description ?? '').toLowerCase().includes(q) ||
        (f.tool ?? '').toLowerCase().includes(q) ||
        (f.cve ?? '').toLowerCase().includes(q) ||
        (f.tags ?? []).some(t => t.toLowerCase().includes(q))
      )
    }
    return base
  }, [findings, filterSev, searchQuery])

  const bySeverity = SEVERITIES.reduce((acc, sev) => {
    acc[sev] = visible.filter(f => f.severity === sev)
    return acc
  }, {} as Record<Severity, SessionFinding[]>)

  function updateAddForm(key: string, value: string) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  async function saveFinding() {
    if (!form.title.trim()) { setError('Title is required'); return }
    setSaving(true)
    setError(null)
    try {
      const payload: CreateFindingPayload = {
        ...form,
        tags: tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(Boolean) : [],
      }
      await api.addSessionFinding(session.session_id, payload)
      setForm(emptyForm())
      setTagsInput('')
      setShowForm(false)
      onUpdate?.()
    } catch (e) {
      setError(String(e))
    } finally {
      setSaving(false)
    }
  }

  async function saveFindingEdit(findingId: string, editForm: Partial<SessionFinding>) {
    setSaving(true)
    setEditError(null)
    try {
      await api.updateSessionFinding(session.session_id, findingId, editForm)
      setEditingFinding(null)
      onUpdate?.()
    } catch (e) {
      setEditError(String(e))
    } finally {
      setSaving(false)
    }
  }

  async function deleteFinding(findingId: string) {
    setDeletingId(findingId)
    try {
      await api.deleteSessionFinding(session.session_id, findingId)
      onUpdate?.()
    } catch (e) {
      setError(String(e))
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="session-findings">
      {/* Edit finding modal */}
      {editingFinding && (
        <EditFindingModal
          finding={editingFinding}
          saving={saving}
          error={editError}
          onSave={saveFindingEdit}
          onClose={() => { setEditingFinding(null); setEditError(null) }}
        />
      )}

      <div className="session-findings-header">
        <div className="session-findings-filters">
          <button
            className={`findings-filter-btn${filterSev === 'all' ? ' findings-filter-btn--active' : ''}`}
            onClick={() => setFilterSev('all')}
          >
            All ({findings.length})
          </button>
          {SEVERITIES.map(sev => {
            const count = findings.filter(f => f.severity === sev).length
            if (count === 0) return null
            return (
              <button
                key={sev}
                className={`findings-filter-btn findings-filter-btn--${sev}${filterSev === sev ? ' findings-filter-btn--active' : ''}`}
                onClick={() => setFilterSev(sev)}
              >
                {SEVERITY_LABEL[sev]} ({count})
              </button>
            )
          })}
        </div>
        <button className="session-action-btn" onClick={() => { setShowForm(true); setError(null) }}>
          <Plus size={12} /> Add Finding
        </button>
      </div>

      <div className="findings-search-row">
        <Search size={12} className="findings-search-icon" />
        <input
          className="findings-search-input"
          type="text"
          placeholder="Search findings…"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        {searchQuery && (
          <button className="findings-search-clear" onClick={() => setSearchQuery('')} title="Clear search">
            <X size={12} />
          </button>
        )}
      </div>

      {showForm && createPortal(
        <div
          className="modal-backdrop finding-modal-backdrop"
          onClick={e => { if (e.target === e.currentTarget) { setShowForm(false); setError(null) } }}
        >
          <div className="modal finding-modal" role="dialog" aria-modal="true" aria-label="Add Finding">
            <div className="modal-header finding-modal-header">
              <div className="modal-title-row">
                <Shield size={13} />
                <span className="modal-name">Add Finding</span>
              </div>
              <button className="modal-close" onClick={() => { setShowForm(false); setError(null) }}>×</button>
            </div>
            <FindingForm
              title={form.title}
              severity={form.severity}
              description={form.description ?? ''}
              tool={form.tool ?? ''}
              cve={form.cve ?? ''}
              evidence={form.evidence ?? ''}
              recommendation={form.recommendation ?? ''}
              tagsInput={tagsInput}
              saving={saving}
              error={error}
              onChange={updateAddForm}
              onTagsChange={setTagsInput}
              onSave={saveFinding}
              onCancel={() => { setShowForm(false); setError(null) }}
            />
          </div>
        </div>,
        document.body
      )}

      {visible.length === 0 && (
        <div className="findings-empty">
          <p className="section-meta">No findings recorded yet.</p>
        </div>
      )}

      {SEVERITIES.map(sev => {
        const group = bySeverity[sev]
        if (!group.length) return null
        return (
          <div key={sev} className={`findings-group findings-group--${sev}`}>
            <div className="findings-group-header">
              <span className={`findings-severity-badge findings-severity-badge--${sev}`}>
                {SEVERITY_LABEL[sev]}
              </span>
              <span className="section-meta">{group.length} finding{group.length !== 1 ? 's' : ''}</span>
            </div>
            {group.map(f => (
              <div key={f.finding_id} className="finding-card">
                <div className="finding-card-header">
                  <span className="finding-title">{f.title}</span>
                  <span className={`finding-status finding-status--${f.status ?? 'open'}`}>{f.status ?? 'open'}</span>
                  <div className="finding-card-actions">
                    <button
                      className="finding-icon-btn"
                      title="Edit"
                      onClick={() => { setEditingFinding(f); setEditError(null) }}
                    >
                      <Edit2 size={12} />
                    </button>
                    <button
                      className="finding-icon-btn finding-icon-btn--danger"
                      title="Delete"
                      disabled={deletingId === f.finding_id}
                      onClick={() => deleteFinding(f.finding_id)}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
                {f.description && <p className="finding-description">{f.description}</p>}
                <div className="finding-meta">
                  {f.tool && <span className="mono finding-meta-item">tool: {f.tool}</span>}
                  {f.cve && <span className="finding-meta-item finding-cve">{f.cve}</span>}
                  {f.tags && f.tags.length > 0 && f.tags.map(tag => (
                    <span key={tag} className="finding-tag-badge">{tag}</span>
                  ))}
                </div>
                {f.evidence && (
                  <details className="finding-evidence-details">
                    <summary className="finding-evidence-summary">Evidence</summary>
                    <pre className="finding-evidence-pre">{f.evidence}</pre>
                  </details>
                )}
                {f.recommendation && (
                  <div className="finding-recommendation">
                    <strong>Recommendation:</strong> {f.recommendation}
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      })}
    </div>
  )
}
