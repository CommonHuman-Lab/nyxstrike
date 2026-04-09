import { useEffect, useState } from 'react'
import { Wrench, Database, Shield, XCircle } from 'lucide-react'
import { api, type Tool, type WebDashboardResponse } from '../../api'
import { StatCard } from '../../components/StatCard'
import { ToolModal } from '../../components/ToolModal'
import { useToast } from '../../components/ToastProvider'
import { filterToolsByOptions, getToolCategories } from '../../shared/toolUtils'
import { ToolsRegistrySection } from './ToolsRegistrySection'
import './ToolsPage.css'

interface ToolsPageProps {
  health: WebDashboardResponse
  tools: Tool[]
  toolsStatus: Record<string, boolean>
}

export default function ToolsPage({ health, tools, toolsStatus }: ToolsPageProps) {
  const { pushToast } = useToast()
  const [search, setSearch] = useState('')
  const [activeCat, setActiveCat] = useState<string>('all')
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [missingOnly, setMissingOnly] = useState(false)
  const [refreshingAvailability, setRefreshingAvailability] = useState(false)
  const [localToolsStatus, setLocalToolsStatus] = useState<Record<string, boolean>>(toolsStatus)
  const [localTotals, setLocalTotals] = useState({
    available: health.total_tools_available,
    total: health.total_tools_count,
  })

  const effectiveToolsStatus = localToolsStatus

  useEffect(() => {
    if (refreshingAvailability) return
    setLocalToolsStatus(toolsStatus)
    setLocalTotals({
      available: health.total_tools_available,
      total: health.total_tools_count,
    })
  }, [toolsStatus, health.total_tools_available, health.total_tools_count, refreshingAvailability])

  const cats = getToolCategories(tools)
  const filtered = filterToolsByOptions(tools, {
    toolsStatus: effectiveToolsStatus,
    activeCategory: activeCat,
    search,
    missingOnly,
    includeParentToolSearch: true,
  })

  const missingCount = localTotals.total - localTotals.available

  async function refreshAvailabilityNow() {
    setRefreshingAvailability(true)
    try {
      const response = await api.refreshToolAvailability()
      if (!response.success) {
        pushToast('error', response.error || 'Failed to refresh availability')
        return
      }
      setLocalToolsStatus(response.tools_status)
      setLocalTotals({
        available: response.total_tools_available,
        total: response.total_tools_count,
      })
      pushToast('success', 'Tool availability refreshed')
    } catch (e) {
      pushToast('error', `Refresh failed: ${String(e)}`)
    } finally {
      setRefreshingAvailability(false)
    }
  }

  return (
    <div className="page-content tools-page">
      {selectedTool && (
        <ToolModal
          tool={selectedTool}
          onClose={() => setSelectedTool(null)}
          installed={effectiveToolsStatus[selectedTool.name]}
        />
      )}

      <div className="kpi-row">
        <StatCard icon={<Wrench size={20} />} label="Total Server Tools" value={tools.length} sub="in registry" accent="var(--blue)" />
        <StatCard
          icon={<Shield size={20} />}
          label="Kali Tools Installed"
          value={`${localTotals.available} / ${localTotals.total}`}
          sub={`${((localTotals.available / Math.max(localTotals.total, 1)) * 100).toFixed(0)}% coverage`}
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
        toolsStatus={effectiveToolsStatus}
        onSelectTool={setSelectedTool}
        onRefreshAvailability={refreshAvailabilityNow}
        refreshingAvailability={refreshingAvailability}
      />
    </div>
  )
}
