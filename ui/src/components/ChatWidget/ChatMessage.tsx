import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { renderMarkdown } from './renderMarkdown'
import type { ChatMessage } from './useChatStream'

interface ChatMessageProps {
  message: ChatMessage
  onRetry?: () => void
}

function formatTime(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function ChatMessageBubble({ message, onRetry }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)

  function copyContent() {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className={`chat-message chat-message--${isUser ? 'user' : 'assistant'}${message.error ? ' chat-message--error' : ''}`}>
      <div className="chat-message-bubble">
        {message.thinking && message.content === '' ? (
          <span className="chat-thinking-indicator">Thinking…</span>
        ) : message.streaming && message.content === '' ? (
          <span className="chat-typing-indicator">
            <span /><span /><span />
          </span>
        ) : isUser ? (
          <span className="chat-message-text">{message.content}</span>
        ) : (
          <div className="chat-message-markdown">
            {renderMarkdown(message.content)}
          </div>
        )}
        {message.error && onRetry && (
          <button className="chat-retry-btn" onClick={onRetry}>Retry</button>
        )}
        {!isUser && !message.streaming && !message.error && message.content && (
          <button
            className="chat-copy-btn"
            onClick={copyContent}
            title="Copy message"
          >
            {copied ? <Check size={12} color="var(--green)" /> : <Copy size={12} />}
          </button>
        )}
      </div>
      {!isUser && !message.streaming && (message.stats || message.timestamp) && (
        <div className="chat-message-meta">
          <span className="chat-message-stats">
            {message.stats && (
              <>
                {message.stats.eval_count} tokens
                {' \u00b7 '}
                {message.stats.tokens_per_sec} tok/s
                {' \u00b7 '}
                {message.stats.total_duration_s}s
              </>
            )}
            {message.stats && message.timestamp && ' \u00b7 '}
            {message.timestamp && formatTime(message.timestamp)}
          </span>
        </div>
      )}
      {isUser && message.timestamp && !message.streaming && (
        <div className="chat-message-meta">
          <span className="chat-message-time">{formatTime(message.timestamp)}</span>
        </div>
      )}
    </div>
  )
}
