import type { RunHistoryEntry } from '../../shared/types'

export function filterHistory(history: RunHistoryEntry[], query: string): RunHistoryEntry[] {
  const q = query.toLowerCase()
  if (!q) return history
  return history.filter(entry => (
    entry.tool.includes(q)
    || Object.values(entry.params).some(v => String(v).toLowerCase().includes(q))
  ))
}

export function groupHistoryByDate(entries: RunHistoryEntry[]): Array<{ dateLabel: string; entries: RunHistoryEntry[] }> {
  const groups: Record<string, RunHistoryEntry[]> = {}

  for (const entry of entries) {
    const date = entry.ts instanceof Date ? entry.ts : new Date(entry.ts)
    const dateLabel = date.toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' })
    if (!groups[dateLabel]) groups[dateLabel] = []
    groups[dateLabel].push(entry)
  }

  return Object.keys(groups)
    .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())
    .map(dateLabel => ({ dateLabel, entries: groups[dateLabel] }))
}
