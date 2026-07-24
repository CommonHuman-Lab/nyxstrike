import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Page } from './routing'

interface UseLogStreamOptions {
  demo: boolean
  page: Page
}

export function useLogStream({ demo, page }: UseLogStreamOptions) {
  const [logLines, setLogLines] = useState<string[]>([])
  const [logAutoScroll, setLogAutoScroll] = useState(true)
  const [logLimit, setLogLimit] = useState(500)
  const logEndRef = useRef<HTMLDivElement>(null)
  const sseRef = useRef<EventSource | null>(null)

  // SSE log stream — only active in logs tab
  useEffect(() => {
    if (demo || page !== 'logs') return

    let es: EventSource | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let unmounted = false

    function connect() {
      if (unmounted) return
      es = api.logStream(150)
      sseRef.current = es

      es.onmessage = (e) => {
        setLogLines(prev => {
          const next = [...prev, e.data]
          return next.length > 500 ? next.slice(-500) : next
        })
      }

      es.onerror = () => {
        es?.close()
        es = null
        if (!unmounted) {
          // simple fixed 3 s reconnect — log stream is low-stakes and lazy
          reconnectTimer = setTimeout(connect, 3_000)
        }
      }
    }

    connect()

    return () => {
      unmounted = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      es?.close()
    }
  }, [demo, page])

  // Auto-scroll log to bottom
  useEffect(() => {
    if (page === 'logs' && logAutoScroll) logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logLines, page, logAutoScroll])

  const applyDemoLogLines = useCallback((lines: string[]) => {
    setLogLines(lines)
  }, [])

  return { logLines, logAutoScroll, setLogAutoScroll, logLimit, setLogLimit, logEndRef, applyDemoLogLines }
}
