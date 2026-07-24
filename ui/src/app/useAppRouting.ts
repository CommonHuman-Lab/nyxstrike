import { useEffect, useState } from 'react'
import { routeFromHash, type Page } from './routing'

export function useAppRouting(isPageEnabled: (page: Page) => boolean) {
  const initialRoute = routeFromHash()
  const [page, setPageState] = useState<Page>(initialRoute.page)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(initialRoute.sessionId)
  const [sidebarMobileOpen, setSidebarMobileOpen] = useState(false)

  function setPage(p: Page) {
    if (p === 'session-detail') return
    window.location.hash = `/${p === 'dashboard' ? '' : p}`
    setPageState(p)
    setActiveSessionId(null)
    setSidebarMobileOpen(false)
  }

  function openSessionDetail(sessionId: string) {
    window.location.hash = `/sessions/${sessionId}`
    setPageState('session-detail')
    setActiveSessionId(sessionId)
    setSidebarMobileOpen(false)
  }

  // Keep state in sync if the user presses Back/Forward
  useEffect(() => {
    function onHashChange() {
      const route = routeFromHash()
      setPageState(route.page)
      setActiveSessionId(route.sessionId)
      setSidebarMobileOpen(false)
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  // If the active page gets disabled, fall back to dashboard
  useEffect(() => {
    if (!isPageEnabled(page)) {
      setPage('dashboard')
    }
  }, [page, isPageEnabled])

  return { page, activeSessionId, sidebarMobileOpen, setSidebarMobileOpen, setPage, openSessionDetail }
}
