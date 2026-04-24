import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import type { ProcessDashboardResponse, ProcessesStreamResponse } from '../../api'

export type StreamStatus = 'polling' | 'streaming' | 'error'

interface UseProcessDashboardResult {
  data: ProcessDashboardResponse | null
  poolStats: Record<string, unknown> | null
  loading: boolean
  error: string | null
  actionMsg: string | null
  streamStatus: StreamStatus
  fetchData: () => Promise<void>
  pauseProcess: (pid: number) => Promise<void>
  resumeProcess: (pid: number) => Promise<void>
  terminateProcess: (pid: number) => Promise<void>
  cancelAiTask: (taskId: string) => Promise<void>
}

function adaptStreamPayload(payload: ProcessesStreamResponse): ProcessDashboardResponse {
  const entries = Object.values(payload.processes).map(p => {
    const raw = p as unknown as Record<string, unknown>
    return {
      pid: p.pid,
      task_id: p.task_id ?? null,
      ai_task: p.ai_task ?? false,
      command: p.command,
      status: p.status,
      // runtime_formatted comes from server-side _annotate_process(); fall back gracefully
      runtime: raw['runtime_formatted'] as string ?? '—',
      progress_percent: `${((p.progress ?? 0) * 100).toFixed(1)}%`,
      progress_bar: '',
      eta: raw['eta_formatted'] as string ?? '—',
      bytes_processed: p.bytes_processed,
      last_output: p.last_output,
    }
  })

  return {
    timestamp: payload.timestamp,
    total_processes: payload.total_count,
    visual_dashboard: '',
    processes: entries,
    system_load: payload.system_load,
  }
}

export function useProcessDashboard(
  demoData?: { processes: ProcessDashboardResponse }
): UseProcessDashboardResult {
  const [data, setData] = useState<ProcessDashboardResponse | null>(demoData?.processes ?? null)
  const [poolStats, setPoolStats] = useState<Record<string, unknown> | null>(
    demoData ? { workers: 4, queued: 2, completed: 38 } : null
  )
  const [loading, setLoading] = useState(!demoData)
  const [error, setError] = useState<string | null>(null)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [streamStatus, setStreamStatus] = useState<StreamStatus>(demoData ? 'polling' : 'streaming')

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const streamRef = useRef<EventSource | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const unmountedRef = useRef(false)

  const fetchData = useCallback(async () => {
    if (demoData) return
    try {
      const [dash, pool] = await Promise.all([api.processDashboard(), api.processPoolStats()])
      setData(dash)
      setPoolStats(pool as Record<string, unknown>)
      setError(null)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [demoData])

  useEffect(() => {
    if (demoData) return

    unmountedRef.current = false

    function cleanupStream() {
      streamRef.current?.close()
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

    function startPolling() {
      cleanupPoll()
      setStreamStatus('polling')
      fetchData()
      pollRef.current = setInterval(fetchData, 3000)
    }

    function scheduleReconnect() {
      cleanupReconnect()
      const attempt = reconnectAttemptsRef.current + 1
      reconnectAttemptsRef.current = attempt
      // exponential back-off: 1s, 2s, 4s, 8s … capped at 30s
      const delayMs = Math.min(30_000, 1_000 * Math.pow(2, Math.max(0, attempt - 1)))
      reconnectRef.current = setTimeout(() => {
        if (!unmountedRef.current) connectStream()
      }, delayMs)
    }

    function connectStream() {
      cleanupStream()
      try {
        const source = api.processesStream()
        streamRef.current = source

        source.onopen = () => {
          if (unmountedRef.current) return
          reconnectAttemptsRef.current = 0
          cleanupReconnect()
          cleanupPoll()
          setStreamStatus('streaming')
        }

        source.onmessage = e => {
          if (unmountedRef.current) return
          try {
            const payload = JSON.parse(e.data) as ProcessesStreamResponse
            if (payload?.success) {
              setData(adaptStreamPayload(payload))
              setPoolStats(payload.pool_stats ?? null)
              setError(null)
              setLoading(false)
            }
          } catch {
            setError('Stream parse error')
          }
        }

        source.onerror = () => {
          if (unmountedRef.current) return
          setStreamStatus('error')
          cleanupStream()
          startPolling()
          scheduleReconnect()
        }
      } catch {
        if (unmountedRef.current) return
        setStreamStatus('error')
        startPolling()
        scheduleReconnect()
      }
    }

    connectStream()

    return () => {
      unmountedRef.current = true
      cleanupStream()
      cleanupPoll()
      cleanupReconnect()
    }
  }, [demoData, fetchData])

  const runAction = useCallback(async (
    fn: () => Promise<{ success: boolean; message?: string; error?: string }>,
    label: string
  ) => {
    try {
      const result = await fn()
      setActionMsg(result.success ? (result.message ?? `${label} OK`) : (result.error ?? `${label} failed`))
    } catch (e) {
      setActionMsg(String(e))
    }

    setTimeout(() => setActionMsg(null), 3000)
    await fetchData()
    if (label === 'Terminated') {
      setData(prev => prev ? {
        ...prev,
        processes: prev.processes.filter(p => p.status !== 'terminated'),
      } : prev)
    }
  }, [fetchData])

  return {
    data,
    poolStats,
    loading,
    error,
    actionMsg,
    streamStatus,
    fetchData,
    pauseProcess: (pid: number) => runAction(() => api.pauseProcess(pid), 'Paused'),
    resumeProcess: (pid: number) => runAction(() => api.resumeProcess(pid), 'Resumed'),
    terminateProcess: (pid: number) => runAction(() => api.terminateProcess(pid), 'Terminated'),
    cancelAiTask: (taskId: string) => runAction(() => api.cancelAiTask(taskId), 'Cancelled'),
  }
}
