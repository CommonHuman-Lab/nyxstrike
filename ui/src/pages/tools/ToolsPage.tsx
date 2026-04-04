import { useState } from 'react'
import { Wrench, Database, Shield, XCircle } from 'lucide-react'
import { type Tool, type WebDashboardResponse } from '../../api'
import { StatCard } from '../../components/StatCard'
import { ToolModal } from '../../components/ToolModal'
import { filterToolsByOptions, getToolCategories } from '../../shared/toolUtils'
import { ToolsRegistrySection } from './ToolsRegistrySection'
import './ToolsPage.css'

interface ToolsPageProps {
  health: WebDashboardResponse
  tools: Tool[]
  toolsStatus: Record<string, boolean>
}

export default function ToolsPage({ health, tools, toolsStatus }: ToolsPageProps) {
  const [search, setSearch] = useState('')
  const [activeCat, setActiveCat] = useState<string>('all')
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [missingOnly, setMissingOnly] = useState(false)

  const cats = getToolCategories(tools)
  const filtered = filterToolsByOptions(tools, {
    toolsStatus,
    activeCategory: activeCat,
    search,
    missingOnly,
    includeParentToolSearch: true,
  })

  const missingCount = health.total_tools_count - health.total_tools_available

  return (
    <div className="page-content tools-page">
      {selectedTool && (
        <ToolModal
          tool={selectedTool}
          onClose={() => setSelectedTool(null)}
          installed={toolsStatus[selectedTool.name]}
        />
      )}

      <div className="kpi-row">
        <StatCard icon={<Wrench size={20} />} label="Total Server Tools" value={tools.length} sub="in registry" accent="var(--blue)" />
        <StatCard
          icon={<Shield size={20} />}
          label="Kali Tools Installed"
          value={`${health.total_tools_available} / ${health.total_tools_count}`}
          sub={`${((health.total_tools_available / Math.max(health.total_tools_count, 1)) * 100).toFixed(0)}% coverage`}
          accent="var(--green)"        
        />
        <StatCard
          icon={<XCircle size={20} />}
          label="Missing"
          value={missingCount}
          sub="not installed"
          accent={missingCount > 0 ? 'var(--amber)' : 'var(--text-dim)'}
        />
        <StatCard
          icon={<Database size={20} />}
          label="Categories"
          value={cats.length - 1}
          sub="tool categories"
          accent="var(--purple)"
        />
      </div>

      <ToolsRegistrySection
        tools={tools}
        filtered={filtered}
        categories={cats}
        activeCat={activeCat}
        setActiveCat={setActiveCat}
        search={search}
        setSearch={setSearch}
        missingOnly={missingOnly}
        setMissingOnly={setMissingOnly}
        missingCount={missingCount}
        toolsStatus={toolsStatus}
        onSelectTool={setSelectedTool}
      />
    </div>
  )
}
