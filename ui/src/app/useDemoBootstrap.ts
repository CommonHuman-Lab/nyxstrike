import { useEffect, useState } from 'react'
import type { WebDashboardResponse, Tool } from '../api'
import type { RunHistoryEntry } from '../shared/types'

interface UseDemoBootstrapOptions {
  demo: boolean
  onSnapshot: (health: WebDashboardResponse, tools: Tool[]) => void
  onRunHistory: (entries: RunHistoryEntry[]) => void
  onLogLines: (lines: string[]) => void
}

export function useDemoBootstrap({ demo, onSnapshot, onRunHistory, onLogLines }: UseDemoBootstrapOptions) {
  const [demoProcesses, setDemoProcesses] = useState<unknown>(null)
  const [demoSessions, setDemoSessions] = useState<unknown>(null)
  const [demoCpuHistory, setDemoCpuHistory] = useState<unknown>(null)

  // Lazy-load large demo data only when in demo mode.
  useEffect(() => {
    if (!demo) return
    import('../app/demo').then(m => {
      onSnapshot(m.DEMO_HEALTH, m.DEMO_TOOLS)
      onRunHistory(m.DEMO_RUN_HISTORY)
      onLogLines(m.DEMO_LOG_LINES)
      setDemoProcesses(m.DEMO_PROCESSES)
      setDemoSessions(m.DEMO_SESSIONS)
      setDemoCpuHistory(m.demoCpuMemHistory())
    })
  }, [demo, onSnapshot, onRunHistory, onLogLines])

  return { demoProcesses, demoSessions, demoCpuHistory }
}
