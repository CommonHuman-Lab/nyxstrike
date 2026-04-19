import { useState } from 'react'
import { Plus, Trash2, MessageSquare } from 'lucide-react'
import { ConfirmActionModal } from '../ConfirmActionModal'
import type { ChatSession } from '../../api'

interface ChatSidebarProps {
  sessions: ChatSession[]
  activeSessionId: string | null
  onSelectSession: (id: string) => void
  onCreateSession: () => void
  onDeleteSession: (id: string) => void
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}: ChatSidebarProps) {
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

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
            onClick={() => onSelectSession(session.id)}
          >
            <MessageSquare size={12} className="chat-session-icon" />
            <span className="chat-session-name">
              {session.name || 'New chat'}
            </span>
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
    </div>
  )
}
