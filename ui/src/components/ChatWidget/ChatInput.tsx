import { useRef, useState, useEffect } from 'react'
import { Send, Square, Smile } from 'lucide-react'

const EMOJI_SET = [
  '👍', '👎', '👋', '🙏', '🤝', '💪', '🎯', '🔥',
  '✅', '❌', '⚠️', '🚨', '🛡️', '🔒', '🔓', '🔑',
  '💡', '📌', '📎', '🗂️', '📊', '📈', '🧪', '🐛',
  '🚀', '⚡', '💻', '🖥️', '🌐', '📡', '🔍', '🕵️',
  '😀', '😂', '🤔', '😎', '🤯', '😱', '👀', '🎉',
]

interface ChatInputProps {
  onSend: (text: string) => void
  streaming: boolean
  onStop: () => void
  disabled?: boolean
  prefill?: string
}

export function ChatInput({ onSend, streaming, onStop, disabled, prefill }: ChatInputProps) {
  const [text, setText] = useState('')
  const [emojiOpen, setEmojiOpen] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const emojiRef = useRef<HTMLDivElement>(null)

  // When a suggestion is selected from the empty state, prefill and focus
  useEffect(() => {
    if (prefill) {
      setText(prefill)
      requestAnimationFrame(() => {
        const ta = textareaRef.current
        if (ta) {
          ta.focus()
          ta.setSelectionRange(ta.value.length, ta.value.length)
        }
      })
    }
  }, [prefill])

  // Close emoji picker on outside click
  useEffect(() => {
    if (!emojiOpen) return
    function onClick(e: MouseEvent) {
      if (emojiRef.current && !emojiRef.current.contains(e.target as Node)) {
        setEmojiOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [emojiOpen])

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
    setEmojiOpen(false)
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

  function insertEmoji(emoji: string) {
    const ta = textareaRef.current
    if (ta) {
      const start = ta.selectionStart
      const end = ta.selectionEnd
      const next = text.slice(0, start) + emoji + text.slice(end)
      setText(next)
      // Restore cursor after emoji
      requestAnimationFrame(() => {
        ta.focus()
        const pos = start + emoji.length
        ta.setSelectionRange(pos, pos)
      })
    } else {
      setText(prev => prev + emoji)
    }
    setEmojiOpen(false)
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
        <div className="chat-emoji-wrapper" ref={emojiRef}>
          <button
            className="chat-emoji-btn"
            onClick={() => setEmojiOpen(prev => !prev)}
            title="Emoji"
            disabled={disabled}
          >
            <Smile size={14} />
          </button>
          {emojiOpen && (
            <div className="chat-emoji-picker">
              {EMOJI_SET.map(e => (
                <button key={e} className="chat-emoji-item" onClick={() => insertEmoji(e)}>
                  {e}
                </button>
              ))}
            </div>
          )}
        </div>
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
