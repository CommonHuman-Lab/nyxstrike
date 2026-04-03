import type { WebDashboardResponse } from '../../api'
import type { RunHistoryEntry } from '../../types'

export function getCatTools(
  category: string,
  allStatuses: Record<string, boolean>,
  toolCategories: Record<string, string[]>
): string[] {
  const fromApi = toolCategories[category] ?? []
  if (fromApi.length > 0) return fromApi
  return Object.keys(allStatuses)
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = parseFloat((bytes / Math.pow(k, i)).toFixed(2))
  return `${value} ${sizes[i]}`
}

export function getCommandsCardData(health: WebDashboardResponse, runHistory: RunHistoryEntry[]) {
  const serverCount = health.telemetry?.commands_executed ?? 0
  const localCount = runHistory.length
  const total = Math.max(serverCount, localCount)

  if (localCount > serverCount) {
    const ok = runHistory.filter(e => e.result.success).length
    return {
      value: total,
      sub: `${ok} ok · ${localCount - ok} failed`,
      accent: ok === localCount ? 'var(--success)' : ok === 0 ? 'var(--danger)' : 'var(--warning)',
    }
  }

  const rate = parseFloat(health.telemetry?.success_rate ?? '0')
  const ok = Math.round(serverCount * rate / 100)
  return {
    value: total,
    sub: `${ok} ok · ${serverCount - ok} failed`,
    accent: ok === serverCount ? 'var(--success)' : ok === 0 ? 'var(--danger)' : 'var(--warning)',
  }
}

export function getToolAvailabilityAgeLabel(ageSeconds: number | null | undefined): string {
  if (ageSeconds === null || ageSeconds === undefined) return 'not yet checked'
  if (ageSeconds < 60) return 'just checked'
  if (ageSeconds < 120) return 'checked a minute ago'
  if (ageSeconds < 3600) return `checked ${Math.floor(ageSeconds / 60)} minutes ago`
  if (ageSeconds < 7200) return 'checked over an hour ago'
  return `checked ${Math.floor(ageSeconds / 3600)} hours ago`
}
