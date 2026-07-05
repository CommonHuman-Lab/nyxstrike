import { usePersistentState } from './usePersistentState'
import type { Page } from '../app/routing'
import { NAV_ENTRIES, MANDATORY_PAGE_IDS } from '../app/navRegistry'

/** Pages that cannot be disabled (always visible). */
export const ALWAYS_VISIBLE_PAGES: ReadonlySet<Page> = MANDATORY_PAGE_IDS

export interface PageConfig {
  page: Exclude<Page, 'session-detail'>
  label: string
  description: string
}

/** All navigable pages with human-readable metadata, derived from the nav registry. */
export const PAGE_CONFIGS: PageConfig[] = NAV_ENTRIES.map(({ id, label, description }) => ({
  page: id,
  label,
  description,
}))

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
