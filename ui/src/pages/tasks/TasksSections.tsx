import {
  RefreshCw, Activity, Cpu, MemoryStick, Wifi,
  PauseCircle, PlayCircle, StopCircle, ListTodo,
} from 'lucide-react'
import type { ProcessDashboardResponse } from '../../api'
import { StatCard } from '../../components/StatCard'
import type { StreamStatus } from './useProcessDashboard'
import { useEscapeClose } from '../../hooks/useEscapeClose'

function formatStatValue(value: unknown): string {
  if (value === null || value === undefined) return 'n/a'
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'n/a'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return `${value.length} items`
  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>
    const parts = Object.entries(obj)
      .slice(0, 2)
      .map(([k, v]) => `${k}:${typeof v === 'number' ? v : typeof v}`)
    return parts.length ? parts.join(' · ') : 'object'
  }
  return String(value)
}

function summarizeObjectKeys(value: unknown): string {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return ''
  const keys = Object.keys(value as Record<string, unknown>)
  if (keys.length === 0) return 'No entries'
  return `${keys.length} entries`
}

export function WorkerPoolSection({
  data,
  streamStatus,
}: {
  data: ProcessDashboardResponse | null
  streamStatus: StreamStatus
}) {
  const load = data?.system_load
  const statusLabel = streamStatus === 'streaming' ? 'Live' : streamStatus === 'polling' ? 'Polling' : 'Offline'
  const statusAccent = streamStatus === 'streaming' ? 'var(--green)' : streamStatus === 'polling' ? 'var(--blue)' : 'var(--red)'
  const timestampLabel = data?.timestamp?.slice(11, 19) ?? 'n/a'

  return (
    <div className="kpi-row">
      <StatCard
        icon={<Activity size={20} />}
        label="Worker Pool"
        value={statusLabel}
        sub={`updated ${timestampLabel}`}
        accent={statusAccent}
      />
      <StatCard
        icon={<Cpu size={20} />}
        label="CPU"
        value={load ? `${load.cpu_percent.toFixed(1)}%` : 'n/a'}
        sub="system load"
        accent="var(--green)"
      />
      <StatCard
        icon={<MemoryStick size={20} />}
        label="Memory"
        value={load ? `${load.memory_percent.toFixed(1)}%` : 'n/a'}
        sub="system memory"
        accent="var(--blue)"
      />
      <StatCard
        icon={<Wifi size={20} />}
        label="Connections"
        value={load ? load.active_connections : 'n/a'}
        sub="active sockets"
        accent="var(--amber)"
      />
    </div>
  )
}

export function ProcessesSection({
  processes,
  actionMsg,
  streamStatus,
  onRefresh,
  onPause,
  onResume,
  onTerminate,
  onCancelAiTask,
}: {
  processes: ProcessDashboardResponse['processes']
  actionMsg: string | null
  streamStatus: StreamStatus
  onRefresh: () => Promise<void>
  onPause: (pid: number) => Promise<void>
  onResume: (pid: number) => Promise<void>
  onTerminate: (pid: number) => Promise<void>
  onCancelAiTask: (taskId: string) => Promise<void>
}) {
  return (
    <section className="section">
      <div className="section-header">
        <h3>Active Processes <span className="badge">{processes.length}</span></h3>
        <div className="section-header-controls">
          {actionMsg && <span className="section-meta" style={{ color: 'var(--amber)' }}>{actionMsg}</span>}
          {streamStatus !== 'streaming' && (
            <button className="icon-btn" onClick={onRefresh} title="Refresh"><RefreshCw size={14} /></button>
          )}
        </div>
      </div>

      {processes.length === 0 ? (
        <div className="tasks-empty">
          <ListTodo size={32} color="var(--text-dim)" />
          <p>No active processes</p>
        </div>
      ) : (
        <div className="tasks-table">
          <div className="tasks-thead table-thead">
            <span>PID</span>
            <span>Command</span>
            <span>Status</span>
            <span>Progress</span>
            <span>Runtime</span>
            <span>ETA</span>
            <span>Actions</span>
          </div>
          {processes.map(process => {
            const isAiTask = Boolean(process.ai_task)
            const rowKey = isAiTask ? (process.task_id ?? process.command) : String(process.pid)
            const pct = parseFloat(process.progress_percent) || 0
            const barColor = process.status === 'running'
              ? 'var(--green)'
              : process.status === 'paused'
                ? 'var(--amber)'
                : 'var(--text-dim)'

            return (
              <div key={rowKey} className="tasks-row">
                <span className="mono tasks-pid" title={isAiTask ? (process.task_id ?? '') : ''}>
                  {isAiTask ? 'AI' : process.pid}
                </span>
                <span className="mono tasks-cmd" title={process.command}>{process.command}</span>
                <span className={`tasks-status tasks-status--${process.status}`}>{process.status}</span>
                <div className="tasks-progress">
                  <div className="tasks-progress-bar-bg">
                    <div className="tasks-progress-bar-fill" style={{ width: `${Math.min(100, pct)}%`, background: barColor }} />
                  </div>
                  <span className="tasks-pct mono">{process.progress_percent}</span>
                </div>
                <span className="mono">{process.runtime}</span>
                <span className="mono">{process.eta}</span>
                <div className="tasks-actions">
                  {!isAiTask && process.status !== 'paused' && (
                    <button className="tasks-btn tasks-btn--pause" title="Pause" onClick={() => onPause(process.pid as number)}>
                      <PauseCircle size={14} />
                    </button>
                  )}
                  {!isAiTask && process.status === 'paused' && (
                    <button className="tasks-btn tasks-btn--resume" title="Resume" onClick={() => onResume(process.pid as number)}>
                      <PlayCircle size={14} />
                    </button>
                  )}
                  {isAiTask ? (
                    <button className="tasks-btn tasks-btn--stop" title="Cancel AI task"
                            onClick={() => onCancelAiTask(process.task_id ?? '')}>
                      <StopCircle size={14} />
                    </button>
                  ) : (
                    <button className="tasks-btn tasks-btn--stop" title="Terminate" onClick={() => onTerminate(process.pid as number)}>
                      <StopCircle size={14} />
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

export function PoolStatsModal({
  open,
  poolStats,
  onClose,
}: {
  open: boolean
  poolStats: Record<string, unknown>
  onClose: () => void
}) {
  useEscapeClose(open, onClose)

  if (!open) return null

  const entries = Object.entries(poolStats).filter(([k]) => !['success', 'timestamp'].includes(k))

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal modal--wide" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-name">Worker Pool Stats</span>
          </div>
          <button className="modal-close" onClick={onClose}>Close</button>
        </div>
        <div className="modal-body">
          {entries.length === 0 ? (
            <div className="tasks-empty tasks-empty--compact">
              <ListTodo size={24} color="var(--text-dim)" />
              <p>No stats available</p>
            </div>
          ) : (
            <div className="tasks-stats-grid">
              {entries.map(([k, v]) => (
                <div key={k} className="tasks-stats-item">
                  <span className="tasks-stats-key">{k.replace(/_/g, ' ')}</span>
                  <span
                    className="tasks-stats-val mono"
                    title={typeof v === 'object' ? JSON.stringify(v) : undefined}
                  >
                    {formatStatValue(v)}
                  </span>
                  {typeof v === 'object' && !Array.isArray(v) && (
                    <span className="tasks-stats-sub">{summarizeObjectKeys(v)}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
