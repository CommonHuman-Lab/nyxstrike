import { XCircle } from 'lucide-react'
import type { Tool } from '../../api'

interface RunToolPickerProps {
  search: string
  setSearch: (value: string) => void
  activeCat: string
  setActiveCat: (value: string) => void
  cats: string[]
  favorites: Tool[]
  filtered: Tool[]
  selected: Tool | null
  onSelectTool: (tool: Tool) => void
}

export function RunToolPicker({
  search,
  setSearch,
  activeCat,
  setActiveCat,
  cats,
  favorites,
  filtered,
  selected,
  onSelectTool,
}: RunToolPickerProps) {
  return (
    <div className="run-picker">
      <div className="run-picker-controls">
        <div className="search-input-wrap">
          <input
            className="search-input mono"
            placeholder="Search tools…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          {search.trim().length > 0 && (
            <button
              className="search-clear-btn"
              onClick={() => setSearch('')}
              title="Clear search"
              aria-label="Clear search"
            >
              <XCircle size={12} />
            </button>
          )}
        </div>
        <div className="cat-tabs run-cat-tabs">
          {cats.map(c => (
            <button
              key={c}
              className={`cat-tab ${activeCat === c ? 'active' : ''}`}
              onClick={() => setActiveCat(activeCat === c ? 'all' : c)}
            >
              {c.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="run-tool-list">
        {favorites.length > 0 && (
          <>
            <div className="run-tool-group-label">Favorites</div>
            {favorites.map(tool => (
              <button
                key={tool.name}
                className={`run-tool-item run-tool-item--favorite${selected?.name === tool.name ? ' active' : ''}`}
                onClick={() => onSelectTool(tool)}
              >
                <span className="run-tool-name mono">{tool.name}</span>
                <span className="run-tool-cat">{tool.category.replace(/_/g, ' ')}</span>
              </button>
            ))}
            <div className="run-tool-group-label">All Tools</div>
          </>
        )}
        {filtered.map(tool => (
          <button
            key={tool.name}
            className={`run-tool-item${selected?.name === tool.name ? ' active' : ''}`}
            onClick={() => onSelectTool(tool)}
          >
            <span className="run-tool-name mono">{tool.name}</span>
            <span className="run-tool-cat">{tool.category.replace(/_/g, ' ')}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
