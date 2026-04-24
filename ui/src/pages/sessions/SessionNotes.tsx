import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  FileText, Folder, FolderOpen, FolderPlus, Plus, Upload,
  Edit2, Trash2, Download, X,
  Search, Pencil, Check,
} from 'lucide-react'
import { api } from '../../api'
import type { SessionNote, SessionNoteSearchResult } from '../../api/types'
import { fmtTs, formatBytes } from '../../shared/utils'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import { CollapseChevron } from '../../components/CollapseChevron'
import { useToast } from '../../components/ToastProvider'
import { NoteModal } from './NoteModal'
import { UploadNoteModal } from './UploadNoteModal'
import { useFolderManager } from './useFolderManager'

// ── Helpers ───────────────────────────────────────────────────────────────────

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

// ── Main component ─────────────────────────────────────────────────────────────

interface OpenModal {
  note: SessionNote
  isNew: boolean
  mode: 'view' | 'edit'
}

export function SessionNotes({ sessionId, initialOpenPath, onInitialOpenConsumed }: { sessionId: string; initialOpenPath?: string; onInitialOpenConsumed?: () => void }) {
  const { pushToast } = useToast()

  const [notes, setNotes] = useState<SessionNote[]>([])
  const [folders, setFolders] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

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

  // delete note confirm
  const [deleteTarget, setDeleteTarget] = useState<SessionNote | null>(null)
  const [deleting, setDeleting] = useState(false)

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

  const noteCount = useMemo(() => notes.length, [notes])

  // ── Folder manager ─────────────────────────────────────────────────────────

  const {
    showNewFolderInput, setShowNewFolderInput,
    newFolderName, setNewFolderName,
    newFolderError,
    creatingFolder,
    createFolder,
    renamingFolder,
    renameDraft, setRenameDraft,
    renameError,
    renameSaving,
    startRenameFolder,
    cancelRenameFolder,
    confirmRenameFolder,
    deleteFolderTarget, setDeleteFolderTarget,
    deletingFolder,
    confirmDeleteFolder,
    expandedFolders, setExpandedFolders,
    toggleFolder,
  } = useFolderManager(sessionId, allFolders, loadNotes)

  // ── Focus helpers ──────────────────────────────────────────────────────────

  const newFolderInputRef = useRef<HTMLInputElement>(null)
  const renameInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (showNewInput) setTimeout(() => newNoteInputRef.current?.focus(), 50)
  }, [showNewInput])

  useEffect(() => {
    if (showNewFolderInput) setTimeout(() => newFolderInputRef.current?.focus(), 50)
  }, [showNewFolderInput])

  useEffect(() => {
    if (renamingFolder) setTimeout(() => renameInputRef.current?.focus(), 50)
  }, [renamingFolder])

  // ── When a saved report path is passed from outside ────────────────────────

  useEffect(() => {
    if (!initialOpenPath || loading || notes.length === 0) return
    const slashIdx = initialOpenPath.indexOf('/')
    const folder = slashIdx !== -1 ? initialOpenPath.slice(0, slashIdx) : ''
    const filename = slashIdx !== -1 ? initialOpenPath.slice(slashIdx + 1) : initialOpenPath
    const found = notes.find(n => n.filename === filename && (n.folder ?? '') === folder)
    if (found) {
      setOpenModal({ note: found, isNew: false, mode: 'view' })
      if (folder) setExpandedFolders(prev => new Set([...prev, folder]))
      onInitialOpenConsumed?.()
    }
  }, [initialOpenPath, loading, notes, onInitialOpenConsumed, setExpandedFolders])

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

  const isSearching = searchQuery.trim().length >= 2

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
      >
        <div className="session-note-card-info">
          <span className="session-note-card-name">
            <FileText size={12} />
            {isSearching && note.folder ? (
              <span className="note-folder-prefix">{note.folder}/</span>
            ) : null}
            {note.filename}.md
          </span>
          {snippet && (
            <span className="session-note-card-snippet">
              <HighlightMatch text={snippet} query={searchQuery} />
            </span>
          )}
          <span className="session-note-card-meta">
            {formatBytes(note.size)} · {fmtTs(note.updated_at)}
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
          <Folder size={12} className="session-new-folder-icon" />
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
                <p className="section-meta section-meta--padded">Searching…</p>
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
                        <CollapseChevron open={isOpen} size={12} />
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
                            onChange={e => { setRenameDraft(e.target.value); }}
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
                                setNewFolderName('')
                                setShowNewInput(true)
                                setNewNoteError(null)
                                setNewNoteName('')
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
