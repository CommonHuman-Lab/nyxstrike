import { useState, useEffect, useRef, useCallback } from 'react'
import { MessageSquare, ChevronLeft, ChevronRight, ArrowDown } from 'lucide-react'
import { ChatSidebar } from './ChatSidebar'
import { ChatMessageList } from './ChatMessageList'
import { ChatInput } from './ChatInput'
import { useChatSessions } from './useChatSessions'
import { useChatStream } from './useChatStream'
import type { ChatMessage } from './useChatStream'
import './ChatWidget.css'

const OPEN_KEY = 'nyxstrike_chat_open'
const SIZE_KEY = 'nyxstrike_chat_size'
const MIN_W = 280
const MIN_H = 350

function loadOpen(): boolean {
  try { return localStorage.getItem(OPEN_KEY) === '1' } catch { return false }
}
function saveOpen(v: boolean) {
  try { localStorage.setItem(OPEN_KEY, v ? '1' : '0') } catch {}
}
function loadSize(): { w: number; h: number } {
  try {
    const s = JSON.parse(localStorage.getItem(SIZE_KEY) || '{}')
    return { w: Number(s.w) || 460, h: Number(s.h) || 520 }
  } catch { return { w: 460, h: 520 } }
}
function saveSize(w: number, h: number) {
  try { localStorage.setItem(SIZE_KEY, JSON.stringify({ w, h })) } catch {}
}

interface ChatWidgetProps {
  llmAvailable: boolean
  currentPage: string
  currentSessionId: string | null
}

