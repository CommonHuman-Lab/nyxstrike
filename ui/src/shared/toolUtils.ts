import type { Tool } from '../api'

type ToolFilterOptions = {
  activeCategory: string
  search: string
  toolsStatus?: Record<string, boolean>
  requireAvailable?: boolean
  missingOnly?: boolean
  includeParentToolSearch?: boolean
}

export function getToolCategories(tools: Tool[]): string[] {
  return ['all', ...Array.from(new Set(tools.map(tool => tool.category))).sort()]
}

export function filterToolsByOptions(tools: Tool[], options: ToolFilterOptions): Tool[] {
  const query = options.search.toLowerCase()

  return tools
    .filter(tool => {
      if (options.requireAvailable && options.toolsStatus?.[tool.name] !== true) return false

      const matchCategory = options.activeCategory === 'all' || tool.category === options.activeCategory
      if (!matchCategory) return false

      const matchSearch = !query
        || tool.name.includes(query)
        || tool.desc.toLowerCase().includes(query)
        || (options.includeParentToolSearch && tool.parent_tool?.toLowerCase().includes(query))
      if (!matchSearch) return false

      if (options.missingOnly) return options.toolsStatus?.[tool.name] === false
      return true
    })
    .sort((a, b) => a.name.localeCompare(b.name))
}
