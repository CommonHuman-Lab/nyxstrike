import { useCallback, useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import { useToast } from '../../components/ToastProvider'
import {
  Plus, Trash2, Edit2, Search, X, KeyRound, Package, RefreshCw,
  Download, CheckCircle2, Circle, Copy, Check,
} from 'lucide-react'
import { api } from '../../api'
import type {
  Credential, CredentialType, CreateCredentialPayload,
  LootItem, LootType, CreateLootPayload,
} from '../../api'
import './LootPage.css'

// ── Constants ──────────────────────────────────────────────────────────────────

const CRED_TYPES: CredentialType[] = [
  'plaintext', 'hash', 'key', 'token', 'cookie', 'certificate', 'other',
]

const LOOT_TYPES: LootType[] = [
  'flag', 'file', 'config', 'hash', 'key', 'secret', 'screenshot', 'other',
]

// ── Helpers ────────────────────────────────────────────────────────────────────

function parseTags(raw: string): string[] {
  return raw.split(',').map(t => t.trim()).filter(Boolean)
}

function tagsToString(tags?: string[]): string {
  return (tags ?? []).join(', ')
}

// ── Copy Button ────────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button className="finding-icon-btn loot-copy-btn" onClick={handleCopy} title="Copy">
      {copied ? <Check size={12} color="var(--green)" /> : <Copy size={12} />}
    </button>
  )
}

// ── Credential Form ────────────────────────────────────────────────────────────

interface CredFormState {
  type: CredentialType
  username: string
  secret: string
  hash_type: string
  service: string
  host: string
  source_tool: string
  evidence: string
  notes: string
  verified: boolean
  tagsInput: string
}

function credFormFromItem(c: Credential): CredFormState {
  return {
    type: c.type,
    username: c.username ?? '',
    secret: c.secret ?? '',
    hash_type: c.hash_type ?? '',
    service: c.service ?? '',
    host: c.host ?? '',
    source_tool: c.source_tool ?? '',
    evidence: c.evidence ?? '',
    notes: c.notes ?? '',
    verified: c.verified ?? false,
    tagsInput: tagsToString(c.tags),
  }
}

function emptyCredFormState(): CredFormState {
  return {
    type: 'plaintext', username: '', secret: '', hash_type: '',
    service: '', host: '', source_tool: '', evidence: '', notes: '',
    verified: false, tagsInput: '',
  }
}

interface CredFormProps {
  form: CredFormState
  saving: boolean
  error: string | null
  saveLabel: string
  onChange: (key: keyof CredFormState, value: string | boolean) => void
  onSave: () => void
  onCancel: () => void
}

