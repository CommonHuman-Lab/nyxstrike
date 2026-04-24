import { lazy, Suspense } from 'react'
import { RefreshCw } from 'lucide-react'
import type { Dispatch, RefObject, SetStateAction } from 'react'
import type {
  Tool,
  ToolExecResponse,
  WebDashboardResponse,
} from '../api'
import type { RunHistoryEntry } from '../shared/types'
import type { ThemeId } from './themes'
import type { Page } from './routing'

// Eagerly loaded — always visible on any page
import { DashboardPage } from '../pages/dashboard/DashboardPage'

// Lazy-loaded page chunks — each becomes its own JS chunk
const RunPage           = lazy(() => import('../pages/run/RunPage').then(m => ({ default: m.RunPage })))
const LogsPage          = lazy(() => import('../pages/logview/LogsPage'))
const SettingsPage      = lazy(() => import('../pages/settings/SettingsPage'))
const HelpPage          = lazy(() => import('../pages/help/HelpPage'))
const TasksPage         = lazy(() => import('../pages/tasks/TasksPage'))
const ToolsPage         = lazy(() => import('../pages/tools/ToolsPage'))
const PluginsPage       = lazy(() => import('../pages/plugins/PluginsPage'))
const ReportsPage       = lazy(() => import('../pages/reports/ReportsPage'))
const SessionsPage      = lazy(() => import('../pages/sessions/SessionsPage'))
const SessionDetailPage = lazy(() => import('../pages/sessions/SessionDetailPage'))

/** Minimal spinner shown while a lazy chunk is loading */
function PageLoader() {
  return (
    <div className="loading-state">
      <RefreshCw size={24} className="spin" color="var(--green)" />
    </div>
  )
}

interface MainContentProps {
  page: Page
  demo: boolean
  tools: Tool[]
  health: WebDashboardResponse | null
  toolsStatusWithParents: Record<string, boolean>
  runHistory: RunHistoryEntry[]
  setRunHistory: Dispatch<SetStateAction<RunHistoryEntry[]>>
  fetchServerRunHistory: () => Promise<void>
  clearServerRunHistory: () => Promise<void>
  commandToolRequest?: { toolName: string; requestId: number } | null
  onCommandToolHandled?: () => void
  openSessionDetail: (sessionId: string) => void
  activeSessionId: string | null
  setPage: (page: Page) => void
  addBrowserRunEntry: (tool: string, params: Record<string, unknown>, result: ToolExecResponse) => void
  logLines: string[]
  logAutoScroll: boolean
  setLogAutoScroll: Dispatch<SetStateAction<boolean>>
  logLimit: number
  setLogLimit: Dispatch<SetStateAction<number>>
  logEndRef: RefObject<HTMLDivElement | null>
  loading: boolean
  error: string | null
  toolCategories: Record<string, string[]>
  themeId: ThemeId
  setThemeId: (theme: ThemeId) => void
  reduceTextureEffects: boolean
  setReduceTextureEffects: (value: boolean) => void
  /** Demo data injected from App (avoids importing demo.ts here) */
  demoProcesses?: unknown
  demoSessions?: unknown
  demoCpuHistory?: unknown
}

export function MainContent({
  page,
  demo,
  tools,
  health,
  toolsStatusWithParents,
  runHistory,
  setRunHistory,
  fetchServerRunHistory,
  clearServerRunHistory,
  commandToolRequest,
  onCommandToolHandled,
  openSessionDetail,
  activeSessionId,
  setPage,
  addBrowserRunEntry,
  logLines,
  logAutoScroll,
  setLogAutoScroll,
  logLimit,
  setLogLimit,
  logEndRef,
  loading,
  error,
  toolCategories,
  themeId,
  setThemeId,
  reduceTextureEffects,
  setReduceTextureEffects,
  demoProcesses,
  demoSessions,
  demoCpuHistory,
}: MainContentProps) {
  return (
    <main className={`main${page === 'run' ? ' main--flush' : ''}`}>
      <Suspense fallback={<PageLoader />}>
        {page === 'settings' && (
          <SettingsPage
            themeId={themeId}
            setThemeId={setThemeId}
            reduceTextureEffects={reduceTextureEffects}
            setReduceTextureEffects={setReduceTextureEffects}
          />
        )}
        {page === 'help' && <HelpPage />}
        {page === 'run' && (
          <RunPage
            tools={tools}
            toolsStatus={toolsStatusWithParents}
            runHistory={runHistory}
            setRunHistory={setRunHistory}
            commandToolRequest={commandToolRequest}
            onCommandToolHandled={onCommandToolHandled}
            onRefresh={fetchServerRunHistory}
            onClearHistory={clearServerRunHistory}
          />
        )}
        {page === 'tasks' && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <TasksPage demoData={demo && demoProcesses ? { processes: demoProcesses as any } : undefined} />
        )}
        {page === 'tools' && health && (
          <ToolsPage health={health} tools={tools} toolsStatus={toolsStatusWithParents} />
        )}
        {page === 'plugins' && <PluginsPage />}
        {page === 'reports' && <ReportsPage runHistory={runHistory} />}
        {page === 'sessions' && (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <SessionsPage demoData={demo && demoSessions ? { sessions: demoSessions as any } : undefined} onOpenSession={openSessionDetail} />
        )}
        {page === 'session-detail' && activeSessionId && (
          <SessionDetailPage
            sessionId={activeSessionId}
            tools={tools}
            onBack={() => setPage('sessions')}
            onToolRun={addBrowserRunEntry}
            llmAvailable={health?.llm_status?.available ?? false}
          />
        )}
        {page === 'logs' && (
          <LogsPage
            logLines={logLines}
            logAutoScroll={logAutoScroll}
            setLogAutoScroll={setLogAutoScroll}
            logLimit={logLimit}
            setLogLimit={setLogLimit}
            logEndRef={logEndRef}
          />
        )}
        {page === 'dashboard' && (
          <>
            {loading && !health && (
              <div className="loading-state">
                <RefreshCw size={24} className="spin" color="var(--green)" />
                <p>Connecting to server…</p>
              </div>
            )}
            {error && !health && (
              <div className="error-banner">
                {error} — is the server running on port 8888?
              </div>
            )}
            {health && (
              <DashboardPage
                health={health}
                tools={tools}
                runHistory={runHistory}
                loading={loading}
                error={error}
                toolCategories={toolCategories}
                demo={demo}
                demoCpuHistory={demoCpuHistory}
              />
            )}
          </>
        )}
      </Suspense>
    </main>
  )
}
