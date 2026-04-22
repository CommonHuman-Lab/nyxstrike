import { useState, useRef, useCallback } from 'react'
import { api } from '../../api'
import type { ChatMessageItem, ToolCallPending } from '../../api'

// Read auth token from sessionStorage (same as client.ts)
function getAuthToken(): string | null {
  return sessionStorage.getItem('nyxstrike_token')
}

export interface ChatStats {
  eval_count: number
  prompt_eval_count: number
  total_duration_s: number
  eval_duration_s: number
  tokens_per_sec: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  thinking?: boolean
  error?: boolean
  stats?: ChatStats
  timestamp?: string
  /** Set when the model is requesting a tool call — awaiting operator confirmation. */
  toolCallPending?: ToolCallPending
}

const BACKOFF_MS = [500, 1000, 2000, 4000]

function nowISO(): string {
  return new Date().toISOString()
}

export function useChatStream(chatSessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const loadHistory = useCallback(async (sessionId: string) => {
    try {
      const res = await api.chat.getMessages(sessionId)
      if (res.success) {
        setMessages(res.messages.map((m: ChatMessageItem) => ({
          id: String(m.id),
          role: m.role,
          content: m.content,
          timestamp: m.created_at,
          ...(m.stats ? { stats: JSON.parse(m.stats) } : {}),
        })))
      }
    } catch { /* ignore */ }
  }, [])

  /**
   * Read an SSE stream from ``response`` and update the assistant message
   * identified by ``assistantMsgId``.  Returns a promise that resolves when
   * the stream ends (DONE / ERROR / network close).
   */
  const _consumeStream = useCallback(async (
    response: globalThis.Response,
    assistantMsgId: string,
  ): Promise<'done' | 'tool_pending'> => {
    if (!response.body) throw new Error('No response body')
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() ?? ''

      for (const event of events) {
        const dataLine = event.trim()
        if (!dataLine.startsWith('data: ')) continue
        const payload = dataLine.slice(6)

        if (payload === '[DONE]') {
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId ? { ...m, streaming: false, thinking: false } : m
          ))
          setStreaming(false)
          return 'done'
        }

        if (payload === '[THINKING]') {
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId ? { ...m, thinking: true } : m
          ))
          continue
        }

        if (payload.startsWith('[STATS]')) {
          try {
            const stats = JSON.parse(payload.slice(7).trim()) as ChatStats
            setMessages(prev => prev.map(m =>
              m.id === assistantMsgId ? { ...m, stats } : m
            ))
          } catch { /* malformed stats, skip */ }
          continue
        }

        if (payload.startsWith('[ERROR]')) {
          const errMsg = payload.slice(7).trim()
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId
              ? { ...m, content: errMsg, streaming: false, thinking: false, error: true }
              : m
          ))
          setStreaming(false)
          return 'done'
        }

        if (payload.startsWith('[TOOL_CALL_PENDING]')) {
          try {
            const pending = JSON.parse(payload.slice(19).trim()) as ToolCallPending
            setMessages(prev => prev.map(m =>
              m.id === assistantMsgId
                ? { ...m, content: '', streaming: false, thinking: false, toolCallPending: pending }
                : m
            ))
          } catch { /* malformed, skip */ }
          setStreaming(false)
          return 'tool_pending'
        }

        // Parse JSON token — first real token clears thinking state
        try {
          const token = JSON.parse(payload)
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId
              ? { ...m, content: m.content + token, thinking: false }
              : m
          ))
        } catch { /* malformed chunk, skip */ }
      }
    }

    // Stream ended without [DONE]
    setMessages(prev => prev.map(m =>
      m.id === assistantMsgId ? { ...m, streaming: false, thinking: false } : m
    ))
    setStreaming(false)
    return 'done'
  }, [])

  const send = useCallback(async (
    message: string,
    context: { page: string; session_id: string },
    retryCount = 0,
  ) => {
    if (!chatSessionId || streaming) return

    // Add user message
    const userMsgId = `user-${Date.now()}-${Math.random().toString(36).slice(2)}`
    setMessages(prev => [...prev, { id: userMsgId, role: 'user', content: message, timestamp: nowISO() }])

    // Add placeholder assistant message (typing indicator)
    const assistantMsgId = `assistant-${Date.now()}-${Math.random().toString(36).slice(2)}`
    setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', content: '', streaming: true, timestamp: nowISO() }])
    setStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller

    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const token = getAuthToken()
    if (token) headers['Authorization'] = `Bearer ${token}`

    try {
      const res = await fetch(`/api/chat/sessions/${chatSessionId}/message`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message, context }),
        signal: controller.signal,
      })

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`)
      }

      await _consumeStream(res, assistantMsgId)

    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId ? { ...m, streaming: false, thinking: false } : m
        ))
        setStreaming(false)
        return
      }

      // Network error — try exponential backoff reconnect
      if (retryCount < BACKOFF_MS.length) {
        const delay = BACKOFF_MS[retryCount]
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: `Connection error, retrying in ${delay / 1000}s…`, streaming: true, thinking: false }
            : m
        ))
        await new Promise(r => setTimeout(r, delay))
        setMessages(prev => prev.filter(m => m.id !== assistantMsgId && m.id !== userMsgId))
        setStreaming(false)
        send(message, context, retryCount + 1)
        return
      }

      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId
          ? { ...m, content: 'Failed to connect after multiple retries.', streaming: false, thinking: false, error: true }
          : m
      ))
      setStreaming(false)
    }
  }, [chatSessionId, streaming, _consumeStream])

  /** Confirm or reject a pending tool call, then stream the follow-up. */
  const confirmToolCall = useCallback(async (
    pendingMsgId: string,
    approved: boolean,
  ) => {
    if (!chatSessionId || streaming) return

    // Replace the pending card with a "running…" / "cancelled" indicator
    setMessages(prev => prev.map(m =>
      m.id === pendingMsgId
        ? { ...m, toolCallPending: undefined, streaming: approved, thinking: approved, content: '' }
        : m
    ))
    if (approved) setStreaming(true)

    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const token = getAuthToken()
    if (token) headers['Authorization'] = `Bearer ${token}`

    try {
      const res = await fetch(`/api/chat/sessions/${chatSessionId}/tool-confirm`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ approved }),
      })

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`)
      }

      // Stream the follow-up response into the same message slot
      await _consumeStream(res, pendingMsgId)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setMessages(prev => prev.map(m =>
        m.id === pendingMsgId
          ? { ...m, content: `Error: ${msg}`, streaming: false, thinking: false, error: true }
          : m
      ))
      setStreaming(false)
    }
  }, [chatSessionId, streaming, _consumeStream])

  function stop() {
    abortRef.current?.abort()
  }

  function clearMessages() {
    setMessages([])
  }

  function addRetryMessage(originalMsg: string, context: { page: string; session_id: string }) {
    setMessages(prev => {
      const last = prev[prev.length - 1]
      if (last?.error) return prev.slice(0, -2)
      return prev
    })
    setTimeout(() => send(originalMsg, context), 0)
  }

  return { messages, streaming, send, stop, loadHistory, clearMessages, addRetryMessage, confirmToolCall }
}
