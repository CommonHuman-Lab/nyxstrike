import { Activity, Shield, Wrench, Zap } from 'lucide-react'
import type { Tool, WebDashboardResponse } from '../../api'
import { StatCard } from '../../components/StatCard'
import type { RunHistoryEntry } from '../../shared/types'
import { uptimeStr } from '../../shared/utils'
import { getCommandsCardData } from './utils'

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

  return (
    <div className="kpi-row">
      <StatCard
        icon={<Activity size={20} />}
        label="Server Status"
        value={health.status.charAt(0).toUpperCase() + health.status.slice(1)}
        sub={`uptime ${uptimeStr(health.uptime)}`}
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