export function ChatWidget({ llmAvailable, currentPage, currentSessionId }: ChatWidgetProps) {
  const [open, setOpen] = useState(loadOpen)
  const [size, setSize] = useState(loadSize)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [prefill, setPrefill] = useState<string>('')

  const { sessions, loading, createSession, deleteSession, deleteAllSessions, updateSessionName, renameSession } = useChatSessions()
  const { messages, streaming, send, stop, loadHistory, clearMessages, confirmToolCall } = useChatStream(activeSessionId)

  const widgetRef = useRef<HTMLDivElement>(null)
  const autoCreatedRef = useRef(false)

  // Keyboard shortcut Ctrl+Shift+C
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'c') {
        e.preventDefault()
        setOpen(prev => {
          saveOpen(!prev)
          return !prev
        })
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // Auto-select most recent session, or create one if none exist
  useEffect(() => {
    if (loading) return
    if (!activeSessionId && sessions.length > 0) {
      setActiveSessionId(sessions[0].id)
    } else if (!activeSessionId && sessions.length === 0 && !autoCreatedRef.current) {
      autoCreatedRef.current = true
      handleCreateSession()
    }
  }, [sessions, activeSessionId, loading]) // eslint-disable-line react-hooks/exhaustive-deps

  // Load history when session changes
  useEffect(() => {
    if (activeSessionId) {
      clearMessages()
      loadHistory(activeSessionId)
    }
  }, [activeSessionId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleCreateSession() {
    const sess = await createSession()
    if (sess) {
      setActiveSessionId(sess.id)
      clearMessages()
    } else {
      autoCreatedRef.current = false
    }
  }

  async function handleDeleteSession(id: string) {
    await deleteSession(id)
    if (activeSessionId === id) {
      const remaining = sessions.filter(s => s.id !== id)
      if (remaining.length > 0) {
        setActiveSessionId(remaining[0].id)
      } else {
        setActiveSessionId(null)
        clearMessages()
      }
    }
  }

  async function handleDeleteAllSessions() {
    await deleteAllSessions()
    setActiveSessionId(null)
    clearMessages()
  }

  function handleSend(text: string) {
    if (!activeSessionId) return
    const ctx = { page: currentPage, session_id: currentSessionId || '' }
    // Auto-name session from first message
    const active = sessions.find(s => s.id === activeSessionId)
    if (active && !active.name) {
      updateSessionName(activeSessionId, text.slice(0, 50))
    }
    send(text, ctx)
  }

  function handleRetry(msg: ChatMessage) {
    // Find the user message just before this error
    const idx = messages.indexOf(msg)
    if (idx > 0 && messages[idx - 1].role === 'user') {
      const original = messages[idx - 1].content
      const ctx = { page: currentPage, session_id: currentSessionId || '' }
      send(original, ctx)
    }
  }

  // Resize drag (top edge and left edge)
  const dragRef = useRef<{ edge: 'top' | 'left'; startX: number; startY: number; startW: number; startH: number } | null>(null)

  const onMouseDown = useCallback((edge: 'top' | 'left') => (e: React.MouseEvent) => {
    e.preventDefault()
    dragRef.current = { edge, startX: e.clientX, startY: e.clientY, startW: size.w, startH: size.h }
  }, [size])

  useEffect(() => {
    function onMove(e: MouseEvent) {
      const d = dragRef.current
      if (!d) return
      let { w, h } = { w: d.startW, h: d.startH }
      if (d.edge === 'top') {
        h = Math.max(MIN_H, d.startH + (d.startY - e.clientY))
      } else {
        w = Math.max(MIN_W, d.startW + (d.startX - e.clientX))
      }
      setSize({ w, h })
      saveSize(w, h)
    }
    function onUp() { dragRef.current = null }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [])

  function toggleOpen() {
    setOpen(prev => { saveOpen(!prev); return !prev })
  }

  if (!llmAvailable) return null

  const activeSession = sessions.find(s => s.id === activeSessionId)
  const sessionLabel = activeSession?.name || (activeSessionId ? 'New chat' : 'Starting…')

  return (
    <>
      {/* FAB */}
      {!open && (
        <button
          className="chat-fab"
          onClick={toggleOpen}
          title="Open chat (Ctrl+Shift+C)"
          aria-label="Open NyxStrike chat"
        >
          <MessageSquare size={14} />
          AI Assistant
        </button>
      )}

      {/* Widget */}
      {open && (
        <div
          ref={widgetRef}
          className="chat-widget"
          style={{ width: size.w, height: size.h }}
        >
          {/* Resize handles */}
          <div className="chat-resize-top" onMouseDown={onMouseDown('top')} />
          <div className="chat-resize-left" onMouseDown={onMouseDown('left')} />

          <div className="chat-layout">
            {/* Sidebar */}
            {sidebarOpen && (
              <ChatSidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                onSelectSession={id => { setActiveSessionId(id) }}
                onCreateSession={handleCreateSession}
                onDeleteSession={handleDeleteSession}
                onDeleteAllSessions={handleDeleteAllSessions}
                onRenameSession={renameSession}
              />
            )}

            {/* Main panel */}
            <div className="chat-main">
              {/* Header */}
              <div className="chat-header">
                <button
                  className="chat-sidebar-toggle"
                  onClick={() => setSidebarOpen(prev => !prev)}
                  title={sidebarOpen ? 'Hide sessions' : 'Show sessions'}
                >
                  {sidebarOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
                </button>
                <div className="chat-header-info">
                  <span className="chat-header-title">NyxStrike AI</span>
                  {currentSessionId && currentPage === 'session-detail' && (
                    <span className="chat-context-badge">context: session</span>
                  )}
                  <span className="chat-session-label mono">{sessionLabel}</span>
                </div>
                <button className="chat-close-btn" onClick={toggleOpen} title="Close">
                  <ArrowDown size={14} />
                </button>
              </div>

              {/* Messages */}
              <ChatMessageList
                messages={messages}
                onRetry={handleRetry}
                onConfirmTool={confirmToolCall}
                onSuggest={setPrefill}
              />

              {/* Input */}
              <ChatInput
                onSend={handleSend}
                streaming={streaming}
                onStop={stop}
                disabled={!activeSessionId}
                prefill={prefill}
              />
            </div>
          </div>
        </div>
      )}
    </>
  )
}
