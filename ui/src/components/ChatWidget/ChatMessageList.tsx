import { useEffect, useRef, useState, useCallback } from 'react'
import { ArrowDown, Zap } from 'lucide-react'
import { ChatMessageBubble } from './ChatMessage'
import type { ChatMessage } from './useChatStream'

interface ChatMessageListProps {
  messages: ChatMessage[]
  onRetry?: (message: ChatMessage) => void
  onConfirmTool?: (msgId: string, approved: boolean) => void
  onSuggest?: (text: string) => void
}

const SUGGESTIONS = [
  { label: 'Nmap scan', prompt: 'Run an nmap scan on 192.168.1.1' },
  { label: 'WHOIS lookup', prompt: 'Do a WHOIS lookup on example.com' },
  { label: 'Subdomain enum', prompt: 'Enumerate subdomains for example.com' },
  { label: 'SMB enumeration', prompt: 'Enumerate SMB shares on 192.168.1.1' },
  { label: 'Web recon', prompt: 'Run a web recon on https://example.com' },
  { label: 'Crack a hash', prompt: 'Help me crack this hash: 5f4dcc3b5aa765d61d8327deb882cf99' },
]

const SCROLL_THRESHOLD = 60

export function ChatMessageList({ messages, onRetry, onConfirmTool, onSuggest }: ChatMessageListProps) {
  const listRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [pinned, setPinned] = useState(true)
  const [showPill, setShowPill] = useState(false)

  const isNearBottom = useCallback(() => {
    const el = listRef.current
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < SCROLL_THRESHOLD
  }, [])

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
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="chat-empty-icon"><Zap size={22} /></div>
            <p className="chat-empty-title">NyxStrike AI</p>
            <p className="chat-empty-sub">Run tools, analyze results, plan attacks — just ask.</p>
            {onSuggest && (
              <div className="chat-empty-suggestions">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s.label}
                    className="chat-empty-chip"
                    onClick={() => onSuggest(s.prompt)}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          messages.map(msg => (
            <ChatMessageBubble
              key={msg.id}
              message={msg}
              onRetry={msg.error && onRetry ? () => onRetry(msg) : undefined}
              onConfirmTool={
                msg.toolCallPending && onConfirmTool
                  ? (approved) => onConfirmTool(msg.id, approved)
                  : undefined
              }
            />
          ))
        )}
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
