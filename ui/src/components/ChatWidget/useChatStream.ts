import { useState, useRef, useCallback } from 'react'
import { api } from '../../api'
import type { ChatMessageItem } from '../../api'

// Read auth token from sessionStorage (same as client.ts)
function getAuthToken(): string | null {
  return sessionStorage.getItem('nyxstrike_token')
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  error?: boolean
}

const BACKOFF_MS = [500, 1000, 2000, 4000]

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
        })))
      }
    } catch { /* ignore */ }
  }, [])

  const send = useCallback(async (
    message: string,
    context: { page: string; session_id: string },
    retryCount = 0,
  ) => {
    if (!chatSessionId || streaming) return

    // Add user message
    const userMsgId = `user-${Date.now()}`
    setMessages(prev => [...prev, { id: userMsgId, role: 'user', content: message }])

    // Add placeholder assistant message (typing indicator)
    const assistantMsgId = `assistant-${Date.now()}`
    setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', content: '', streaming: true }])
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

      const reader = res.body.getReader()
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
              m.id === assistantMsgId ? { ...m, streaming: false } : m
            ))
            setStreaming(false)
            return
          }

          if (payload.startsWith('[ERROR]')) {
            const errMsg = payload.slice(7).trim()
            setMessages(prev => prev.map(m =>
              m.id === assistantMsgId
                ? { ...m, content: errMsg, streaming: false, error: true }
                : m
            ))
            setStreaming(false)
            return
          }

          // Parse JSON token
          try {
            const token = JSON.parse(payload)
            setMessages(prev => prev.map(m =>
              m.id === assistantMsgId
                ? { ...m, content: m.content + token }
                : m
            ))
          } catch { /* malformed chunk, skip */ }
        }
      }

      // Stream ended without [DONE]
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId ? { ...m, streaming: false } : m
      ))
      setStreaming(false)

    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        // User stopped — mark as done, content already streamed
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId ? { ...m, streaming: false } : m
        ))
        setStreaming(false)
        return
      }

      // Network error — try exponential backoff reconnect
      if (retryCount < BACKOFF_MS.length) {
        const delay = BACKOFF_MS[retryCount]
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: `Connection error, retrying in ${delay / 1000}s…`, streaming: true }
            : m
        ))
        await new Promise(r => setTimeout(r, delay))
        // Remove the placeholder and retry
        setMessages(prev => prev.filter(m => m.id !== assistantMsgId && m.id !== userMsgId))
        setStreaming(false)
        send(message, context, retryCount + 1)
        return
      }

      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId
          ? { ...m, content: 'Failed to connect after multiple retries.', streaming: false, error: true }
          : m
      ))
      setStreaming(false)
    }
  }, [chatSessionId, streaming])

  function stop() {
    abortRef.current?.abort()
  }

  function clearMessages() {
    setMessages([])
  }

  function addRetryMessage(originalMsg: string, context: { page: string; session_id: string }) {
    // Remove last error message and resend
    setMessages(prev => {
      const last = prev[prev.length - 1]
      if (last?.error) return prev.slice(0, -2) // remove user + error pair
      return prev
    })
    setTimeout(() => send(originalMsg, context), 0)
  }

  return { messages, streaming, send, stop, loadHistory, clearMessages, addRetryMessage }
}
