import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { Search } from 'lucide-react'
import type { Tool } from '../api'
import type { Page } from '../app/routing'
import { useEscapeClose } from '../hooks/useEscapeClose'
import './CommandPalette.css'

interface CommandPaletteProps {
  open: boolean
  onClose: () => void
  setPage: (page: Page) => void
  tools: Tool[]
  onSelectTool: (tool: Tool) => void
}

interface PaletteAction {
  id: string
  label: string
  hint: string
  run: () => void
}

const PAGE_ACTIONS: Array<{ page: Page; label: string }> = [
  { page: 'dashboard', label: 'Open Home' },
  { page: 'run', label: 'Open Run' },
  { page: 'reports', label: 'Open Reports' },
  { page: 'tasks', label: 'Open Tasks' },
  { page: 'tools', label: 'Open Tools' },
  { page: 'sessions', label: 'Open Sessions' },
  { page: 'settings', label: 'Open Settings' },
  { page: 'logs', label: 'Open Logs' },
  { page: 'help', label: 'Open Help' },
]

export function CommandPalette({ open, onClose, setPage, tools, onSelectTool }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)

  const actions = useMemo<PaletteAction[]>(() => {
    const pageActions: PaletteAction[] = PAGE_ACTIONS.map(item => ({
      id: `page-${item.page}`,
      label: item.label,
      hint: 'Navigation',
      run: () => { setPage(item.page); onClose() },
    }))

    const toolActions: PaletteAction[] = tools.slice(0, 120).map(tool => ({
      id: `tool-${tool.name}`,
      label: `Run ${tool.name}`,
      hint: tool.category.replace(/_/g, ' '),
      run: () => {
        setPage('run')
        onSelectTool(tool)
        onClose()
      },
    }))

    return [...pageActions, ...toolActions]
  }, [tools, setPage, onSelectTool, onClose])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return actions.slice(0, 18)
    return actions
      .filter(action => `${action.label} ${action.hint}`.toLowerCase().includes(q))
      .slice(0, 18)
  }, [actions, query])

  useEffect(() => {
    if (!open) return
    setQuery('')
    setActive(0)
  }, [open])

  useEscapeClose(open, onClose)

  useEffect(() => {
    if (!open) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.preventDefault()
        return
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setActive(prev => Math.min(prev + 1, Math.max(filtered.length - 1, 0)))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setActive(prev => Math.max(prev - 1, 0))
        return
      }
      if (e.key === 'Enter') {
        const action = filtered[active]
        if (action) {
          e.preventDefault()
          action.run()
        }
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, filtered, active])

  if (!open) return null

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal command-palette" onClick={e => e.stopPropagation()}>
        <div className="command-palette-input-wrap">
          <Search size={14} />
          <input
            autoFocus
            className="command-palette-input mono"
            value={query}
            onChange={e => { setQuery(e.target.value); setActive(0) }}
            placeholder="Type a command or tool name..."
          />
        </div>
        <div className="command-palette-list">
          {filtered.map((action, idx) => (
            <button
              key={action.id}
              className={`command-palette-item${idx === active ? ' active' : ''}`}
              onClick={action.run}
            >
              <span className="command-palette-label">{action.label}</span>
              <span className="command-palette-hint">{action.hint}</span>
            </button>
          ))}
          {filtered.length === 0 && <div className="command-palette-empty">No results</div>}
        </div>
      </div>
    </div>,
    document.body
  )
}
