import { useEffect, useRef, useState } from 'react'
import { Activity, Shield, Wrench, Zap } from 'lucide-react'
import type { Tool, WebDashboardResponse } from '../../api'
import { StatCard } from '../../components/StatCard'
import type { RunHistoryEntry } from '../../shared/types'
import { uptimeStr } from '../../shared/utils'
import { getCommandsCardData } from './utils'

/** Ticks every second, returning a live uptime string derived from the
 *  server-supplied uptime value.  Anchors a local start timestamp on the
 *  first valid uptime received so subsequent SSE keepalives don't reset it. */
function useLiveUptime(serverUptime: number): string {
  const startedAtRef = useRef<number | null>(null)
  const [display, setDisplay] = useState(() => uptimeStr(serverUptime))

  // Update the anchor whenever the server sends a fresh uptime value that
  // differs meaningfully (>2s) from what we'd compute locally, so drift
  // doesn't accumulate over very long sessions.
  useEffect(() => {
    if (serverUptime <= 0) return
    const inferredStart = Date.now() - serverUptime * 1000
    if (
      startedAtRef.current === null ||
      Math.abs(inferredStart - startedAtRef.current) > 2000
    ) {
      startedAtRef.current = inferredStart
    }
  }, [serverUptime])

  useEffect(() => {
    const id = setInterval(() => {
      if (startedAtRef.current === null) return
      const secs = (Date.now() - startedAtRef.current) / 1000
      setDisplay(uptimeStr(secs))
    }, 1000)
    return () => clearInterval(id)
  }, [])

  return display
}

export function KpiSection({
  health,
  tools,
  runHistory,
}: {
  health: WebDashboardResponse
  tools: Tool[]
  runHistory: RunHistoryEntry[]
}) {
  const commands = getCommandsCardData(health, runHistory)
  const uptime = useLiveUptime(health.uptime)

  return (
    <div className="kpi-row">
      <StatCard
        icon={<Activity size={20} />}
        label="Server Status"
        value={health.status.charAt(0).toUpperCase() + health.status.slice(1)}
        sub={`uptime ${uptime}`}
        accent={health.status === 'healthy' ? 'var(--success)' : 'var(--danger)'}
      />
      <StatCard
        icon={<Shield size={20} />}
        label="Kali Tools"
        value={`${health.total_tools_available} / ${health.total_tools_count}`}
        sub={health.all_essential_tools_available ? 'all essential ready' : 'some essential missing'}
        accent={health.all_essential_tools_available ? 'var(--success)' : 'var(--warning)'}
      />
      <StatCard icon={<Wrench size={20} />} label="Server Tools" value={tools.length} sub="in registry" accent="var(--blue)" />
      <StatCard
        icon={<Zap size={20} />}
        label="Commands"
        value={commands.value}
        sub={commands.sub}
        accent={commands.accent}
      />
    </div>
  )
}
