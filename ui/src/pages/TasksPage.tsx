import { useState, useEffect, useRef } from 'react'
import {
  RefreshCw, XCircle, ListTodo, Cpu, MemoryStick, Wifi,
  Activity, PauseCircle, PlayCircle, StopCircle,
} from 'lucide-react'
import { api, type ProcessDashboardResponse } from '../api'
import './TasksPage.css'

export default function TasksPage() {
  const [data, setData] = useState<ProcessDashboardResponse | null>(null)
  const [poolStats, setPoolStats] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  async function fetchData() {
    try {
      const [dash, pool] = await Promise.all([api.processDashboard(), api.processPoolStats()])
      setData(dash)
      setPoolStats(pool as Record<string, unknown>)
      setError(null)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    pollRef.current = setInterval(fetchData, 3000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  async function doAction(fn: () => Promise<{ success: boolean; message?: string; error?: string }>, label: string) {
    try {
      const r = await fn()
      setActionMsg(r.success ? (r.message ?? label + ' OK') : (r.error ?? label + ' failed'))
    } catch (e) {
      setActionMsg(String(e))
    }
    setTimeout(() => setActionMsg(null), 3000)
    fetchData()
  }

  if (loading && !data) return (
    <div className="loading-state">
      <RefreshCw size={20} className="spin" color="var(--green)" />
      <p>Loading tasks…</p>
    </div>
  )
  if (error && !data) return (
    <div className="error-banner"><XCircle size={16} /> {error}</div>
  )

  const processes = data?.processes ?? []
  const load = data?.system_load

  return (
    <div className="page-content">
      {poolStats && (
        <section className="section">
          <div className="section-header">
            <h3>Worker Pool</h3>
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
              ))
            }
          </div>
        </section>
      )}

      <section className="section">
        <div className="section-header">
          <h3>Active Processes <span className="badge">{processes.length}</span></h3>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {actionMsg && <span className="section-meta" style={{ color: 'var(--amber)' }}>{actionMsg}</span>}
            <button className="icon-btn" onClick={fetchData} title="Refresh"><RefreshCw size={14} /></button>
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
            {processes.map(p => {
              const pct = parseFloat(p.progress_percent) || 0
              const barColor = p.status === 'running' ? 'var(--green)' : p.status === 'paused' ? 'var(--amber)' : 'var(--text-dim)'
              return (
                <div key={p.pid} className="tasks-row">
                  <span className="mono tasks-pid">{p.pid}</span>
                  <span className="mono tasks-cmd" title={p.command}>{p.command}</span>
                  <span className={`tasks-status tasks-status--${p.status}`}>{p.status}</span>
                  <div className="tasks-progress">
                    <div className="tasks-progress-bar-bg">
                      <div className="tasks-progress-bar-fill" style={{ width: `${Math.min(100, pct)}%`, background: barColor }} />
                    </div>
                    <span className="tasks-pct mono">{p.progress_percent}</span>
                  </div>
                  <span className="mono">{p.runtime}</span>
                  <span className="mono">{p.eta}</span>
                  <div className="tasks-actions">
                    {p.status !== 'paused' && (
                      <button className="tasks-btn tasks-btn--pause" title="Pause" onClick={() => doAction(() => api.pauseProcess(p.pid), 'Paused')}>
                        <PauseCircle size={14} />
                      </button>
                    )}
                    {p.status === 'paused' && (
                      <button className="tasks-btn tasks-btn--resume" title="Resume" onClick={() => doAction(() => api.resumeProcess(p.pid), 'Resumed')}>
                        <PlayCircle size={14} />
                      </button>
                    )}
                    <button className="tasks-btn tasks-btn--stop" title="Terminate" onClick={() => doAction(() => api.terminateProcess(p.pid), 'Terminated')}>
                      <StopCircle size={14} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
