import { useEffect, useRef, useState, useCallback } from 'react'
import { ArrowDown } from 'lucide-react'
import { ChatMessageBubble } from './ChatMessage'
import type { ChatMessage } from './useChatStream'

interface ChatMessageListProps {
  messages: ChatMessage[]
  onRetry?: (message: ChatMessage) => void
}

const SCROLL_THRESHOLD = 60

export function ChatMessageList({ messages, onRetry }: ChatMessageListProps) {
  const listRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [pinned, setPinned] = useState(true)
  const [showPill, setShowPill] = useState(false)

  const isNearBottom = useCallback(() => {
    const el = listRef.current
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < SCROLL_THRESHOLD
  }, [])

  // Track scroll position
  useEffect(() => {
    const el = listRef.current
    if (!el) return
    function onScroll() {
      const near = isNearBottom()
      setPinned(near)
      if (near) setShowPill(false)
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [isNearBottom])

  // Auto-scroll when pinned and messages change
  useEffect(() => {
    if (pinned) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    } else {
      setShowPill(true)
    }
  }, [messages, pinned])

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    setPinned(true)
    setShowPill(false)
  }

  return (
    <div className="chat-message-list-wrapper">
      <div className="chat-message-list" ref={listRef}>
        {messages.length === 0 && (
          <div className="chat-empty-state">
            <span>Ask NyxStrike anything…</span>
          </div>
        )}
        {messages.map(msg => (
          <ChatMessageBubble
            key={msg.id}
            message={msg}
            onRetry={msg.error && onRetry ? () => onRetry(msg) : undefined}
          />
        ))}
        <div ref={bottomRef} />
      </div>
      {showPill && (
        <button className="chat-scroll-bottom-pill" onClick={scrollToBottom} title="Scroll to bottom">
          <ArrowDown size={14} />
        </button>
      )}
    </div>
  )
}
