import { useState } from 'react'
import {
  Activity, AlertCircle, Box, Brain, Bug, CheckCircle,
  ChevronRight, ChevronUp,
  Cpu, Database, Earth, Eye, Fingerprint, Lock, Server, Shield, Wand, Wifi, XCircle, Zap,
} from 'lucide-react'
import type { Tool, WebDashboardResponse } from '../../api'
import { ToolModal } from '../../components/ToolModal'
import { CollapseChevron } from '../../components/CollapseChevron'
import { getCatTools, getToolAvailabilityAgeLabel } from './utils'

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  essential: <Wand size={14} />,
  network_recon: <Wifi size={14} />,
  web_recon: <Activity size={14} />,
  web_vuln: <AlertCircle size={14} />,
  brute_force: <Lock size={14} />,
  binary: <Cpu size={14} />,
  forensics: <Database size={14} />,
  cloud: <Server size={14} />,
  osint: <Eye size={14} />,
  exploitation: <Zap size={14} />,
  api: <Activity size={14} />,
  wifi_pentest: <Wifi size={14} />,
  database: <Database size={14} />,
  vulnerability_intelligence: <Bug size={14} />,
  active_directory: <Box size={14} />,
  fingerprint: <Fingerprint size={14} />,
  ops: <Earth size={14} />,
  intelligence: <Brain size={14} />,
  data_processing: <Server size={14} />,
  ai_assist: <Brain size={14} />,
}

function ToolCategoryRow({
  category,
  stats,
  toolStatuses,
  toolsByName,
}: {
  category: string
  stats: { total: number; available: number }
  toolStatuses: Record<string, boolean>
  toolsByName: Record<string, Tool>
}) {
  const [open, setOpen] = useState(false)
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const pct = stats.total > 0 ? (stats.available / stats.total) * 100 : 0
  const color = pct === 100 ? 'var(--green)' : pct > 50 ? 'var(--amber)' : 'var(--red)'
  const toolsInCat = Object.entries(toolStatuses).sort(([a], [b]) => a.localeCompare(b))

  return (
    <>
      {selectedTool && (
        <ToolModal
          tool={selectedTool}
          onClose={() => setSelectedTool(null)}
          installed={toolStatuses[selectedTool.name]}
        />
      )}
      <div className="cat-row">
        <button className="cat-header" onClick={() => setOpen(prev => !prev)}>
          <span className="cat-icon" style={{ color }}>{CATEGORY_ICONS[category] || <Shield size={14} />}</span>
          <span className="cat-name">{category.replace(/_/g, ' ')}</span>
          <span className="cat-badge" style={{ background: `${color}22`, color }}>
            {stats.available}/{stats.total}
          </span>
          <div className="cat-bar-bg">
            <div className="cat-bar-fill" style={{ width: `${pct}%`, background: color }} />
          </div>
          <span className="cat-chevron"><CollapseChevron open={open} size={14} /></span>
        </button>

        {open && (
          <div className="cat-tools-grid">
            {toolsInCat.map(([name, available]) => {
              const toolObj = toolsByName[name]
              return (
                <div
                  key={name}
                  className={`tool-chip ${available ? 'available' : 'missing'}${toolObj ? ' tool-chip--clickable' : ''}`}
                  onClick={toolObj ? () => setSelectedTool(toolObj) : undefined}
                  title={toolObj ? `Click for details on ${name}` : undefined}
                >
                  {available
                    ? <CheckCircle size={10} color="var(--green)" />
                    : <XCircle size={10} color="var(--red)" />}
                  <span className="mono">{name}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </>
  )
}

export function ToolAvailabilitySection({
  health,
  tools,
  toolCategories,
}: {
  health: WebDashboardResponse
  tools: Tool[]
  toolCategories: Record<string, string[]>
}) {
  const [showAll, setShowAll] = useState(false)
  const toolsByName = Object.fromEntries(tools.map(tool => [tool.name, tool]))
  const installColor = health.all_essential_tools_available ? 'var(--success)' : 'var(--warning)'
  const categoryEntries = Object.entries(health.category_stats)
    .sort(([a], [b]) => a.localeCompare(b))
  const missingCategoryCount = categoryEntries.filter(([, stats]) => stats.available < stats.total).length
  const visibleCategoryEntries = showAll
    ? categoryEntries
    : categoryEntries.filter(([, stats]) => stats.available < stats.total)

  return (
    <section className="section">
      <button className="section-header section-header--collapsible" onClick={() => setShowAll(prev => !prev)}>
        <h3>
          Tool Availability
          <span className="section-install-badge" style={{ color: installColor, borderColor: `${installColor}55`, background: `${installColor}1A` }}>
            {health.total_tools_available}/{health.total_tools_count} installed
          </span>
        </h3>
        <div className="section-header-side">
          <span className="section-meta">{getToolAvailabilityAgeLabel(health.tool_availability_age_seconds)}</span>
          <span className="section-chevron"><CollapseChevron open={showAll} size={14} /></span>
        </div>
      </button>
      <div className="cat-list">
        {!showAll && (
          <div className="cat-list-mode-note">
            {missingCategoryCount === 0
              ? `All categories fully installed (${categoryEntries.length}/${categoryEntries.length})`
              : `Showing categories with missing tools (${missingCategoryCount}/${categoryEntries.length})`}
          </div>
        )}
        {visibleCategoryEntries.map(([category, stats]) => {
          const catToolNames = getCatTools(category, health.tools_status, toolCategories)
          const catStatuses = Object.fromEntries(catToolNames.map(name => [name, health.tools_status[name] ?? false]))
          return (
            <ToolCategoryRow
              key={category}
              category={category}
              stats={stats}
              toolStatuses={catStatuses}
              toolsByName={toolsByName}
            />
          )
        })}
        <button className="cat-list-toggle-row" onClick={() => setShowAll(prev => !prev)}>
          <span>{showAll ? 'Show only incomplete categories' : 'Show all categories'}</span>
          <span className="cat-list-toggle-chevron">{showAll ? <ChevronUp size={14} /> : <ChevronRight size={14} />}</span>
        </button>
      </div>
    </section>
  )
}
