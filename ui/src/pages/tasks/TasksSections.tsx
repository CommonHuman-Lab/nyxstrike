import {
  RefreshCw, Cpu, MemoryStick, Wifi,
  Activity, PauseCircle, PlayCircle, StopCircle, ListTodo,
} from 'lucide-react'
import type { ProcessDashboardResponse } from '../../api'
import type { StreamStatus } from './useProcessDashboard'

function StreamStatusDot({ status }: { status: StreamStatus }) {
  let color = 'var(--amber)'
  if (status === 'streaming') color = 'var(--green)'
  else if (status === 'polling') color = 'var(--blue)'
  else if (status === 'error') color = 'var(--red)'

  return (
    <span
      className="stream-dot"
      style={{
        display: 'inline-block',
        marginRight: 5,
        width: 10,
        height: 10,
        borderRadius: '50%',
        background: color,
        verticalAlign: 'middle',
      }}
      title={
        status === 'streaming' ? 'Live update (SSE)'
          : status === 'polling' ? 'Polling (no stream)'
            : status === 'error' ? 'Offline/error'
              : 'Unknown'
      }
    />
  )
}

export function WorkerPoolSection({
  data,
  poolStats,
  streamStatus,
}: {
  data: ProcessDashboardResponse | null
  poolStats: Record<string, unknown>
  streamStatus: StreamStatus
}) {
  const load = data?.system_load

  return (
    <section className="section">
      <div className="section-header">
        <h3>Worker Pool <StreamStatusDot status={streamStatus} /></h3>
        <span className="section-meta mono">{data?.timestamp?.slice(11, 19)}</span>
      </div>
      <div className="tasks-pool-row">
        {load && (
          <>
            <div className="tasks-pool-stat">
              <Cpu size={14} color="var(--green)" />
              <span className="tasks-pool-label">CPU</span>
              <span className="tasks-pool-val mono">{load.cpu_percent.toFixed(1)}%</span>
            </div>
            <div className="tasks-pool-stat">
              <MemoryStick size={14} color="var(--blue)" />
              <span className="tasks-pool-label">Memory</span>
              <span className="tasks-pool-val mono">{load.memory_percent.toFixed(1)}%</span>
            </div>
            <div className="tasks-pool-stat">
              <Wifi size={14} color="var(--text-dim)" />
              <span className="tasks-pool-label">Connections</span>
              <span className="tasks-pool-val mono">{load.active_connections}</span>
            </div>
          </>
        )}
        {Object.entries(poolStats)
          .filter(([k]) => !['success', 'timestamp'].includes(k))
          .slice(0, 6)
          .map(([k, v]) => (
            <div key={k} className="tasks-pool-stat">
              <Activity size={14} color="var(--text-dim)" />
              <span className="tasks-pool-label">{k.replace(/_/g, ' ')}</span>
              <span className="tasks-pool-val mono">{String(v)}</span>
            </div>
          ))}
      </div>
    </section>
  )
}

export function ProcessesSection({
  processes,
  actionMsg,
  onRefresh,
  onPause,
  onResume,
  onTerminate,
}: {
  processes: ProcessDashboardResponse['processes']
  actionMsg: string | null
  onRefresh: () => Promise<void>
  onPause: (pid: number) => Promise<void>
  onResume: (pid: number) => Promise<void>
  onTerminate: (pid: number) => Promise<void>
}) {
  return (
    <section className="section">
      <div className="section-header">
        <h3>Active Processes <span className="badge">{processes.length}</span></h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {actionMsg && <span className="section-meta" style={{ color: 'var(--amber)' }}>{actionMsg}</span>}
          <button className="icon-btn" onClick={onRefresh} title="Refresh"><RefreshCw size={14} /></button>
        </div>
      </div>

      {processes.length === 0 ? (
        <div className="tasks-empty">
          <ListTodo size={32} color="var(--text-dim)" />
          <p>No active processes</p>
        </div>
      ) : (
        <div className="tasks-table">
          <div className="tasks-thead">
            <span>PID</span>
            <span>Command</span>
            <span>Status</span>
            <span>Progress</span>
            <span>Runtime</span>
            <span>ETA</span>
            <span>Actions</span>
          </div>
          {processes.map(process => {
            const pct = parseFloat(process.progress_percent) || 0
            const barColor = process.status === 'running'
              ? 'var(--green)'
              : process.status === 'paused'
                ? 'var(--amber)'
                : 'var(--text-dim)'

            return (
              <div key={process.pid} className="tasks-row">
                <span className="mono tasks-pid">{process.pid}</span>
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
                  {process.status !== 'paused' && (
                    <button className="tasks-btn tasks-btn--pause" title="Pause" onClick={() => onPause(process.pid)}>
                      <PauseCircle size={14} />
                    </button>
                  )}
                  {process.status === 'paused' && (
                    <button className="tasks-btn tasks-btn--resume" title="Resume" onClick={() => onResume(process.pid)}>
                      <PlayCircle size={14} />
                    </button>
                  )}
                  <button className="tasks-btn tasks-btn--stop" title="Terminate" onClick={() => onTerminate(process.pid)}>
                    <StopCircle size={14} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
