import type { Tool } from '../../api'

interface RunToolPickerProps {
  search: string
  setSearch: (value: string) => void
  activeCat: string
  setActiveCat: (value: string) => void
  cats: string[]
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
  filtered,
  selected,
  onSelectTool,
}: RunToolPickerProps) {
  return (
    <div className="run-picker">
      <div className="run-picker-controls">
        <input
          className="search-input mono"
          placeholder="Search tools…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="cat-tabs run-cat-tabs">
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
      <div className="run-tool-list">
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
