import { useState } from 'react'
import { FlaskConical } from 'lucide-react'

// isDemoMode/exitDemo are tiny helpers — import eagerly (no data payload).
import { isDemoMode, exitDemo } from './app/demoUtils'
import { TokenGate } from './components/TokenGate'
import { ToastProvider } from './components/ToastProvider'
import { getToolsStatusWithParents } from './app/tools'
import { TopBar } from './app/TopBar'
import { Sidebar } from './app/Sidebar'
import { MainContent } from './app/MainContent'
import { useThemePreferences } from './app/useThemePreferences'
import { useAppRouting } from './app/useAppRouting'
import { useLogStream } from './app/useLogStream'
import { useCommandPalette } from './app/useCommandPalette'
import { useAuth } from './app/useAuth'
import { useRunHistory } from './app/useRunHistory'
import { useDashboardData } from './app/useDashboardData'
import { useDemoBootstrap } from './app/useDemoBootstrap'
import { CommandPalette } from './components/CommandPalette'
import { ReportGenerationBubble } from './components/ReportGenerationBubble'
import { ChatWidget } from './components/ChatWidget'
import { usePageVisibility } from './hooks/usePageVisibility'
import { usePersistentState } from './hooks/usePersistentState'
import { useEscapeClose } from './hooks/useEscapeClose'
import './App.css'

export default function App() {
  const [demo] = useState(isDemoMode)

  const { isPageEnabled, togglePage } = usePageVisibility()
  const { page, activeSessionId, sidebarMobileOpen, setSidebarMobileOpen, setPage, openSessionDetail } = useAppRouting(isPageEnabled)

  const [sidebarCollapsed, setSidebarCollapsed] = usePersistentState('nyxstrike_sidebar_collapsed', false)
  useEscapeClose(sidebarMobileOpen, () => setSidebarMobileOpen(false))

  const { logLines, logAutoScroll, setLogAutoScroll, logLimit, setLogLimit, logEndRef, applyDemoLogLines } = useLogStream({ demo, page })

  const { authed, needsAuth, setAuthed, setNeedsAuth } = useAuth({
    demo,
    onProbeSuccess: h => dashboardOnProbeSuccess(h),
    onLoadingDone: () => dashboardOnProbeLoadingDone(),
  })
  const {
    health, tools, lastRefresh, loading, error, isStreaming, streamingError, toolCategories,
    fetchAll, applyDemoSnapshot,
    onProbeSuccess: dashboardOnProbeSuccess, onProbeLoadingDone: dashboardOnProbeLoadingDone,
  } = useDashboardData({
    demo, authed,
    onUnauthorized: () => { setNeedsAuth(true); setAuthed(false) },
  })
  const { runHistory, setRunHistory, addBrowserRunEntry, fetchServerRunHistory, clearServerRunHistory } = useRunHistory(demo, authed)

  const { demoProcesses, demoSessions, demoCpuHistory } = useDemoBootstrap({
    demo,
    onSnapshot: applyDemoSnapshot,
    onRunHistory: setRunHistory,
    onLogLines: applyDemoLogLines,
  })

  const {
    paletteOpen, setPaletteOpen, commandToolRequest, clearCommandToolRequest,
    showPaletteHint, dismissPaletteHint, openCommandPalette, handleCommandSelectTool,
  } = useCommandPalette(setPage)
  const { themeId, setThemeId, reduceTextureEffects, setReduceTextureEffects } = useThemePreferences()

  if (needsAuth && !authed) {
    return <TokenGate onUnlocked={() => { setAuthed(true); setNeedsAuth(false) }} />
  }

  const toolsStatusWithParents = getToolsStatusWithParents(tools, health?.tools_status ?? {})

  return (
    <ToastProvider>
      <div className={demo ? 'layout layout--demo' : 'layout'}>
        <CommandPalette
          open={paletteOpen}
          onClose={() => setPaletteOpen(false)}
          setPage={setPage}
          tools={tools}
          onSelectTool={handleCommandSelectTool}
        />
        <ReportGenerationBubble />
        <ChatWidget
          llmAvailable={health?.llm_status?.available ?? false}
          currentPage={page}
          currentSessionId={activeSessionId}
        />
        {demo && (
          <div className="demo-banner">
            <FlaskConical size={13} />
            <span>Demo mode — all data is synthetic</span>
            <button onClick={() => { exitDemo(); window.location.href = window.location.pathname + window.location.hash }}>Exit demo</button>
          </div>
        )}

        <TopBar
          lastRefresh={lastRefresh}
          demo={demo}
          isStreaming={isStreaming}
          streamingError={streamingError}
          health={health}
          error={error}
          loading={loading}
          fetchAll={fetchAll}
          themeId={themeId}
          setThemeId={setThemeId}
          reduceTextureEffects={reduceTextureEffects}
          setReduceTextureEffects={setReduceTextureEffects}
          onOpenCommandPalette={openCommandPalette}
          onSignOut={() => { setAuthed(false); setNeedsAuth(true) }}
          onToggleMobileSidebar={() => setSidebarMobileOpen(v => !v)}
        />

        {showPaletteHint && (
          <div className="palette-hint-floating" role="status" aria-live="polite">
            <button className="palette-hint-main" onClick={openCommandPalette} title="Open command palette">
              <span className="palette-hint-title">Try Command Palette</span>
              <span className="palette-hint-kbd mono">Ctrl/Cmd + K</span>
            </button>
            <button className="palette-hint-close" onClick={dismissPaletteHint} title="Dismiss hint">x</button>
          </div>
        )}

        <div
          className="app-body"
          style={{ '--sidebar-w': sidebarCollapsed ? '3.25rem' : '13rem' } as React.CSSProperties}
        >
          <Sidebar
            page={page}
            setPage={setPage}
            isPageEnabled={isPageEnabled}
            collapsed={sidebarCollapsed}
            onToggleCollapsed={() => setSidebarCollapsed(v => !v)}
            mobileOpen={sidebarMobileOpen}
            onCloseMobile={() => setSidebarMobileOpen(false)}
          />
          {sidebarMobileOpen && (
            <div className="sidebar-backdrop" onClick={() => setSidebarMobileOpen(false)} />
          )}

          <MainContent
            page={page}
            demo={demo}
            tools={tools}
            health={health}
            toolsStatusWithParents={toolsStatusWithParents}
            runHistory={runHistory}
            setRunHistory={setRunHistory}
            fetchServerRunHistory={fetchServerRunHistory}
            clearServerRunHistory={clearServerRunHistory}
            commandToolRequest={commandToolRequest}
            onCommandToolHandled={clearCommandToolRequest}
            openSessionDetail={openSessionDetail}
            activeSessionId={activeSessionId}
            setPage={setPage}
            addBrowserRunEntry={addBrowserRunEntry}
            logLines={logLines}
            logAutoScroll={logAutoScroll}
            setLogAutoScroll={setLogAutoScroll}
            logLimit={logLimit}
            setLogLimit={setLogLimit}
            logEndRef={logEndRef}
            loading={loading}
            error={error}
            toolCategories={toolCategories}
            themeId={themeId}
            setThemeId={setThemeId}
            reduceTextureEffects={reduceTextureEffects}
            setReduceTextureEffects={setReduceTextureEffects}
            demoProcesses={demoProcesses}
            demoSessions={demoSessions}
            isPageEnabled={isPageEnabled}
            togglePage={togglePage}
            demoCpuHistory={demoCpuHistory}
          />
        </div>
      </div>
    </ToastProvider>
  )
}
