import { useRef, useState } from 'react'
import { Send, Square } from 'lucide-react'

interface ChatInputProps {
  onSend: (text: string) => void
  streaming: boolean
  onStop: () => void
  disabled?: boolean
}

export function ChatInput({ onSend, streaming, onStop, disabled }: ChatInputProps) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    const trimmed = text.trim()
    if (!trimmed || streaming || disabled) return
    onSend(trimmed)
    setText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setText(e.target.value)
    // Auto-grow
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  return (
    <div className="chat-input-area">
      <textarea
        ref={textareaRef}
        className="chat-textarea mono"
        value={text}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Message NyxStrike… (Enter to send, Shift+Enter for newline)"
        rows={1}
        disabled={disabled}
      />
      <div className="chat-input-actions">
        {streaming ? (
          <button className="chat-send-btn chat-stop-btn" onClick={onStop} title="Stop">
            <Square size={14} />
          </button>
        ) : (
          <button
            className="chat-send-btn"
            onClick={submit}
            disabled={!text.trim() || disabled}
            title="Send"
          >
            <Send size={14} />
          </button>
        )}
      </div>
    </div>
  )
}
