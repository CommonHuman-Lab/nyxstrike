import { RefreshCw } from 'lucide-react'
import type { Dispatch, RefObject, SetStateAction } from 'react'
import type {
  Tool,
  ToolExecResponse,
  WebDashboardResponse,
} from '../api'
import type { HistoryPoint, RunHistoryEntry } from '../types'
import { DashboardPage } from '../pages/dashboard/DashboardPage'
import { RunPage } from '../pages/run/RunPage'
import LogsPage from '../pages/logview/LogsPage'
import SettingsPage from '../pages/settings/SettingsPage'
import HelpPage from '../pages/help/HelpPage'
import TasksPage from '../pages/tasks/TasksPage'
import ToolsPage from '../pages/tools/ToolsPage'
import ReportsPage from '../pages/reports/ReportsPage'
import SessionsPage from '../pages/sessions/SessionsPage'
import SessionDetailPage from '../pages/sessions/SessionDetailPage'
import { DEMO_PROCESSES, DEMO_SESSIONS } from '../demo'
import type { Page } from './routing'

interface MainContentProps {
  page: Page
  demo: boolean
  tools: Tool[]
  health: WebDashboardResponse | null
  toolsStatusWithParents: Record<string, boolean>
  runHistory: RunHistoryEntry[]
  setRunHistory: Dispatch<SetStateAction<RunHistoryEntry[]>>
  fetchServerRunHistory: () => Promise<void>
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
  history: HistoryPoint[]
  toolCategories: Record<string, string[]>
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
  history,
  toolCategories,
}: MainContentProps) {
  return (
    <main className={`main${page === 'run' ? ' main--flush' : ''}`}>
      {page === 'settings' && <SettingsPage />}
      {page === 'help' && <HelpPage />}
      {page === 'run' && (
        <RunPage
          tools={tools}
          toolsStatus={toolsStatusWithParents}
          runHistory={runHistory}
          setRunHistory={setRunHistory}
          onRefresh={fetchServerRunHistory}
        />
      )}
      {page === 'tasks' && <TasksPage demoData={demo ? { processes: DEMO_PROCESSES } : undefined} />}
      {page === 'tools' && health && (
        <ToolsPage health={health} tools={tools} toolsStatus={toolsStatusWithParents} />
      )}
      {page === 'reports' && <ReportsPage runHistory={runHistory} />}
      {page === 'sessions' && <SessionsPage demoData={demo ? { sessions: DEMO_SESSIONS } : undefined} onOpenSession={openSessionDetail} />}
      {page === 'session-detail' && activeSessionId && (
        <SessionDetailPage
          sessionId={activeSessionId}
          tools={tools}
          onBack={() => setPage('sessions')}
          onToolRun={addBrowserRunEntry}
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
              history={history}
              runHistory={runHistory}
              loading={loading}
              error={error}
              toolCategories={toolCategories}
            />
          )}
        </>
      )}
    </main>
  )
}
