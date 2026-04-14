import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import SimpleMDE from 'react-simplemde-editor'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  FileText, Folder, FolderOpen, FolderPlus, Plus, Upload,
  Edit2, Eye, Trash2, Download, X, Save, AlertTriangle,
  ChevronRight, ChevronDown, Search, Pencil, Check, RefreshCw,
} from 'lucide-react'
import { api } from '../../api'
import type { SessionNote, SessionNoteSearchResult } from '../../api/types'
import { fmtTs } from '../../shared/utils'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import { useToast } from '../../components/ToastProvider'
import 'easymde/dist/easymde.min.css'

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtBytes(b: number): string {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / (1024 * 1024)).toFixed(1)} MB`
}

function slugify(raw: string): string {
  return raw
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-zA-Z0-9_\-]/g, '')
    .slice(0, 120)
}

function HighlightMatch({ text, query }: { text: string; query: string }) {
  const q = query.trim()
  if (!q) return <>{text}</>
  const idx = text.toLowerCase().indexOf(q.toLowerCase())
  if (idx === -1) return <>{text}</>
  return (
    <>
      {text.slice(0, idx)}
      <mark className="note-snippet-highlight">{text.slice(idx, idx + q.length)}</mark>
      {text.slice(idx + q.length)}
    </>
  )
}

// ── Note Modal ─────────────────────────────────────────────────────────────────

type ModalMode = 'view' | 'edit'

interface NoteModalProps {
  sessionId: string
  note: SessionNote
  isNew: boolean
  initialMode: ModalMode
  /** All folders available for the folder-change select */
  allFolders: string[]
  onClose: () => void
  onSaved: () => void
  onDelete: (note: SessionNote) => void
  pushToast: (kind: 'success' | 'error' | 'info', text: string) => void
}

function NoteModal({
  sessionId,
  note,
  isNew,
  initialMode,
  allFolders,
  onClose,
  onSaved,
  onDelete,
  pushToast,
}: NoteModalProps) {
  const [mode, setMode] = useState<ModalMode>(initialMode)
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [editorReady, setEditorReady] = useState(false)

  // folder select: starts as note's current folder
  const [selectedFolder, setSelectedFolder] = useState(note.folder ?? '')

  // Load content on mount (skip for brand-new notes)
  useEffect(() => {
    if (isNew) return
    let cancelled = false
    api.sessionNote(sessionId, note.filename, note.folder)
      .then(res => { if (!cancelled) { setContent(res.content); setLoading(false) } })
      .catch(() => {
        if (!cancelled) {
          setLoading(false)
          pushToast('error', `Failed to load ${note.filename}.md`)
        }
      })
    return () => { cancelled = true }
  }, [sessionId, note.filename, note.folder, isNew, pushToast])

  // Escape key closes (unless saving)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !saving) onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [saving, onClose])

  async function save() {
    setSaving(true)
    setSaveError(null)
    try {
      const folderChanged = !isNew && selectedFolder !== (note.folder ?? '')
      if (isNew) {
        await api.createSessionNote(sessionId, note.filename, content, selectedFolder)
        pushToast('success', `${note.filename}.md created`)
      } else if (folderChanged) {
        // Move: create in new folder, delete from old folder
        await api.createSessionNote(sessionId, note.filename, content, selectedFolder)
        await api.deleteSessionNote(sessionId, note.filename, note.folder)
        pushToast('success', `${note.filename}.md moved to ${selectedFolder || 'root'}`)
      } else {
        await api.updateSessionNote(sessionId, note.filename, content, note.folder)
        pushToast('success', `${note.filename}.md saved`)
      }
      onSaved()
      onClose()
    } catch (e) {
      setSaveError(String(e))
    } finally {
      setSaving(false)
    }
  }

  const displayPath = selectedFolder
    ? `${selectedFolder}/${note.filename}.md`
    : `${note.filename}.md`

  const downloadUrl = note.folder
    ? `/api/sessions/${sessionId}/notes/${note.filename}?folder=${encodeURIComponent(note.folder)}&download=1`
    : `/api/sessions/${sessionId}/notes/${note.filename}?download=1`

  return createPortal(
    <div
      className="modal-backdrop note-modal-backdrop"
      onClick={e => { if (e.target === e.currentTarget && !saving) onClose() }}
    >
      <div className="modal note-modal" role="dialog" aria-modal="true" aria-label={displayPath}>
        {/* Header */}
        <div className="modal-header note-modal-header">
          <div className="modal-title-row">
            <span className="note-modal-icon">
              <FileText size={13} />
            </span>
            <span className="modal-name note-modal-name">{displayPath}</span>
          </div>
          <div className="note-modal-header-actions">
            {/* Folder select — only in edit mode and when there are folders */}
            {mode === 'edit' && allFolders.length > 0 && (
              <select
                className="note-modal-folder-select"
                value={selectedFolder}
                onChange={e => setSelectedFolder(e.target.value)}
                disabled={saving}
                title="Move to folder"
              >
                <option value="">/ root</option>
                {allFolders.map(f => (
                  <option key={f} value={f}>{f}/</option>
                ))}
              </select>
            )}

            {mode === 'view' && (
              <button
                className="session-action-btn"
                onClick={() => { setEditorReady(false); setMode('edit') }}
                title="Edit"
              >
                <Edit2 size={12} /> Edit
              </button>
            )}
            {mode === 'edit' && (
              <>
                <button
                  className="session-action-btn session-action-btn--primary"
                  onClick={save}
                  disabled={saving}
                >
                  <Save size={12} /> {saving ? 'Saving…' : 'Save'}
                </button>
                {!isNew && (
                  <button
                    className="session-action-btn"
                    onClick={() => { setSaveError(null); setMode('view') }}
                    disabled={saving}
                    title="Switch to view"
                  >
                    <Eye size={12} /> View
                  </button>
                )}
              </>
            )}
            {!isNew && (
              <>
                <a
                  className="session-action-btn"
                  title="Download"
                  href={downloadUrl}
                  download={`${note.filename}.md`}
                >
                  <Download size={12} />
                </a>
                <button
                  className="session-action-btn session-action-btn--danger"
                  title="Delete"
                  onClick={() => { onClose(); onDelete(note) }}
                  disabled={saving}
                >
                  <Trash2 size={12} />
                </button>
              </>
            )}
            <button
              className="modal-close note-modal-close"
              onClick={onClose}
              disabled={saving}
              title="Close"
            >
              ×
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="note-modal-body">
          {/* Save error stays inline — user must see it without the modal closing */}
          {saveError && (
            <div className="session-notes-error" style={{ marginBottom: 10 }}>{saveError}</div>
          )}

          {loading ? (
            <p className="section-meta" style={{ padding: '20px 0' }}>Loading…</p>
          ) : mode === 'view' ? (
            <div className="session-notes-read-body note-modal-read-body">
              {content.trim() ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              ) : (
                <p style={{ color: 'var(--text-dim)', fontStyle: 'italic', margin: 0 }}>
                  This note is empty. Click Edit to start writing.
                </p>
              )}
            </div>
          ) : (
            <div className="note-modal-editor-wrap">
              {!editorReady && (
                <div className="editor-loading" aria-label="Loading editor…">
                  <RefreshCw size={22} className="spin" color="var(--green)" />
                </div>
              )}
              <div className={editorReady ? 'editor-ready' : undefined}
                   style={editorReady ? undefined : { position: 'absolute', visibility: 'hidden', pointerEvents: 'none', width: '100%' }}>
                <SimpleMDE
                  value={content}
                  onChange={setContent}
                  getMdeInstance={() => setEditorReady(true)}
                  options={{
                    spellChecker: false,
                    autofocus: true,
                    placeholder: 'Write your notes in markdown…',
                    status: ['lines', 'words'],
                    toolbar: [
                      'bold', 'italic', 'heading', '|',
                      'quote', 'unordered-list', 'ordered-list', '|',
                      'link', 'code', 'table', '|',
                      'preview', 'side-by-side', 'fullscreen', '|',
                      'guide',
                    ],
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}

// ── Upload Modal ───────────────────────────────────────────────────────────────

interface UploadNoteModalProps {
  sessionId: string
  allFolders: string[]
  onClose: () => void
  onUploaded: () => void
  pushToast: (kind: 'success' | 'error' | 'info', text: string) => void
}

function UploadNoteModal({
  sessionId,
  allFolders,
  onClose,
  onUploaded,
  pushToast,
}: UploadNoteModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [noteName, setNoteName] = useState('')
  const [folder, setFolder] = useState('')
  const [uploading, setUploading] = useState(false)
  const [conflict, setConflict] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropRef = useRef<HTMLDivElement>(null)

  // Escape closes
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !uploading) onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [uploading, onClose])

  function pickFile(f: File) {
    setFile(f)
    const rawName = f.name.replace(/\.md$/i, '')
    setNoteName(slugify(rawName) || 'uploaded-note')
    setConflict(false)
    setError(null)
  }

  function onFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (f) pickFile(f)
    e.target.value = ''
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0]
    if (f) pickFile(f)
  }

  async function doUpload(overwrite: boolean) {
    if (!file) return
    const name = slugify(noteName) || 'uploaded-note'
    setUploading(true)
    setError(null)
    try {
      const res = await api.uploadSessionNote(sessionId, name, file, overwrite, folder)
      if ('conflict' in res && res.conflict) {
        setConflict(true)
        setUploading(false)
        return
      }
      pushToast('success', `${name}.md uploaded`)
      onUploaded()
      onClose()
    } catch {
      setError('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const effectiveName = (slugify(noteName) || 'uploaded-note') + '.md'

  return createPortal(
    <div
      className="modal-backdrop"
      onClick={e => { if (e.target === e.currentTarget && !uploading) onClose() }}
    >
      <div className="modal upload-note-modal" role="dialog" aria-modal="true" aria-label="Upload note">
        {/* Header */}
        <div className="modal-header upload-note-modal-header">
          <div className="modal-title-row">
            <span className="note-modal-icon"><Upload size={13} /></span>
            <span className="modal-name">Upload note</span>
          </div>
          <button className="modal-close" onClick={onClose} disabled={uploading} title="Close">×</button>
        </div>

        {/* Body */}
        <div className="upload-note-modal-body">

          {/* Drop zone */}
          <div
            ref={dropRef}
            className={`upload-note-dropzone${file ? ' upload-note-dropzone--has-file' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={onDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".md,text/markdown,text/plain"
              style={{ display: 'none' }}
              onChange={onFileInputChange}
            />
            {file ? (
              <div className="upload-note-file-chosen">
                <FileText size={20} />
                <span className="upload-note-file-name">{file.name}</span>
                <span className="upload-note-file-size">{fmtBytes(file.size)}</span>
              </div>
            ) : (
              <div className="upload-note-dropzone-prompt">
                <Upload size={24} style={{ opacity: 0.45 }} />
                <span>Drop a <code>.md</code> file here, or click to browse</span>
              </div>
            )}
          </div>

          {/* Fields — only shown once a file is chosen */}
          {file && (
            <div className="upload-note-fields">
              {/* Note name */}
              <label className="upload-note-field-label">
                Note name
                <div className="upload-note-name-row">
                  <input
                    className="upload-note-name-input"
                    type="text"
                    value={noteName}
                    onChange={e => { setNoteName(e.target.value); setConflict(false); setError(null) }}
                    disabled={uploading}
                    placeholder="note-name"
                  />
                  <span className="upload-note-name-ext">.md</span>
                </div>
                <span className="upload-note-field-hint">
                  Will be saved as <strong>{effectiveName}</strong>
                </span>
              </label>

              {/* Folder */}
              {allFolders.length > 0 && (
                <label className="upload-note-field-label">
                  Folder
                  <select
                    className="note-modal-folder-select upload-note-folder-select"
                    value={folder}
                    onChange={e => { setFolder(e.target.value); setConflict(false) }}
                    disabled={uploading}
                  >
                    <option value="">/ root</option>
                    {allFolders.map(f => (
                      <option key={f} value={f}>{f}/</option>
                    ))}
                  </select>
                </label>
              )}

              {/* Conflict warning */}
              {conflict && (
                <div className="upload-note-conflict">
                  <AlertTriangle size={13} />
                  <span>
                    <strong>{effectiveName}</strong> already exists{folder ? ` in ${folder}/` : ''}. Overwrite?
                  </span>
                </div>
              )}

              {/* Generic error */}
              {error && (
                <div className="upload-note-error">{error}</div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="upload-note-modal-footer">
          <button className="session-action-btn" onClick={onClose} disabled={uploading}>
            Cancel
          </button>
          {conflict ? (
            <button
              className="session-action-btn session-action-btn--danger"
              onClick={() => void doUpload(true)}
              disabled={uploading}
            >
              {uploading ? 'Uploading…' : 'Overwrite'}
            </button>
          ) : (
            <button
              className="session-action-btn session-action-btn--primary"
              onClick={() => void doUpload(false)}
              disabled={!file || uploading}
            >
              {uploading ? 'Uploading…' : 'Upload'}
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

interface OpenModal {
  note: SessionNote
  isNew: boolean
  mode: 'view' | 'edit'
}

interface DeleteFolderTarget {
  folder: string
  noteCount: number
}

export function SessionNotes({ sessionId, initialOpenPath, onInitialOpenConsumed }: { sessionId: string; initialOpenPath?: string; onInitialOpenConsumed?: () => void }) {
  const { pushToast } = useToast()

  const [notes, setNotes] = useState<SessionNote[]>([])
  const [folders, setFolders] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  // which folders are expanded in the accordion (Set of folder names)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  // which folder context to use when creating a new note ('' = root)
  const [newNoteFolder, setNewNoteFolder] = useState('')

  // search
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SessionNoteSearchResult[] | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // modal
  const [openModal, setOpenModal] = useState<OpenModal | null>(null)

  // new note creation
  const [showNewInput, setShowNewInput] = useState(false)
  const [newNoteName, setNewNoteName] = useState('')
  const [newNoteError, setNewNoteError] = useState<string | null>(null)
  const newNoteInputRef = useRef<HTMLInputElement>(null)

  // new folder creation
  const [showNewFolderInput, setShowNewFolderInput] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [newFolderError, setNewFolderError] = useState<string | null>(null)
  const [creatingFolder, setCreatingFolder] = useState(false)
  const newFolderInputRef = useRef<HTMLInputElement>(null)

  // delete note confirm
  const [deleteTarget, setDeleteTarget] = useState<SessionNote | null>(null)
  const [deleting, setDeleting] = useState(false)

  // delete folder confirm
  const [deleteFolderTarget, setDeleteFolderTarget] = useState<DeleteFolderTarget | null>(null)
  const [deletingFolder, setDeletingFolder] = useState(false)

  // inline folder rename
  const [renamingFolder, setRenamingFolder] = useState<string | null>(null)
  const [renameDraft, setRenameDraft] = useState('')
  const [renameError, setRenameError] = useState<string | null>(null)
  const [renameSaving, setRenameSaving] = useState(false)
  const renameInputRef = useRef<HTMLInputElement>(null)

  // upload modal
  const [showUploadModal, setShowUploadModal] = useState(false)

  // ── Data loading ───────────────────────────────────────────────────────────

  const loadNotes = useCallback(async () => {
    try {
      const [notesRes, foldersRes] = await Promise.all([
        api.sessionNotes(sessionId),
        api.sessionNoteFolders(sessionId),
      ])
      setNotes(notesRes.notes)
      setFolders(foldersRes.folders ?? [])
    } catch {
      pushToast('error', 'Failed to load notes')
    } finally {
      setLoading(false)
    }
  }, [sessionId, pushToast])

  useEffect(() => { loadNotes() }, [loadNotes])

  // When a saved report path is passed from outside (via bubble click), wait
  // until notes have loaded then open that note automatically.
  useEffect(() => {
    if (!initialOpenPath || loading || notes.length === 0) return
    // initialOpenPath: "reports/report-ai-2026-04-13" (folder/filename, no ext)
    const slashIdx = initialOpenPath.indexOf('/')
    const folder = slashIdx !== -1 ? initialOpenPath.slice(0, slashIdx) : ''
    const filename = slashIdx !== -1 ? initialOpenPath.slice(slashIdx + 1) : initialOpenPath
    const found = notes.find(n => n.filename === filename && (n.folder ?? '') === folder)
    if (found) {
      setOpenModal({ note: found, isNew: false, mode: 'view' })
      if (folder) setExpandedFolders(prev => new Set([...prev, folder]))
      onInitialOpenConsumed?.()
    }
  }, [initialOpenPath, loading, notes, onInitialOpenConsumed])

  useEffect(() => {
    if (showNewInput) setTimeout(() => newNoteInputRef.current?.focus(), 50)
  }, [showNewInput])

  useEffect(() => {
    if (showNewFolderInput) setTimeout(() => newFolderInputRef.current?.focus(), 50)
  }, [showNewFolderInput])

  // ── Derived data ───────────────────────────────────────────────────────────

  const allFolders = useMemo(() => {
    const seen = new Set<string>(folders)
    for (const n of notes) {
      if (n.folder) seen.add(n.folder)
    }
    return Array.from(seen).sort()
  }, [notes, folders])

  const rootNotes = useMemo(
    () => notes.filter(n => !n.folder),
    [notes]
  )

  const notesByFolder = useMemo(() => {
    const map: Record<string, SessionNote[]> = {}
    for (const n of notes) {
      if (n.folder) {
        if (!map[n.folder]) map[n.folder] = []
        map[n.folder].push(n)
      }
    }
    return map
  }, [notes])

  // When searching: flat list across all folders filtered by query
  // (populated by the debounced server search effect below)

  const noteCount = useMemo(() => notes.length, [notes])

  // ── Debounced server-side search ───────────────────────────────────────────

  useEffect(() => {
    const q = searchQuery.trim()
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    if (q.length < 2) {
      setSearchResults(null)
      setSearchLoading(false)
      return
    }
    setSearchLoading(true)
    searchTimerRef.current = setTimeout(async () => {
      try {
        const res = await api.searchSessionNotes(sessionId, q)
        setSearchResults(res.results)
      } catch {
        setSearchResults([])
      } finally {
        setSearchLoading(false)
      }
    }, 350)
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    }
  }, [searchQuery, sessionId])

  // ── Toggle folder accordion ────────────────────────────────────────────────

  function toggleFolder(folder: string) {
    setExpandedFolders(prev => {
      const next = new Set(prev)
      if (next.has(folder)) {
        next.delete(folder)
      } else {
        next.add(folder)
      }
      return next
    })
  }

  // ── Open modal ─────────────────────────────────────────────────────────────

  function openNewNoteEditor(name: string) {
    const slug = slugify(name)
    if (!slug) { setNewNoteError('Note name is empty or contains only invalid characters'); return }
    setOpenModal({ note: { filename: slug, folder: newNoteFolder, size: 0, updated_at: 0 }, isNew: true, mode: 'edit' })
    setShowNewInput(false)
    setNewNoteName('')
    setNewNoteError(null)
  }

  function openViewModal(note: SessionNote) {
    setOpenModal({ note, isNew: false, mode: 'view' })
  }

  function openEditModal(note: SessionNote) {
    setOpenModal({ note, isNew: false, mode: 'edit' })
  }

  // ── Create folder ──────────────────────────────────────────────────────────

  async function createFolder(name: string) {
    const slug = slugify(name)
    if (!slug) { setNewFolderError('Folder name is empty or contains only invalid characters'); return }
    setCreatingFolder(true)
    setNewFolderError(null)
    try {
      await api.createSessionNoteFolder(sessionId, slug)
      pushToast('success', `Folder "${slug}" created`)
      setShowNewFolderInput(false)
      setNewFolderName('')
      await loadNotes()
      // Auto-expand newly created folder
      setExpandedFolders(prev => new Set([...prev, slug]))
    } catch (e: unknown) {
      const msg = (e instanceof Error) ? e.message : String(e)
      if (msg.includes('409') || msg.toLowerCase().includes('already exists')) {
        setNewFolderError(`Folder "${slug}" already exists`)
      } else {
        setNewFolderError('Failed to create folder')
      }
    } finally {
      setCreatingFolder(false)
    }
  }

  // ── Rename folder ──────────────────────────────────────────────────────────

  function startRenameFolder(folder: string) {
    setRenamingFolder(folder)
    setRenameDraft(folder)
    setRenameError(null)
    setTimeout(() => renameInputRef.current?.focus(), 50)
  }

  function cancelRenameFolder() {
    setRenamingFolder(null)
    setRenameDraft('')
    setRenameError(null)
  }

  async function confirmRenameFolder() {
    if (!renamingFolder) return
    const slug = slugify(renameDraft)
    if (!slug) { setRenameError('Name is empty or contains only invalid characters'); return }
    if (slug === renamingFolder) { cancelRenameFolder(); return }
    if (allFolders.includes(slug)) { setRenameError(`Folder "${slug}" already exists`); return }
    setRenameSaving(true)
    setRenameError(null)
    try {
      await api.renameSessionNoteFolder(sessionId, renamingFolder, slug)
      pushToast('success', `Folder renamed to "${slug}"`)
      // Update expanded state: keep expanded if it was expanded before
      setExpandedFolders(prev => {
        const next = new Set(prev)
        if (next.has(renamingFolder)) {
          next.delete(renamingFolder)
          next.add(slug)
        }
        return next
      })
      cancelRenameFolder()
      await loadNotes()
    } catch (e: unknown) {
      const msg = (e instanceof Error) ? e.message : String(e)
      if (msg.includes('409') || msg.toLowerCase().includes('already exists')) {
        setRenameError(`Folder "${slug}" already exists`)
      } else {
        setRenameError('Failed to rename folder')
      }
    } finally {
      setRenameSaving(false)
    }
  }

  // ── Delete folder ──────────────────────────────────────────────────────────

  async function confirmDeleteFolder() {
    if (!deleteFolderTarget) return
    setDeletingFolder(true)
    try {
      await api.deleteSessionNoteFolder(sessionId, deleteFolderTarget.folder)
      pushToast('success', `Folder "${deleteFolderTarget.folder}" deleted`)
      setExpandedFolders(prev => {
        const next = new Set(prev)
        next.delete(deleteFolderTarget.folder)
        return next
      })
      setDeleteFolderTarget(null)
      await loadNotes()
    } catch {
      pushToast('error', `Failed to delete folder "${deleteFolderTarget.folder}"`)
    } finally {
      setDeletingFolder(false)
    }
  }

  // ── Delete note ─────────────────────────────────────────────────────────────

  async function confirmDelete() {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await api.deleteSessionNote(sessionId, deleteTarget.filename, deleteTarget.folder)
      pushToast('success', `${deleteTarget.filename}.md deleted`)
      setDeleteTarget(null)
      await loadNotes()
    } catch {
      pushToast('error', `Failed to delete ${deleteTarget.filename}.md`)
    } finally {
      setDeleting(false)
    }
  }

  // ── Note card render helper ────────────────────────────────────────────────

  function renderNoteCard(note: SessionNote & { snippet?: string }, indented = false) {
    const noteKey = `${note.folder}/${note.filename}`
    const downloadUrl = note.folder
      ? `/api/sessions/${sessionId}/notes/${note.filename}?folder=${encodeURIComponent(note.folder)}&download=1`
      : `/api/sessions/${sessionId}/notes/${note.filename}?download=1`
    const snippet = 'snippet' in note ? (note as { snippet: string }).snippet : ''
    return (
      <div
        key={noteKey}
        className={`session-note-card${indented ? ' session-note-card--indented' : ''}`}
        onClick={() => openViewModal(note)}
        style={{ cursor: 'pointer' }}
      >
        <div className="session-note-card-info">
          <span className="session-note-card-name">
            <FileText size={12} />
            {isSearching && note.folder ? (
              <span style={{ color: 'var(--text-dim)', marginRight: 2 }}>{note.folder}/</span>
            ) : null}
            {note.filename}.md
          </span>
          {snippet && (
            <span className="session-note-card-snippet">
              <HighlightMatch text={snippet} query={searchQuery} />
            </span>
          )}
          <span className="session-note-card-meta">
            {fmtBytes(note.size)} · {fmtTs(note.updated_at)}
          </span>
        </div>
        <div className="session-note-card-actions" onClick={e => e.stopPropagation()}>
          <button
            className="session-action-btn"
            title="Edit"
            onClick={() => openEditModal(note)}
          >
            <Edit2 size={12} />
          </button>
          <a
            className="session-action-btn"
            title="Download"
            href={downloadUrl}
            download={`${note.filename}.md`}
          >
            <Download size={12} />
          </a>
          <button
            className="session-action-btn session-action-btn--danger"
            title="Delete"
            onClick={() => setDeleteTarget(note)}
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>
    )
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  const isSearching = searchQuery.trim().length >= 2

  return (
    <div className="session-notes">
      {/* Note modal */}
      {openModal && (
        <NoteModal
          sessionId={sessionId}
          note={openModal.note}
          isNew={openModal.isNew}
          initialMode={openModal.mode}
          allFolders={allFolders}
          onClose={() => setOpenModal(null)}
          onSaved={loadNotes}
          onDelete={note => { setOpenModal(null); setDeleteTarget(note) }}
          pushToast={pushToast}
        />
      )}

      {/* Upload modal */}
      {showUploadModal && (
        <UploadNoteModal
          sessionId={sessionId}
          allFolders={allFolders}
          onClose={() => setShowUploadModal(false)}
          onUploaded={loadNotes}
          pushToast={pushToast}
        />
      )}

      {/* Delete note confirm modal */}
      <ConfirmActionModal
        isOpen={!!deleteTarget}
        title="Delete note"
        description={`Are you sure you want to delete ${deleteTarget?.filename}.md? This cannot be undone.`}
        confirmLabel="Delete"
        confirmVariant="danger"
        isConfirming={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />

      {/* Delete folder confirm modal */}
      <ConfirmActionModal
        isOpen={!!deleteFolderTarget}
        title="Delete folder"
        description={
          deleteFolderTarget
            ? deleteFolderTarget.noteCount > 0
              ? `Delete folder "${deleteFolderTarget.folder}" and all ${deleteFolderTarget.noteCount} note${deleteFolderTarget.noteCount !== 1 ? 's' : ''} inside it? This cannot be undone.`
              : `Delete folder "${deleteFolderTarget.folder}"? This cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        confirmVariant="danger"
        isConfirming={deletingFolder}
        onConfirm={confirmDeleteFolder}
        onClose={() => setDeleteFolderTarget(null)}
      />

      {/* Header row */}
      <div className="session-notes-header">
        <span className="session-notes-count">{noteCount} note{noteCount !== 1 ? 's' : ''}</span>
        <div className="session-notes-header-actions">
          <button
            className="session-action-btn"
            onClick={() => {
              setShowNewFolderInput(false)
              setNewFolderError(null)
              setNewFolderName('')
              setShowNewInput(v => !v)
              setNewNoteError(null)
              setNewNoteName('')
              setNewNoteFolder('')
            }}
          >
            <Plus size={12} /> New Note
          </button>
          <button
            className="session-action-btn"
            onClick={() => {
              setShowNewInput(false)
              setNewNoteError(null)
              setNewNoteName('')
              setShowNewFolderInput(v => !v)
              setNewFolderError(null)
              setNewFolderName('')
            }}
          >
            <FolderPlus size={12} /> New Folder
          </button>
          <button
            className="session-action-btn"
            onClick={() => setShowUploadModal(true)}
          >
            <Upload size={12} /> Upload .md
          </button>
        </div>
      </div>

      {/* Search bar */}
      <div className="session-notes-search-row">
        <Search size={12} className="session-notes-search-icon" />
        <input
          className="session-notes-search-input"
          type="text"
          placeholder="Search notes…"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        {searchQuery && (
          <button className="session-notes-search-clear" onClick={() => setSearchQuery('')} title="Clear search">
            <X size={12} />
          </button>
        )}
      </div>

      {/* New note inline input */}
      {showNewInput && (
        <div className="session-notes-new-row">
          {allFolders.length > 0 && (
            <select
              className="session-notes-folder-select"
              value={newNoteFolder}
              onChange={e => setNewNoteFolder(e.target.value)}
              title="Create note in folder"
            >
              <option value="">/ root</option>
              {allFolders.map(f => (
                <option key={f} value={f}>{f}/</option>
              ))}
            </select>
          )}
          <input
            ref={newNoteInputRef}
            className="session-notes-name-input"
            type="text"
            placeholder="Note title (letters, digits, hyphens, underscores)"
            value={newNoteName}
            onChange={e => setNewNoteName(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') openNewNoteEditor(newNoteName)
              if (e.key === 'Escape') { setShowNewInput(false); setNewNoteName('') }
            }}
          />
          <span className="session-notes-name-ext">.md</span>
          <button
            className="session-action-btn session-action-btn--primary"
            onClick={() => openNewNoteEditor(newNoteName)}
          >
            Create
          </button>
          <button className="session-action-btn" onClick={() => { setShowNewInput(false); setNewNoteName('') }}>
            <X size={12} />
          </button>
          {newNoteError && <span className="session-notes-error-inline">{newNoteError}</span>}
        </div>
      )}

      {/* New folder inline input */}
      {showNewFolderInput && (
        <div className="session-notes-new-row">
          <Folder size={12} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
          <input
            ref={newFolderInputRef}
            className="session-notes-name-input"
            type="text"
            placeholder="Folder name (letters, digits, hyphens, underscores)"
            value={newFolderName}
            onChange={e => setNewFolderName(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') void createFolder(newFolderName)
              if (e.key === 'Escape') { setShowNewFolderInput(false); setNewFolderName('') }
            }}
            disabled={creatingFolder}
          />
          <button
            className="session-action-btn session-action-btn--primary"
            onClick={() => void createFolder(newFolderName)}
            disabled={creatingFolder}
          >
            {creatingFolder ? 'Creating…' : 'Create'}
          </button>
          <button className="session-action-btn" onClick={() => { setShowNewFolderInput(false); setNewFolderName('') }} disabled={creatingFolder}>
            <X size={12} />
          </button>
          {newFolderError && <span className="session-notes-error-inline">{newFolderError}</span>}
        </div>
      )}

      {/* Loading */}
      {loading && <p className="section-meta">Loading notes…</p>}

      {/* Content */}
      {!loading && (
        <div className="session-notes-list">
          {/* Search results — flat, cross-folder, server-side */}
          {isSearching && (
            <>
              {searchLoading ? (
                <p className="section-meta" style={{ padding: '12px 0' }}>Searching…</p>
              ) : searchResults === null || searchResults.length === 0 ? (
                <div className="session-notes-empty">
                  <FileText size={28} color="var(--text-dim)" />
                  <p>No notes match &quot;{searchQuery}&quot;.</p>
                </div>
              ) : (
                searchResults.map(n => renderNoteCard(n, false))
              )}
            </>
          )}

          {/* Normal accordion view */}
          {!isSearching && (
            <>
              {/* Root notes */}
              {rootNotes.map(n => renderNoteCard(n, false))}

              {/* Folder accordions */}
              {allFolders.map(folder => {
                const folderNotes = notesByFolder[folder] ?? []
                const isOpen = expandedFolders.has(folder)
                return (
                  <div key={`folder:${folder}`} className="session-notes-folder-group">
                    {/* Folder header row */}
                    <div
                      className="session-note-folder-row"
                      onClick={() => renamingFolder !== folder && toggleFolder(folder)}
                    >
                      <span className="session-note-folder-chevron">
                        {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      </span>
                      <span className="session-note-folder-icon">
                        {isOpen ? <FolderOpen size={13} /> : <Folder size={13} />}
                      </span>

                      {/* Rename input OR static name */}
                      {renamingFolder === folder ? (
                        <div
                          className="session-note-folder-rename-wrap"
                          onClick={e => e.stopPropagation()}
                        >
                          <input
                            ref={renameInputRef}
                            className="session-note-folder-rename-input"
                            value={renameDraft}
                            onChange={e => { setRenameDraft(e.target.value); setRenameError(null) }}
                            onKeyDown={e => {
                              if (e.key === 'Enter') void confirmRenameFolder()
                              if (e.key === 'Escape') cancelRenameFolder()
                            }}
                            disabled={renameSaving}
                          />
                          <button
                            className="session-action-btn session-action-btn--primary"
                            title="Confirm rename"
                            onClick={() => void confirmRenameFolder()}
                            disabled={renameSaving}
                          >
                            <Check size={11} />
                          </button>
                          <button
                            className="session-action-btn"
                            title="Cancel rename"
                            onClick={cancelRenameFolder}
                            disabled={renameSaving}
                          >
                            <X size={11} />
                          </button>
                          {renameError && (
                            <span className="session-notes-error-inline">{renameError}</span>
                          )}
                        </div>
                      ) : (
                        <>
                          <span className="session-note-folder-name">{folder}</span>
                          {folderNotes.length > 0 && (
                            <span className="session-note-folder-count" title={`${folderNotes.length} note${folderNotes.length !== 1 ? 's' : ''}`}>
                              {folderNotes.length}
                            </span>
                          )}
                          <div
                            className="session-note-folder-actions"
                            onClick={e => e.stopPropagation()}
                          >
                            <button
                              className="session-action-btn"
                              title={`Rename ${folder}`}
                              onClick={() => startRenameFolder(folder)}
                            >
                              <Pencil size={11} />
                            </button>
                            <button
                              className="session-action-btn"
                              title={`New note in ${folder}`}
                              onClick={() => {
                                setNewNoteFolder(folder)
                                setShowNewFolderInput(false)
                                setNewFolderError(null)
                                setNewFolderName('')
                                setShowNewInput(true)
                                setNewNoteError(null)
                                setNewNoteName('')
                                // Expand the folder so the new note appears inside
                                setExpandedFolders(prev => new Set([...prev, folder]))
                              }}
                            >
                              <Plus size={11} />
                            </button>
                            <button
                              className="session-action-btn session-action-btn--danger"
                              title="Delete folder"
                              onClick={() => setDeleteFolderTarget({ folder, noteCount: folderNotes.length })}
                            >
                              <Trash2 size={11} />
                            </button>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Notes inside folder — shown when expanded */}
                    {isOpen && (
                      <div className="session-notes-folder-contents">
                        {folderNotes.length === 0 ? (
                          <p className="session-notes-folder-empty">No notes yet.</p>
                        ) : (
                          folderNotes.map(n => renderNoteCard(n, true))
                        )}
                      </div>
                    )}
                  </div>
                )
              })}

              {/* Empty state */}
              {rootNotes.length === 0 && allFolders.length === 0 && !showNewInput && !showNewFolderInput && (
                <div className="session-notes-empty">
                  <FileText size={28} color="var(--text-dim)" />
                  <p>No notes yet. Create one or upload a .md file.</p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
