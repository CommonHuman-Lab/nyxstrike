import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { FileText, Upload, AlertTriangle } from 'lucide-react'
import { api } from '../../api'
import { formatBytes } from '../../shared/utils'

function slugify(raw: string): string {
  return raw
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-zA-Z0-9_\-]/g, '')
    .slice(0, 120)
}

export interface UploadNoteModalProps {
  sessionId: string
  allFolders: string[]
  onClose: () => void
  onUploaded: () => void
  pushToast: (kind: 'success' | 'error' | 'info', text: string) => void
}

export function UploadNoteModal({
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
                <span className="upload-note-file-size">{formatBytes(file.size)}</span>
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
