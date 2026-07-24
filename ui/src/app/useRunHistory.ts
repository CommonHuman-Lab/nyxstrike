import { useCallback, useEffect, useState } from 'react'
import {
  api,
  type ToolExecResponse,
  type RunHistoryEntry as ApiRunHistoryEntry,
  type RunHistorySummaryEntry,
} from '../api'
import type { RunHistoryEntry } from '../shared/types'

/** Extract the `Date: <ISO>` line written by analyze-session into stdout. */
function parseDateFromStdout(stdout: string): Date | null {
  const m = stdout.match(/^Date:\s+(\S+)/m)
  if (!m) return null
  const d = new Date(m[1])
  return isNaN(d.getTime()) ? null : d
}

export function useRunHistory(demo: boolean, authed: boolean) {
  const [runHistory, setRunHistory] = useState<RunHistoryEntry[]>([])

  const addBrowserRunEntry = useCallback((tool: string, params: Record<string, unknown>, result: ToolExecResponse) => {
    setRunHistory(prev => {
      const entry: RunHistoryEntry = {
        id: Date.now(),
        tool,
        params,
        result,
        ts: new Date(),
        source: 'browser',
      }
      return [entry, ...prev].slice(0, 200)
    })
  }, [])

  /** Lightweight: fetches only id/tool/timestamp/success — used on mount and periodic refresh.
   * Keeps the dashboard KPI count accurate without pulling stdout/stderr/params.
   */
  const fetchRunHistorySummary = useCallback(async () => {
    if (demo) return
    try {
      const r = await api.runHistorySummary()
      if (!r.success) return
      setRunHistory(prev => {
        const existingServerIds = new Set(prev.filter(e => e.source === 'server').map(e => e.serverId))
        const newEntries: RunHistoryEntry[] = (r.runs as RunHistorySummaryEntry[])
          .filter(e => !existingServerIds.has(e.id))
          .map(e => ({
            id: -(e.id),
            serverId: e.id,
            source: 'server' as const,
            tool: e.tool,
            params: {},
            ts: e.timestamp ? new Date(e.timestamp) : new Date(),
            result: {
              stdout: '',
              stderr: '',
              return_code: 0,
              success: e.success,
              timed_out: false,
              partial_results: false,
              execution_time: e.execution_time,
              timestamp: e.timestamp,
            },
          }))
        if (newEntries.length === 0) return prev
        const merged = [...prev, ...newEntries].sort((a, b) => b.ts.getTime() - a.ts.getTime())
        return merged
      })
    } catch { /* non-critical */ }
  }, [demo])

  /** Full fetch: includes stdout/stderr/params — called explicitly from the RunPage refresh button. */
  const fetchServerRunHistory = useCallback(async () => {
    if (demo) return
    try {
      const r = await api.runHistory()
      if (!r.success) return
      setRunHistory(prev => {
        // Replace all server entries with the full payload.
        const browserEntries = prev.filter(e => e.source !== 'server')
        const fullEntries: RunHistoryEntry[] = r.runs
          .filter((e: ApiRunHistoryEntry) => {
            // Skip server entries that match a local browser run (same tool, within 10s)
            const serverTs = e.timestamp ? new Date(e.timestamp).getTime() : 0
            return !browserEntries.some(local =>
              local.source === 'browser' &&
              local.tool === e.tool &&
              serverTs > 0 &&
              Math.abs(local.ts.getTime() - serverTs) < 10_000
            )
          })
          .map((e: ApiRunHistoryEntry) => ({
            id: -(e.id),
            serverId: e.id,
            source: 'server' as const,
            tool: e.tool,
            params: e.params,
            ts: e.timestamp ? new Date(e.timestamp) : (parseDateFromStdout(e.stdout ?? '') ?? new Date()),
            result: {
              stdout: e.stdout,
              stderr: e.stderr,
              return_code: e.return_code,
              success: e.success,
              timed_out: e.timed_out,
              partial_results: e.partial_results,
              execution_time: e.execution_time,
              timestamp: e.timestamp,
            },
          }))
        const merged = [...browserEntries, ...fullEntries].sort((a, b) => b.ts.getTime() - a.ts.getTime())
        return merged
      })
    } catch { /* non-critical */ }
  }, [demo])

  const clearServerRunHistory = useCallback(async () => {
    if (demo) {
      setRunHistory([])
      return
    }
    const r = await api.clearRunHistory()
    if (r.success) setRunHistory([])
  }, [demo])

  useEffect(() => {
    if (demo || !authed) return
    // Use the lightweight summary endpoint on mount — no stdout/stderr/params payload.
    // The full fetch is triggered explicitly from the RunPage refresh button.
    fetchRunHistorySummary().catch(() => {})
  }, [demo, authed, fetchRunHistorySummary])

  return { runHistory, setRunHistory, addBrowserRunEntry, fetchServerRunHistory, clearServerRunHistory }
}
