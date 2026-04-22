import { useState } from 'react'
import { Copy, Check, Terminal, ShieldAlert } from 'lucide-react'
import { renderMarkdown } from './renderMarkdown'
import type { ChatMessage } from './useChatStream'

interface ChatMessageProps {
  message: ChatMessage
  onRetry?: () => void
  onConfirmTool?: (approved: boolean) => void
}

function formatTime(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

function ToolCallCard({ message, onConfirmTool }: { message: ChatMessage; onConfirmTool?: (approved: boolean) => void }) {
  const tc = message.toolCallPending!
  const args = tc.arguments || {}
  const argLines = Object.entries(args)
  return (
    <div className="chat-tool-call-card">
      <div className="chat-tool-call-header">
        <Terminal size={13} />
        <span className="chat-tool-call-name">{tc.tool_name}</span>
      </div>
      {tc.description && (
        <p className="chat-tool-call-desc">{tc.description}</p>
      )}
      {argLines.length > 0 && (
        <div className="chat-tool-call-args">
          {argLines.map(([k, v]) => (
            <div key={k} className="chat-tool-call-arg">
              <span className="chat-tool-call-arg-key">{k}</span>
              <span className="chat-tool-call-arg-val">{String(v)}</span>
            </div>
          ))}
        </div>
      )}
      <div className="chat-tool-call-warning">
        <ShieldAlert size={12} />
        <span>Operator confirmation required before execution</span>
      </div>
      {onConfirmTool && (
        <div className="chat-tool-call-actions">
          <button
            className="chat-tool-call-btn chat-tool-call-btn--approve"
            onClick={() => onConfirmTool(true)}
          >
            Approve &amp; Run
          </button>
          <button
            className="chat-tool-call-btn chat-tool-call-btn--reject"
            onClick={() => onConfirmTool(false)}
          >
            Reject
          </button>
        </div>
      )}
    </div>
  )
}

export function ChatMessageBubble({ message, onRetry, onConfirmTool }: ChatMessageProps) {
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
        {message.toolCallPending ? (
          <ToolCallCard message={message} onConfirmTool={onConfirmTool} />
        ) : message.thinking && message.content === '' ? (
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
        {!isUser && !message.streaming && !message.error && !message.toolCallPending && message.content && (
          <button
            className="chat-copy-btn"
            onClick={copyContent}
            title="Copy message"
          >
            {copied ? <Check size={12} color="var(--green)" /> : <Copy size={12} />}
          </button>
        )}
      </div>
      {!isUser && !message.streaming && !message.toolCallPending && (message.stats || message.timestamp) && (
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


