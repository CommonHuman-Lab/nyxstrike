import { useEffect, useRef } from 'react'
import { ChatMessageBubble } from './ChatMessage'
import type { ChatMessage } from './useChatStream'

interface ChatMessageListProps {
  messages: ChatMessage[]
  onRetry?: (message: ChatMessage) => void
}

export function ChatMessageList({ messages, onRetry }: ChatMessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-message-list">
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
  )
}
