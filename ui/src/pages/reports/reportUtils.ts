import type { RunHistoryEntry } from '../../shared/types'

export type GroupBy = 'tool' | 'target'

export function extractTarget(entry: RunHistoryEntry): string {
  const targetKeys = ['target', 'url', 'host', 'ip', 'domain', 'file']

  for (const key of targetKeys) {
    const value = entry.params[key]
    if (value) return String(value)
  }

  const first = Object.values(entry.params)[0]
  return first ? String(first) : '(no target)'
}

export function groupByDate(entries: RunHistoryEntry[]): Array<{ label: string; entries: RunHistoryEntry[] }> {
  const map = new Map<string, { label: string; date: Date; entries: RunHistoryEntry[] }>()

  for (const entry of entries) {
    const label = entry.ts.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    if (!map.has(label)) map.set(label, { label, date: entry.ts, entries: [] })
    map.get(label)!.entries.push(entry)
  }

  return Array.from(map.values())
    .sort((a, b) => b.date.getTime() - a.date.getTime())
    .map(({ label, entries: dayEntries }) => ({ label, entries: dayEntries }))
}

export function getGroupStats(entries: RunHistoryEntry[]) {
  const ok = entries.filter(e => e.result.success).length
  const avgTime = entries.reduce((sum, e) => sum + (e.result.execution_time ?? 0), 0) / entries.length
  const last = entries.reduce((a, b) => (a.ts > b.ts ? a : b))
  return { total: entries.length, ok, failed: entries.length - ok, avgTime, last }
}
