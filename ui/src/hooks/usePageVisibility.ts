import { usePersistentState } from './usePersistentState'
import type { Page } from '../app/routing'

/** Pages that cannot be disabled (always visible). */
export const ALWAYS_VISIBLE_PAGES: ReadonlySet<Page> = new Set(['dashboard', 'settings'])

export interface PageConfig {
  page: Exclude<Page, 'session-detail'>
  label: string
  description: string
}

/** All navigable pages with human-readable metadata. */
export const PAGE_CONFIGS: PageConfig[] = [
  { page: 'dashboard', label: 'Home', description: 'Overview dashboard with KPIs and live status' },
  { page: 'run',       label: 'Run',  description: 'Execute security tools interactively' },
  { page: 'logs',      label: 'Logs', description: 'Live server log stream' },
  { page: 'tasks',     label: 'Tasks', description: 'Background task queue and progress' },
  { page: 'tools',     label: 'Tools', description: 'Browse and inspect available tools' },
  { page: 'plugins',   label: 'Plugins', description: 'Manage skill and plugin extensions' },
  { page: 'reports',   label: 'Reports', description: 'Generated scan reports' },
  { page: 'sessions',  label: 'Sessions', description: 'Saved recon/engagement sessions' },
  { page: 'loot',      label: 'Loot', description: 'Captured credentials and artefacts' },
  { page: 'help',      label: 'Help', description: 'Documentation and keyboard shortcuts' },
  { page: 'settings',  label: 'Settings', description: 'Application settings (always visible)' },
]

const STORAGE_KEY = 'nyxstrike_disabled_pages'

/**
 * Returns the set of disabled page keys and a toggle function.
 * Settings and Dashboard are always enabled and cannot be toggled off.
 */
export function usePageVisibility() {
  const [disabledPages, setDisabledPages] = usePersistentState<string[]>(STORAGE_KEY, [])

  function isPageEnabled(page: Page): boolean {
    if (ALWAYS_VISIBLE_PAGES.has(page)) return true
    return !disabledPages.includes(page)
  }

  function togglePage(page: Page) {
    if (ALWAYS_VISIBLE_PAGES.has(page)) return
    setDisabledPages(prev =>
      prev.includes(page) ? prev.filter(p => p !== page) : [...prev, page]
    )
  }

  return { disabledPages, isPageEnabled, togglePage }
}
