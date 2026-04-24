import { useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import type { ResourceUsage, SystemResourcesResponse } from '../../api'
import type { HistoryPoint } from '../../shared/types'

const HISTORY_MAX = 20
const RECONNECT_CAP_MS = 30_000

export interface SystemResourcesState {
  resources: ResourceUsage | null
  resources_timestamp: string
  history: HistoryPoint[]
  connected: boolean
}

/**
 * Opens /api/system/resources/stream only while mounted.
 * Reconnects with exponential back-off (1s → 2s → 4s … capped at 30s).
 * Falls back to polling the /web-dashboard endpoint on persistent failure.
 */
export function useSystemResources(
  demoResources?: ResourceUsage,
  demoHistory?: HistoryPoint[]
): SystemResourcesState {
  const [resources, setResources] = useState<ResourceUsage | null>(
    demoResources ?? null
  )
  const [timestamp, setTimestamp] = useState('')
  const [history, setHistory] = useState<HistoryPoint[]>(demoHistory ?? [])
  const [connected, setConnected] = useState(false)

  const streamRef = useRef<EventSource | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptsRef = useRef(0)
  const unmountedRef = useRef(false)

  useEffect(() => {
    if (demoResources) return

    unmountedRef.current = false

    function applyPayload(payload: SystemResourcesResponse) {
      setResources(payload.resources)
      setTimestamp(payload.resources_timestamp)
      setHistory(prev => {
        const point: HistoryPoint = {
          t: Date.now(),
          cpu: payload.resources.cpu_percent,
          mem: payload.resources.memory_percent,
          network_bytes_sent: payload.resources.network_bytes_sent,
          network_bytes_recv: payload.resources.network_bytes_recv,
        }
        const combined = [...prev, point]
        return combined.length <= HISTORY_MAX
          ? combined
          : combined.slice(combined.length - HISTORY_MAX)
      })
    }

    function stopPoll() {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }

    function stopStream() {
      streamRef.current?.close()
      streamRef.current = null
    }

    function stopReconnect() {
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current)
        reconnectRef.current = null
      }
    }

    function startPoll() {
      stopPoll()
      setConnected(false)
      async function tick() {
        try {
          const dash = await api.dashboard()
          if (!unmountedRef.current && dash.resources && dash.resources_timestamp) {
            applyPayload({
              resources: dash.resources,
              resources_timestamp: dash.resources_timestamp,
            })
          }
        } catch { /* ignore */ }
      }
      tick()
      pollRef.current = setInterval(tick, 5_000)
    }

    function scheduleReconnect() {
      stopReconnect()
      const attempt = ++attemptsRef.current
      const delayMs = Math.min(RECONNECT_CAP_MS, 1_000 * Math.pow(2, attempt - 1))
      reconnectRef.current = setTimeout(() => {
        if (!unmountedRef.current) connect()
      }, delayMs)
    }

    function connect() {
      stopStream()
      try {
        const es = api.resourcesStream()
        streamRef.current = es

        es.onopen = () => {
          if (unmountedRef.current) return
          attemptsRef.current = 0
          stopReconnect()
          stopPoll()
          setConnected(true)
        }

        es.onmessage = e => {
          if (unmountedRef.current) return
          try {
            const payload = JSON.parse(e.data) as SystemResourcesResponse
            if (payload?.resources) applyPayload(payload)
          } catch { /* ignore parse errors */ }
        }

        es.onerror = () => {
          if (unmountedRef.current) return
          setConnected(false)
          stopStream()
          startPoll()
          scheduleReconnect()
        }
      } catch {
        if (unmountedRef.current) return
        setConnected(false)
        startPoll()
        scheduleReconnect()
      }
    }

    connect()

    return () => {
      unmountedRef.current = true
      stopStream()
      stopPoll()
      stopReconnect()
    }
  }, [demoResources])

  return {
    resources,
    resources_timestamp: timestamp,
    history,
    connected,
  }
}
