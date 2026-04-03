import type { Tool } from '../../api'
import type { RunHistoryEntry } from '../../types'

export function getCategories(tools: Tool[]): string[] {
  return ['all', ...Array.from(new Set(tools.map(t => t.category))).sort()]
}

export function getFilteredTools(
  tools: Tool[],
  toolsStatus: Record<string, boolean>,
  activeCat: string,
  search: string
): Tool[] {
  const q = search.toLowerCase()
  return tools
    .filter(tool => {
      if (toolsStatus[tool.name] !== true) return false
      const matchCat = activeCat === 'all' || tool.category === activeCat
      return matchCat && (!q || tool.name.includes(q) || tool.desc.toLowerCase().includes(q))
    })
    .sort((a, b) => a.name.localeCompare(b.name))
}

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