function CredForm({ form, saving, error, saveLabel, onChange, onSave, onCancel }: CredFormProps) {
  return (
    <div className="loot-modal-body">
      <div className="loot-form-row">
        <select
          name="cred-type"
          className="loot-form-select"
          value={form.type}
          onChange={e => onChange('type', e.target.value)}
        >
          {CRED_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <input
          name="cred-username"
          className="loot-form-input"
          placeholder="Username"
          value={form.username}
          onChange={e => onChange('username', e.target.value)}
          autoFocus
        />
      </div>
      <input
        name="cred-secret"
        className="loot-form-input"
        placeholder="Secret / password"
        value={form.secret}
        onChange={e => onChange('secret', e.target.value)}
      />
      <div className="loot-form-row">
        <input
          name="cred-hash-type"
          className="loot-form-input"
          placeholder="Hash type (e.g. NTLM)"
          value={form.hash_type}
          onChange={e => onChange('hash_type', e.target.value)}
        />
        <input
          name="cred-service"
          className="loot-form-input"
          placeholder="Service (e.g. ssh)"
          value={form.service}
          onChange={e => onChange('service', e.target.value)}
        />
        <input
          name="cred-host"
          className="loot-form-input"
          placeholder="Host"
          value={form.host}
          onChange={e => onChange('host', e.target.value)}
        />
      </div>
      <div className="loot-form-row">
        <input
          name="cred-source-tool"
          className="loot-form-input"
          placeholder="Source tool"
          value={form.source_tool}
          onChange={e => onChange('source_tool', e.target.value)}
        />
        <input
          name="cred-tags"
          className="loot-form-input"
          placeholder="Tags (comma separated)"
          value={form.tagsInput}
          onChange={e => onChange('tagsInput', e.target.value)}
        />
      </div>
      <textarea
        name="cred-evidence"
        className="loot-form-textarea"
        placeholder="Evidence"
        rows={3}
        value={form.evidence}
        onChange={e => onChange('evidence', e.target.value)}
      />
      <textarea
        name="cred-notes"
        className="loot-form-textarea"
        placeholder="Notes"
        rows={2}
        value={form.notes}
        onChange={e => onChange('notes', e.target.value)}
      />
      <label className="loot-form-checkbox-row">
        <input
          name="cred-verified"
          type="checkbox"
          checked={form.verified}
          onChange={e => onChange('verified', e.target.checked)}
        />
        <span>Verified</span>
      </label>
      {error && <div className="loot-form-error">{error}</div>}
      <div className="loot-form-actions">
        <button
          className="session-action-btn session-action-btn--primary"
          onClick={onSave}
          disabled={saving}
        >
          {saving ? 'Saving…' : saveLabel}
        </button>
        <button className="session-action-btn" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </div>
  )
}

// ── Loot Form ──────────────────────────────────────────────────────────────────

interface LootFormState {
  loot_type: LootType
  title: string
  content: string
  path: string
  host: string
  source_tool: string
  notes: string
  tagsInput: string
}

function lootFormFromItem(item: LootItem): LootFormState {
  return {
    loot_type: item.loot_type,
    title: item.title,
    content: item.content ?? '',
    path: item.path ?? '',
    host: item.host ?? '',
    source_tool: item.source_tool ?? '',
    notes: item.notes ?? '',
    tagsInput: tagsToString(item.tags),
  }
}

function emptyLootFormState(): LootFormState {
  return {
    loot_type: 'other', title: '', content: '', path: '',
    host: '', source_tool: '', notes: '', tagsInput: '',
  }
}

interface LootFormProps {
  form: LootFormState
  saving: boolean
  error: string | null
  saveLabel: string
  onChange: (key: keyof LootFormState, value: string) => void
  onSave: () => void
  onCancel: () => void
}

function LootForm({ form, saving, error, saveLabel, onChange, onSave, onCancel }: LootFormProps) {
  const isScreenshot = form.loot_type === 'screenshot'

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      onChange('content', reader.result as string)
      if (!form.title) onChange('title', file.name)
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="loot-modal-body">
      <div className="loot-form-row">
        <select
          name="loot-type"
          className="loot-form-select"
          value={form.loot_type}
          onChange={e => onChange('loot_type', e.target.value)}
        >
          {LOOT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <input
          name="loot-title"
          className="loot-form-input"
          placeholder="Title *"
          value={form.title}
          onChange={e => onChange('title', e.target.value)}
          autoFocus
        />
      </div>
      {isScreenshot ? (
        <div className="loot-screenshot-upload">
          <label className="loot-screenshot-label">
            <input
              name="loot-screenshot"
              type="file"
              accept="image/*"
              className="loot-screenshot-file-input"
              onChange={handleFileChange}
            />
            {form.content
              ? <img src={form.content} alt="preview" className="loot-screenshot-preview" />
              : <span className="loot-screenshot-placeholder">Click to upload screenshot (PNG, JPG, GIF…)</span>
            }
          </label>
          {form.content && (
            <button
              type="button"
              className="session-action-btn loot-screenshot-clear"
              onClick={() => onChange('content', '')}
            >
              Remove image
            </button>
          )}
        </div>
      ) : (
        <textarea
          name="loot-content"
          className="loot-form-textarea"
          placeholder="Content"
          rows={4}
          value={form.content}
          onChange={e => onChange('content', e.target.value)}
        />
      )}
      <div className="loot-form-row">
        <input
          name="loot-path"
          className="loot-form-input"
          placeholder="Path"
          value={form.path}
          onChange={e => onChange('path', e.target.value)}
        />
        <input
          name="loot-host"
          className="loot-form-input"
          placeholder="Host"
          value={form.host}
          onChange={e => onChange('host', e.target.value)}
        />
        <input
          name="loot-source-tool"
          className="loot-form-input"
          placeholder="Source tool"
          value={form.source_tool}
          onChange={e => onChange('source_tool', e.target.value)}
        />
      </div>
      <div className="loot-form-row">
        <input
          name="loot-tags"
          className="loot-form-input"
          placeholder="Tags (comma separated)"
          value={form.tagsInput}
          onChange={e => onChange('tagsInput', e.target.value)}
        />
      </div>
      <textarea
        name="loot-notes"
        className="loot-form-textarea"
        placeholder="Notes"
        rows={2}
        value={form.notes}
        onChange={e => onChange('notes', e.target.value)}
      />
      {error && <div className="loot-form-error">{error}</div>}
      <div className="loot-form-actions">
        <button
          className="session-action-btn session-action-btn--primary"
          onClick={onSave}
          disabled={saving}
        >
          {saving ? 'Saving…' : saveLabel}
        </button>
        <button className="session-action-btn" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </div>
  )
}

// ── Credential Modal ───────────────────────────────────────────────────────────

interface CredModalProps {
  item?: Credential
  saving: boolean
  error: string | null
  onSave: (form: CredFormState) => void
  onClose: () => void
}

function CredModal({ item, saving, error, onSave, onClose }: CredModalProps) {
  const [form, setForm] = useState<CredFormState>(
    item ? credFormFromItem(item) : emptyCredFormState()
  )

  function handleChange(key: keyof CredFormState, value: string | boolean) {
    setForm(p => ({ ...p, [key]: value }))
  }

  return createPortal(
    <div
      className="modal-backdrop loot-modal-backdrop"
      onClick={e => { if (e.target === e.currentTarget && !saving) onClose() }}
    >
      <div className="modal loot-modal" role="dialog" aria-modal="true">
        <div className="modal-header loot-modal-header">
          <div className="modal-title-row">
            <KeyRound size={13} />
            <span className="modal-name">{item ? 'Edit Credential' : 'Add Credential'}</span>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}>×</button>
        </div>
        <CredForm
          form={form}
          saving={saving}
          error={error}
          saveLabel={item ? 'Save Changes' : 'Add Credential'}
          onChange={handleChange}
          onSave={() => onSave(form)}
          onCancel={onClose}
        />
      </div>
    </div>,
    document.body
  )
}

