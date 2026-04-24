import { Activity, Clock, RefreshCw, Target } from 'lucide-react'
import type { SessionSummary } from '../../api'
import { fmtTs } from '../../shared/utils'
import { sessionName } from './utils'

export function SessionCard({
  session,
  onOpen,
}: {
  session: SessionSummary
  onOpen: (sessionId: string) => void
}) {
  const toolStatus = (session.metadata?.tool_status ?? {}) as Record<string, string>
  const lastRun = ((session.metadata?.last_run ?? null) as {
    tool?: string
    success?: boolean
    return_code?: number
    execution_time?: number
  } | null)

  return (
    <div className="session-card session-card--compact registry-card--clickable" onClick={() => onOpen(session.session_id)}>
      <div className="session-card-header">
        <div className="session-target">
          <Target size={13} color="var(--blue)" />
          <span className="mono">{session.target}</span>
        </div>
        <div className="session-card-header-badges">
          {session.risk_level && session.risk_level !== 'unknown' && (
            <span
              className={`session-risk session-risk--${session.risk_level.toLowerCase()}`}
              title={`Risk level: ${session.risk_level.toLowerCase()}`}
            >
              {session.risk_level.toLowerCase()}
            </span>
          )}
          {session.status && (
            <span className={`session-status session-status--${session.status}`}>{session.status}</span>
          )}
        </div>
      </div>

      <div className="session-card-meta">
        <span><Activity size={11} /> {session.total_findings} findings</span>
        <span><RefreshCw size={11} /> {session.iterations} iterations</span>
        <span><Clock size={11} /> {fmtTs(session.updated_at)}</span>
      </div>

      <div className="session-tools">
        {session.tools_executed.slice(0, 7).map(tool => (
          <span
            key={tool}
            className={`session-tool-chip mono session-tool-chip--${toolStatus[tool] === 'success' ? 'success' : toolStatus[tool] === 'failed' ? 'failed' : 'idle'}`}
          >
            {tool}
          </span>
        ))}
        {session.tools_executed.length > 7 && (
          <span className="session-tool-chip session-tool-chip--more">+{session.tools_executed.length - 7}</span>
        )}
      </div>

      <div className="session-card-footer">
        <span className="session-id mono">{session.session_id}</span>
        <span className="session-tool-chip mono">{sessionName(session)}</span>
      </div>

      {lastRun?.tool && (
        <div className="session-last-run mono">
          last: {lastRun.tool} | {lastRun.success ? 'OK' : 'FAIL'} | exit {lastRun.return_code ?? 0} | {(lastRun.execution_time ?? 0).toFixed(2)}s
        </div>
      )}
    </div>
  )
}
