import { useEffect, useState } from 'react'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import type { Page } from './routing'
import { NAV_ENTRIES } from './navRegistry'
import './Sidebar.css'

interface SidebarProps {
  page: Page
  setPage: (page: Page) => void
  isPageEnabled: (page: Page) => boolean
  collapsed: boolean
  onToggleCollapsed: () => void
  mobileOpen: boolean
  onCloseMobile: () => void
}

function isEntryActive(entryId: Exclude<Page, 'session-detail'>, page: Page): boolean {
  if (entryId === 'sessions') return page === 'sessions' || page === 'session-detail'
  return page === entryId
}

// Matches the `max-width: 768px` breakpoint used throughout App.css.
const MOBILE_QUERY = '(max-width: 768px)'

function useIsMobileViewport(): boolean {
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)
  useEffect(() => {
    const mql = window.matchMedia(MOBILE_QUERY)
    function onChange() { setIsMobile(mql.matches) }
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [])
  return isMobile
}

export function Sidebar({
  page,
  setPage,
  isPageEnabled,
  collapsed,
  onToggleCollapsed,
  mobileOpen,
  onCloseMobile,
}: SidebarProps) {
  const visibleEntries = NAV_ENTRIES.filter(entry => isPageEnabled(entry.id))
  // Icon-only collapse is a desktop concept — the mobile drawer always shows full labels.
  const isMobileViewport = useIsMobileViewport()
  const effectiveCollapsed = collapsed && !isMobileViewport

  return (
    <aside
      className={`sidebar${effectiveCollapsed ? ' sidebar--collapsed' : ''}${mobileOpen ? ' sidebar--mobile-open' : ''}`}
    >
      <div className="sidebar-collapse-row">
        <button
          className="sidebar-collapse-btn"
          onClick={onToggleCollapsed}
          title={effectiveCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {effectiveCollapsed ? <PanelLeftOpen size={14} /> : <PanelLeftClose size={14} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {visibleEntries.map(entry => {
          const Icon = entry.icon
          const active = isEntryActive(entry.id, page)
          return (
            <button
              key={entry.id}
              className={`sidebar-nav-item${active ? ' active' : ''}${effectiveCollapsed ? ' collapsed' : ''}`}
              onClick={() => { setPage(entry.id); onCloseMobile() }}
              title={entry.label}
            >
              <Icon size={14} className="sidebar-nav-icon" />
              {!effectiveCollapsed && <span className="sidebar-nav-label">{entry.label}</span>}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
