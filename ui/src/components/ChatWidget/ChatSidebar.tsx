import { useState, useRef, useEffect } from 'react'
import { Plus, Trash2, MessageSquare } from 'lucide-react'
import { ConfirmActionModal } from '../ConfirmActionModal'
import type { ChatSession } from '../../api'

interface ChatSidebarProps {
  sessions: ChatSession[]
  activeSessionId: string | null
  onSelectSession: (id: string) => void
  onCreateSession: () => void
  onDeleteSession: (id: string) => void
  onDeleteAllSessions: () => void
  onRenameSession: (id: string, name: string) => void
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onDeleteAllSessions,
  onRenameSession,
}: ChatSidebarProps) {
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingId])

  function startEdit(session: ChatSession) {
    setEditingId(session.id)
    setEditValue(session.name || 'New chat')
  }

  function commitEdit() {
    if (editingId && editValue.trim()) {
      onRenameSession(editingId, editValue.trim())
    }
    setEditingId(null)
  }

  function cancelEdit() {
    setEditingId(null)
  }

  return (
    <div className="chat-sidebar">
      <div className="chat-sidebar-header">
        <span className="chat-sidebar-title">Chats</span>
        <button className="chat-new-btn" onClick={onCreateSession} title="New chat">
          <Plus size={14} />
        </button>
      </div>

      <div className="chat-session-list">
        {sessions.length === 0 && (
          <div className="chat-session-empty">No sessions yet</div>
        )}
        {sessions.map(session => (
          <div
            key={session.id}
            className={`chat-session-item${session.id === activeSessionId ? ' active' : ''}`}
            onClick={() => { if (editingId !== session.id) onSelectSession(session.id) }}
            onDoubleClick={e => { e.stopPropagation(); startEdit(session) }}
          >
            <MessageSquare size={12} className="chat-session-icon" />
            {editingId === session.id ? (
              <input
                ref={inputRef}
                className="chat-session-rename-input"
                value={editValue}
                onChange={e => setEditValue(e.target.value)}
                onBlur={commitEdit}
                onKeyDown={e => {
                  if (e.key === 'Enter') commitEdit()
                  if (e.key === 'Escape') cancelEdit()
                }}
                onClick={e => e.stopPropagation()}
              />
            ) : (
              <span className="chat-session-name">
                {session.name || 'New chat'}
              </span>
            )}
            <button
              className="chat-session-delete"
              onClick={e => { e.stopPropagation(); setConfirmDeleteId(session.id) }}
              title="Delete"
            >
              <Trash2 size={11} />
            </button>
          </div>
        ))}
      </div>

      {sessions.length > 0 && (
        <div className="chat-sidebar-footer">
          <button
            className="chat-delete-all-btn"
            onClick={() => setConfirmDeleteAll(true)}
            title="Delete all chats"
          >
            <Trash2 size={11} />
            Delete all
          </button>
        </div>
      )}

      <ConfirmActionModal
        isOpen={confirmDeleteId !== null}
        title="Delete chat?"
        description="This will permanently delete the chat session and all its messages."
        confirmLabel="Delete"
        confirmVariant="danger"
        onConfirm={() => {
          if (confirmDeleteId) onDeleteSession(confirmDeleteId)
          setConfirmDeleteId(null)
        }}
        onClose={() => setConfirmDeleteId(null)}
      />

      <ConfirmActionModal
        isOpen={confirmDeleteAll}
        title="Delete all chats?"
        description="This will permanently delete all chat sessions and their messages. This cannot be undone."
        confirmLabel="Delete all"
        confirmVariant="danger"
        onConfirm={() => {
          onDeleteAllSessions()
          setConfirmDeleteAll(false)
        }}
        onClose={() => setConfirmDeleteAll(false)}
      />
    </div>
  )
}
