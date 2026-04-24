import { useEffect, useRef, useState } from 'react'
import { api, type SessionsResponse } from '../../api'

interface UseSessionsStreamOptions {
  enabled: boolean
  initialStatus?: 'streaming' | 'polling' | 'error'
  onData: (data: SessionsResponse) => void
  onError: (msg: string) => void
  onLoadingDone: () => void
}

export function useSessionsStream({
  enabled,
  initialStatus = 'streaming',
  onData,
  onError,
  onLoadingDone,
}: UseSessionsStreamOptions) {
  const [streamStatus, setStreamStatus] = useState<'streaming' | 'polling' | 'error'>(initialStatus)
  const streamRef = useRef<EventSource | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)

  useEffect(() => {
    if (!enabled) return

    let unmounted = false

    function cleanupStream() {
      if (streamRef.current) streamRef.current.close()
      streamRef.current = null
    }
    function cleanupPoll() {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
    function cleanupReconnect() {
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current)
        reconnectRef.current = null
      }
    }

    function refreshSilent() {
      api.sessions()
        .then(sessionsData => {
          onData(sessionsData)
        })
        .catch(e => onError(String(e)))
    }

    function startPolling() {
      cleanupPoll()
      setStreamStatus('polling')
      refreshSilent()
      pollRef.current = setInterval(refreshSilent, 5000)
    }

    function scheduleReconnect(connectFn: () => void) {
      cleanupReconnect()
      const attempt = reconnectAttemptsRef.current + 1
      reconnectAttemptsRef.current = attempt
      const delayMs = Math.min(30000, 1000 * (2 ** Math.max(0, attempt - 1)))
      reconnectRef.current = setTimeout(() => {
        if (unmounted) return
        connectFn()
      }, delayMs)
    }

    function connectStream() {
      cleanupStream()
      try {
        const source = api.sessionsStream()
        streamRef.current = source
        source.onopen = () => {
          reconnectAttemptsRef.current = 0
          cleanupReconnect()
          cleanupPoll()
          setStreamStatus('streaming')
        }
        source.onmessage = e => {
          try {
            const sessionsData = JSON.parse(e.data) as SessionsResponse
            if (sessionsData?.success) {
              onData(sessionsData)
              onLoadingDone()
            }
          } catch {
            onError('Session stream parse error')
          }
        }
        source.onerror = () => {
          if (unmounted) return
          setStreamStatus('error')
          cleanupStream()
          startPolling()
          scheduleReconnect(connectStream)
        }
      } catch {
        if (unmounted) return
        setStreamStatus('error')
        startPolling()
        scheduleReconnect(connectStream)
      }
    }

    connectStream()

    return () => {
      unmounted = true
      cleanupStream()
      cleanupPoll()
      cleanupReconnect()
    }
  }, [enabled])

  return { streamStatus }
}
