import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import SimpleMDE from 'react-simplemde-editor'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FileText, Edit2, Eye, Trash2, Download, Save } from 'lucide-react'
import { RefreshCw } from 'lucide-react'
import { api } from '../../api'
import type { SessionNote } from '../../api/types'
import 'easymde/dist/easymde.min.css'

type ModalMode = 'view' | 'edit'

export interface NoteModalProps {
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

export function NoteModal({
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
            <div className="session-notes-error">{saveError}</div>
          )}

          {loading ? (
            <p className="section-meta section-meta--padded">Loading…</p>
          ) : mode === 'view' ? (
            <div className="session-notes-read-body note-modal-read-body">
              {content.trim() ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              ) : (
                <p className="notes-empty-text">
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
