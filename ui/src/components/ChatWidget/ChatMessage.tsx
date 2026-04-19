import { renderMarkdown } from './renderMarkdown'
import type { ChatMessage } from './useChatStream'

interface ChatMessageProps {
  message: ChatMessage
  onRetry?: () => void
}

export function ChatMessageBubble({ message, onRetry }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`chat-message chat-message--${isUser ? 'user' : 'assistant'}${message.error ? ' chat-message--error' : ''}`}>
      <div className="chat-message-bubble">
        {message.streaming && message.content === '' ? (
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
      </div>
      {!isUser && !message.streaming && message.stats && (
        <div className="chat-message-stats">
          {message.stats.eval_count} tokens
          {' \u00b7 '}
          {message.stats.tokens_per_sec} tok/s
          {' \u00b7 '}
          {message.stats.total_duration_s}s
        </div>
      )}
    </div>
  )
}