// ── Loot Modal ─────────────────────────────────────────────────────────────────

interface LootModalProps {
  item?: LootItem
  saving: boolean
  error: string | null
  onSave: (form: LootFormState) => void
  onClose: () => void
}

function LootModal({ item, saving, error, onSave, onClose }: LootModalProps) {
  const [form, setForm] = useState<LootFormState>(
    item ? lootFormFromItem(item) : emptyLootFormState()
  )

  function handleChange(key: keyof LootFormState, value: string) {
    setForm(p => ({ ...p, [key]: value }))
  }

  return createPortal(
    <div
      className="modal-backdrop loot-modal-backdrop"
      onClick={e => { if (e.target === e.currentTarget && !saving) onClose() }}
    >
      <div className="modal loot-modal" role="dialog" aria-modal="true">
        <div className="modal-header loot-modal-header">
          <div className="modal-title-row">
            <Package size={13} />
            <span className="modal-name">{item ? 'Edit Loot' : 'Add Loot'}</span>
          </div>
          <button className="modal-close" onClick={onClose} disabled={saving}>×</button>
        </div>
        <LootForm
          form={form}
          saving={saving}
          error={error}
          saveLabel={item ? 'Save Changes' : 'Add Loot'}
          onChange={handleChange}
          onSave={() => onSave(form)}
          onCancel={onClose}
        />
      </div>
    </div>,
    document.body
  )
}

// ── Credentials Tab ────────────────────────────────────────────────────────────

