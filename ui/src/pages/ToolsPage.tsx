import { useState } from 'react'
import { CheckCircle, XCircle, Wrench, Database, Shield } from 'lucide-react'
import { type Tool, type WebDashboardResponse } from '../api'
import { StatCard } from '../components/StatCard'
import { ToolModal } from '../components/ToolModal'
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

  const cats = ['all', ...Array.from(new Set(tools.map(t => t.category))).sort()]
  const filtered = tools.filter(t => {
    const matchCat = activeCat === 'all' || t.category === activeCat
    const q = search.toLowerCase()
    const matchSearch = !q || t.name.includes(q) || t.desc.toLowerCase().includes(q)
    const matchMissing = !missingOnly || toolsStatus[t.name] === false
    return matchCat && matchSearch && matchMissing
  }).sort((a, b) => a.name.localeCompare(b.name))

  const missingCount = health.total_tools_count - health.total_tools_available

  return (
    <div className="page-content">
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

      <section className="section">
        <div className="section-header">
          <h3>Tool Registry <span className="badge">{filtered.length} / {tools.length}</span></h3>
        </div>
        <div className="registry-controls">
          <div className="registry-controls-top">
            <input
              className="search-input mono"
              placeholder="Search tools…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <button
              className={`registry-missing-toggle${missingOnly ? ' active' : ''}`}
              onClick={() => setMissingOnly(o => !o)}
              title="Show only tools not installed"
            >
              <XCircle size={12} />
              Not installed
              {missingCount > 0 && <span className="badge">{missingCount}</span>}
            </button>
          </div>
          <div className="cat-tabs">
            {cats.map(c => (
              <button
                key={c}
                className={`cat-tab ${activeCat === c ? 'active' : ''}`}
                onClick={() => setActiveCat(c)}
              >
                {c.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>
        <div className="registry-grid registry-grid--wide">
          {filtered.map(t => (
            <div
              key={t.name}
              className="registry-card registry-card--clickable"
              onClick={() => setSelectedTool(t)}
              title={`Click for details on ${t.name}`}
            >
              <div className="registry-card-top">
                <span className="registry-name mono">{t.name}</span>
                <span className="registry-cat">{t.category.replace(/_/g, ' ')}</span>
                {toolsStatus[t.name] === true && (
                  <span className="registry-installed" title="Installed">
                    <CheckCircle size={11} color="var(--green)" />
                  </span>
                )}
                {toolsStatus[t.name] === false && (
                  <span className="registry-installed" title="Not installed">
                    <XCircle size={11} color="var(--red)" />
                  </span>
                )}
              </div>
              <p className="registry-desc">{t.desc}</p>
              <div className="registry-footer">
                <span className="registry-endpoint mono">{t.method} {t.endpoint}</span>
                <span className="registry-eff" title="Effectiveness">
                  {'█'.repeat(Math.round(t.effectiveness * 5))}{'░'.repeat(5 - Math.round(t.effectiveness * 5))}
                </span>
              </div>
            </div>
          ))}
          {filtered.length === 0 && <p className="empty-state">No tools match your filter.</p>}
        </div>
      </section>
    </div>
  )
}
