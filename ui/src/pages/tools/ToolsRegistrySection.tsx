import { CheckCircle, XCircle } from 'lucide-react'
import type { Tool } from '../../api'

interface ToolsRegistrySectionProps {
  tools: Tool[]
  filtered: Tool[]
  categories: string[]
  activeCat: string
  setActiveCat: (value: string) => void
  search: string
  setSearch: (value: string) => void
  missingOnly: boolean
  setMissingOnly: (value: boolean | ((prev: boolean) => boolean)) => void
  missingCount: number
  toolsStatus: Record<string, boolean>
  onSelectTool: (tool: Tool) => void
}

export function ToolsRegistrySection({
  tools,
  filtered,
  categories,
  activeCat,
  setActiveCat,
  search,
  setSearch,
  missingOnly,
  setMissingOnly,
  missingCount,
  toolsStatus,
  onSelectTool,
}: ToolsRegistrySectionProps) {
  return (
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
            onClick={() => setMissingOnly(prev => !prev)}
            title="Show only tools not installed"
          >
            <XCircle size={12} />
            Not installed
            {missingCount > 0 && <span className="badge">{missingCount}</span>}
          </button>
        </div>
        <div className="cat-tabs">
          {categories.map(category => (
            <button
              key={category}
              className={`cat-tab ${activeCat === category ? 'active' : ''}`}
              onClick={() => setActiveCat(category)}
            >
              {category.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="registry-grid registry-grid--wide">
        {filtered.map(tool => (
          <div
            key={tool.name}
            className="registry-card registry-card--clickable"
            onClick={() => onSelectTool(tool)}
            title={`Click for details on ${tool.name}`}
          >
            <div className="registry-card-top">
              <span className="registry-name mono" title={tool.name}>{tool.name}</span>
              <div className="registry-meta">
                {tool.parent_tool && (
                  <span className="registry-cat" title={`Based on ${tool.parent_tool}`}>
                    {tool.parent_tool}
                  </span>
                )}
                {toolsStatus[tool.name] === true && (
                  <span className="registry-installed" title="Installed">
                    <CheckCircle size={11} color="var(--green)" />
                  </span>
                )}
                {toolsStatus[tool.name] === false && (
                  <span className="registry-installed" title="Not installed">
                    <XCircle size={11} color="var(--red)" />
                  </span>
                )}
              </div>
            </div>
            <p className="registry-desc">{tool.desc}</p>
            <div className="registry-footer">
              <span className="registry-cat">{tool.category.replace(/_/g, ' ')}</span>
              <span className="registry-eff" title="Effectiveness">
                {'█'.repeat(Math.round(tool.effectiveness * 5))}{'░'.repeat(5 - Math.round(tool.effectiveness * 5))}
              </span>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <p className="empty-state">No tools match your filter.</p>}
      </div>
    </section>
  )
}