function CredentialsTab() {
  const { pushToast } = useToast()
  const [items, setItems] = useState<Credential[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState<CredentialType | 'all'>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Credential | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<Credential | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.credentials()
      setItems(res.credentials)
    } catch (e) {
      pushToast('error', `Failed to load credentials: ${e}`)
    } finally {
      setLoading(false)
    }
  }, [pushToast])

  useEffect(() => { load() }, [load])

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase()
    let base = filterType === 'all' ? items : items.filter(c => c.type === filterType)
    if (q) {
      base = base.filter(c =>
        (c.username ?? '').toLowerCase().includes(q) ||
        (c.service ?? '').toLowerCase().includes(q) ||
        (c.host ?? '').toLowerCase().includes(q) ||
        (c.source_tool ?? '').toLowerCase().includes(q) ||
        (c.tags ?? []).some(t => t.toLowerCase().includes(q))
      )
    }
    return base
  }, [items, filterType, search])

  // group by type
  const byType = useMemo(() => {
    const groups: Record<string, Credential[]> = {}
    for (const item of visible) {
      groups[item.type] = groups[item.type] ?? []
      groups[item.type].push(item)
    }
    return groups
  }, [visible])

  async function handleSave(form: CredFormState) {
    if (!form.secret && !form.username) { setSaveError('Username or secret is required'); return }
    setSaving(true)
    setSaveError(null)
    try {
      const payload: CreateCredentialPayload = {
        type: form.type,
        username: form.username || undefined,
        secret: form.secret || undefined,
        hash_type: form.hash_type || undefined,
        service: form.service || undefined,
        host: form.host || undefined,
        source_tool: form.source_tool || undefined,
        evidence: form.evidence || undefined,
        notes: form.notes || undefined,
        verified: form.verified,
        tags: parseTags(form.tagsInput),
      }
      if (editing) {
        await api.updateCredential(editing.cred_id, payload)
        setEditing(null)
        pushToast('success', 'Credential updated')
      } else {
        await api.createCredential(payload)
        setModalOpen(false)
        pushToast('success', 'Credential added')
      }
      await load()
    } catch (e) {
      setSaveError(String(e))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(credId: string) {
    setDeletingId(credId)
    try {
      await api.deleteCredential(credId)
      pushToast('success', 'Credential deleted')
      await load()
    } catch (e) {
      pushToast('error', `Delete failed: ${e}`)
    } finally {
      setDeletingId(null)
    }
  }

  const typeCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const item of items) c[item.type] = (c[item.type] ?? 0) + 1
    return c
  }, [items])

  return (
    <div className="loot-tab-content">
      {/* Modals */}
      {modalOpen && (
        <CredModal
          saving={saving}
          error={saveError}
          onSave={handleSave}
          onClose={() => { setModalOpen(false); setSaveError(null) }}
        />
      )}
      {editing && (
        <CredModal
          item={editing}
          saving={saving}
          error={saveError}
          onSave={handleSave}
          onClose={() => { setEditing(null); setSaveError(null) }}
        />
      )}
      <ConfirmActionModal
        isOpen={confirmDelete !== null}
        title="Delete Credential"
        description={`Delete credential${confirmDelete?.username ? ` for "${confirmDelete.username}"` : ''}? This cannot be undone.`}
        confirmLabel="Delete"
        confirmVariant="danger"
        isConfirming={deletingId !== null}
        onConfirm={async () => {
          if (confirmDelete) {
            await handleDelete(confirmDelete.cred_id)
            setConfirmDelete(null)
          }
        }}
        onClose={() => setConfirmDelete(null)}
      />

      {/* Header */}
      <div className="loot-tab-header">
        <div className="loot-filter-row">
          <button
            className={`loot-filter-btn${filterType === 'all' ? ' loot-filter-btn--active' : ''}`}
            onClick={() => setFilterType('all')}
          >
            All ({items.length})
          </button>
          {CRED_TYPES.map(t => {
            const count = typeCounts[t] ?? 0
            if (!count) return null
            return (
              <button
                key={t}
                className={`loot-filter-btn${filterType === t ? ' loot-filter-btn--active' : ''}`}
                onClick={() => setFilterType(filterType === t ? 'all' : t)}
              >
                {t} ({count})
              </button>
            )
          })}
        </div>
        <div className="loot-header-actions">
          <button className="session-action-btn" onClick={load} title="Refresh" disabled={loading}>
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
          </button>
          <a className="session-action-btn" href={api.exportCredentialsUrl()} download title="Export CSV">
            <Download size={12} /> Export
          </a>
          <button
            className="session-action-btn session-action-btn--primary"
            onClick={() => { setModalOpen(true); setSaveError(null) }}
          >
            <Plus size={12} /> Add Credential
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="loot-search-row">
        <Search size={12} className="loot-search-icon" />
        <input
          className="loot-search-input"
          type="text"
          placeholder="Search credentials…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {search && (
          <button className="loot-search-clear" onClick={() => setSearch('')} title="Clear">
            <X size={12} />
          </button>
        )}
      </div>

      {loading && items.length === 0 && (
        <div className="loot-loading">
          <RefreshCw size={18} className="spin" />
        </div>
      )}

      {!loading && visible.length === 0 && (
        <div className="loot-empty">No credentials recorded yet.</div>
      )}

      {Object.entries(byType).map(([type, group]) => (
        <div key={type} className="loot-group">
          <div className="loot-group-header">
            <span className={`loot-type-badge loot-type-badge--${type}`}>{type}</span>
            <span className="section-meta">{group.length} item{group.length !== 1 ? 's' : ''}</span>
          </div>
          {group.map(cred => (
            <div key={cred.cred_id} className="loot-card">
              <div className="loot-card-header">
                <div className="loot-card-title">
                  <KeyRound size={12} className="loot-card-icon" />
                  <span className="loot-card-name mono">
                    {cred.username ? `${cred.username}` : '—'}
                    {cred.service && <span className="loot-card-service"> @ {cred.service}</span>}
                    {cred.host && <span className="loot-card-host"> ({cred.host})</span>}
                  </span>
                  {cred.verified
                    ? <span title="Verified"><CheckCircle2 size={12} className="loot-verified-icon" /></span>
                    : <span title="Not verified"><Circle size={12} className="loot-unverified-icon" /></span>
                  }
                  {cred.tags && cred.tags.map(tag => (
                    <span key={tag} className="loot-tag-badge">{tag}</span>
                  ))}
                </div>
                <div className="loot-card-actions">
                  <button
                    className="finding-icon-btn"
                    title="Edit"
                    onClick={() => { setEditing(cred); setSaveError(null) }}
                  >
                    <Edit2 size={12} />
                  </button>
                  <button
                    className="finding-icon-btn finding-icon-btn--danger"
                    title="Delete"
                    disabled={deletingId === cred.cred_id}
                    onClick={() => setConfirmDelete(cred)}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
              {cred.secret && (
                <div className="loot-card-secret-wrap">
                  <pre className="loot-card-secret mono">{cred.secret}</pre>
                  <CopyButton text={cred.secret} />
                </div>
              )}
              <div className="loot-card-meta">
                {cred.hash_type && <span className="loot-meta-item mono">hash: {cred.hash_type}</span>}
                {cred.source_tool && <span className="loot-meta-item mono">tool: {cred.source_tool}</span>}
              </div>
              {cred.notes && <p className="loot-card-notes">{cred.notes}</p>}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

// ── Loot Tab ───────────────────────────────────────────────────────────────────

function LootTab() {
  const { pushToast } = useToast()
  const [items, setItems] = useState<LootItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState<LootType | 'all'>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<LootItem | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<LootItem | null>(null)
  const [lightbox, setLightbox] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.loot()
      setItems(res.loot)
    } catch (e) {
      pushToast('error', `Failed to load loot: ${e}`)
    } finally {
      setLoading(false)
    }
  }, [pushToast])

  useEffect(() => { load() }, [load])

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase()
    let base = filterType === 'all' ? items : items.filter(c => c.loot_type === filterType)
    if (q) {
      base = base.filter(c =>
        c.title.toLowerCase().includes(q) ||
        (c.content ?? '').toLowerCase().includes(q) ||
        (c.host ?? '').toLowerCase().includes(q) ||
        (c.source_tool ?? '').toLowerCase().includes(q) ||
        (c.tags ?? []).some(t => t.toLowerCase().includes(q))
      )
    }
    return base
  }, [items, filterType, search])

  const byType = useMemo(() => {
    const groups: Record<string, LootItem[]> = {}
    for (const item of visible) {
      groups[item.loot_type] = groups[item.loot_type] ?? []
      groups[item.loot_type].push(item)
    }
    return groups
  }, [visible])

  async function handleSave(form: LootFormState) {
    if (!form.title.trim()) { setSaveError('Title is required'); return }
    setSaving(true)
    setSaveError(null)
    try {
      const payload: CreateLootPayload = {
        loot_type: form.loot_type,
        title: form.title,
        content: form.content || null,
        path: form.path || undefined,
        host: form.host || undefined,
        source_tool: form.source_tool || undefined,
        notes: form.notes || undefined,
        tags: parseTags(form.tagsInput),
      }
      if (editing) {
        await api.updateLoot(editing.loot_id, payload)
        setEditing(null)
        pushToast('success', 'Loot updated')
      } else {
        await api.createLoot(payload)
        setModalOpen(false)
        pushToast('success', 'Loot added')
      }
      await load()
    } catch (e) {
      setSaveError(String(e))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(lootId: string) {
    setDeletingId(lootId)
    try {
      await api.deleteLoot(lootId)
      pushToast('success', 'Loot deleted')
      await load()
    } catch (e) {
      pushToast('error', `Delete failed: ${e}`)
    } finally {
      setDeletingId(null)
    }
  }

  const typeCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const item of items) c[item.loot_type] = (c[item.loot_type] ?? 0) + 1
    return c
  }, [items])

  return (
    <div className="loot-tab-content">
      {modalOpen && (
        <LootModal
          saving={saving}
          error={saveError}
          onSave={handleSave}
          onClose={() => { setModalOpen(false); setSaveError(null) }}
        />
      )}
      {editing && (
        <LootModal
          item={editing}
          saving={saving}
          error={saveError}
          onSave={handleSave}
          onClose={() => { setEditing(null); setSaveError(null) }}
        />
      )}
      <ConfirmActionModal
        isOpen={confirmDelete !== null}
        title="Delete Loot"
        description={`Delete "${confirmDelete?.title ?? 'this item'}"? This cannot be undone.`}
        confirmLabel="Delete"
        confirmVariant="danger"
        isConfirming={deletingId !== null}
        onConfirm={async () => {
          if (confirmDelete) {
            await handleDelete(confirmDelete.loot_id)
            setConfirmDelete(null)
          }
        }}
        onClose={() => setConfirmDelete(null)}
      />

      <div className="loot-tab-header">
        <div className="loot-filter-row">
          <button
            className={`loot-filter-btn${filterType === 'all' ? ' loot-filter-btn--active' : ''}`}
            onClick={() => setFilterType('all')}
          >
            All ({items.length})
          </button>
          {LOOT_TYPES.map(t => {
            const count = typeCounts[t] ?? 0
            if (!count) return null
            return (
              <button
                key={t}
                className={`loot-filter-btn${filterType === t ? ' loot-filter-btn--active' : ''}`}
                onClick={() => setFilterType(filterType === t ? 'all' : t)}
              >
                {t} ({count})
              </button>
            )
          })}
        </div>
        <div className="loot-header-actions">
          <button className="session-action-btn" onClick={load} title="Refresh" disabled={loading}>
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
          </button>
          <a className="session-action-btn" href={api.exportLootUrl()} download title="Export CSV">
            <Download size={12} /> Export
          </a>
          <button
            className="session-action-btn session-action-btn--primary"
            onClick={() => { setModalOpen(true); setSaveError(null) }}
          >
            <Plus size={12} /> Add Loot
          </button>
        </div>
      </div>

      <div className="loot-search-row">
        <Search size={12} className="loot-search-icon" />
        <input
          className="loot-search-input"
          type="text"
          placeholder="Search loot…"          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {search && (
          <button className="loot-search-clear" onClick={() => setSearch('')} title="Clear">
            <X size={12} />
          </button>
        )}
      </div>

      {loading && items.length === 0 && (
        <div className="loot-loading">
          <RefreshCw size={18} className="spin" />
        </div>
      )}

      {!loading && visible.length === 0 && (
        <div className="loot-empty">No loot recorded yet.</div>
      )}

      {Object.entries(byType).map(([type, group]) => (
        <div key={type} className="loot-group">
          <div className="loot-group-header">
            <span className={`loot-type-badge loot-type-badge--${type}`}>{type}</span>
            <span className="section-meta">{group.length} item{group.length !== 1 ? 's' : ''}</span>
          </div>
          {group.map(item => (
            <div key={item.loot_id} className="loot-card">
              <div className="loot-card-header">
                <div className="loot-card-title">
                  <Package size={12} className="loot-card-icon" />
                  <span className="loot-card-name">{item.title}</span>
                  {item.host && <span className="loot-card-host">({item.host})</span>}
                  {item.tags && item.tags.map(tag => (
                    <span key={tag} className="loot-tag-badge">{tag}</span>
                  ))}
                </div>
                <div className="loot-card-actions">
                  <button
                    className="finding-icon-btn"
                    title="Edit"
                    onClick={() => { setEditing(item); setSaveError(null) }}
                  >
                    <Edit2 size={12} />
                  </button>
                  <button
                    className="finding-icon-btn finding-icon-btn--danger"
                    title="Delete"
                    disabled={deletingId === item.loot_id}
                    onClick={() => setConfirmDelete(item)}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
              {item.content && item.loot_type === 'screenshot' && item.content.startsWith('data:image') ? (
                <div className="loot-screenshot-card" onClick={() => setLightbox(item.content!)}>
                  <img src={item.content} alt={item.title} className="loot-screenshot-thumb" />
                  <span className="loot-screenshot-hint">Click to expand</span>
                </div>
              ) : item.content ? (
                <div className="loot-card-secret-wrap">
                  <pre className="loot-card-secret mono">{item.content}</pre>
                  <CopyButton text={item.content} />
                </div>
              ) : null}
              <div className="loot-card-meta">
                {item.path && <span className="loot-meta-item mono">path: {item.path}</span>}
                {item.source_tool && <span className="loot-meta-item mono">tool: {item.source_tool}</span>}
              </div>
              {item.notes && <p className="loot-card-notes">{item.notes}</p>}
            </div>
          ))}
        </div>
      ))}

      {lightbox && createPortal(
        <div className="loot-lightbox-backdrop" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="screenshot" className="loot-lightbox-img" />
          <button className="loot-lightbox-close" onClick={() => setLightbox(null)} title="Close">×</button>
        </div>,
        document.body
      )}
    </div>
  )
}

// ── LootPage ───────────────────────────────────────────────────────────────────

type Tab = 'credentials' | 'loot'

export function LootPage() {
  const [tab, setTab] = useState<Tab>('credentials')

  return (
    <div className="page-content">
      <div className="loot-page-card">
        <div className="loot-page-header">
          <h1 className="loot-page-title">
            <KeyRound size={16} /> Loot Store
          </h1>
          <p className="loot-page-subtitle section-meta">
            Manage captured credentials and loot from your engagements.
          </p>
        </div>

        <div className="loot-tabs">
          <button
            className={`loot-tab-btn${tab === 'credentials' ? ' loot-tab-btn--active' : ''}`}
            onClick={() => setTab('credentials')}
          >
            <KeyRound size={13} /> Credentials
          </button>
          <button
            className={`loot-tab-btn${tab === 'loot' ? ' loot-tab-btn--active' : ''}`}
            onClick={() => setTab('loot')}
          >
            <Package size={13} /> Loot
          </button>
        </div>

        {tab === 'credentials' && <CredentialsTab />}
        {tab === 'loot' && <LootTab />}
      </div>
    </div>
  )
}

export default LootPage
