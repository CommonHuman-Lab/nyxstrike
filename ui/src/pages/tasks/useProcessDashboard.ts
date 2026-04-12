import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type ProcessDashboardResponse } from '../../api'

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

    let dashSource: EventSource | null = null
    let poolSource: EventSource | null = null

    function closeStreams() {
      dashSource?.close()
      poolSource?.close()
    }

    function startPolling() {
      if (pollRef.current) return
      setStreamStatus('polling')
      pollRef.current = setInterval(fetchData, 3000)
    }

    try {
      dashSource = api.processDashboardStream()
      poolSource = api.processPoolStatsStream()

      let dashOpen = false
      let poolOpen = false

      dashSource.onopen = () => {
        dashOpen = true
        if (dashOpen && poolOpen) setStreamStatus('streaming')
      }

      poolSource.onopen = () => {
        poolOpen = true
        if (dashOpen && poolOpen) setStreamStatus('streaming')
      }

      const onStreamError = () => {
        setStreamStatus('error')
        closeStreams()
        startPolling()
      }

      dashSource.onerror = onStreamError
      poolSource.onerror = onStreamError

      dashSource.onmessage = e => {
        try {
          setData(JSON.parse(e.data))
          setError(null)
          setLoading(false)
        } catch {
          setError('Stream parse error')
        }
      }

      poolSource.onmessage = e => {
        try {
          setPoolStats(JSON.parse(e.data))
          setError(null)
        } catch {
          setError('Pool stats stream error')
        }
      }
    } catch {
      setStreamStatus('error')
      startPolling()
    }

    return () => {
      closeStreams()
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [demoData, fetchData])

  useEffect(() => {
    if (demoData) return

    if (streamStatus !== 'polling') {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
      return
    }

    fetchData()
    if (!pollRef.current) {
      pollRef.current = setInterval(fetchData, 3000)
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [demoData, fetchData, streamStatus])

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
