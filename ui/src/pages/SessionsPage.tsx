import { useState, useEffect } from 'react'
import {
  RefreshCw, XCircle, Activity, Clock, CheckCircle,
  Layers, Target,
} from 'lucide-react'
import { api, type SessionsResponse, type SessionSummary } from '../api'
import { StatCard } from '../components/StatCard'
import './SessionsPage.css'

function fmtTs(ts: number) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString('en-GB')
}

function SessionCard({ s }: { s: SessionSummary }) {
  return (
    <div className="session-card">
      <div className="session-card-header">
        <div className="session-target">
          <Target size={13} color="var(--blue)" />
          <span className="mono">{s.target}</span>
        </div>
        {s.status && (
          <span className={`session-status session-status--${s.status}`}>{s.status}</span>
        )}
      </div>
      <div className="session-card-meta">
        <span><Activity size={11} /> {s.total_findings} findings</span>
        <span><RefreshCw size={11} /> {s.iterations} iterations</span>
        <span><Clock size={11} /> {fmtTs(s.updated_at)}</span>
      </div>
      {s.tools_executed.length > 0 && (
        <div className="session-tools">
          {s.tools_executed.slice(0, 8).map(t => (
            <span key={t} className="session-tool-chip mono">{t}</span>
          ))}
          {s.tools_executed.length > 8 && (
            <span className="session-tool-chip session-tool-chip--more">+{s.tools_executed.length - 8}</span>
          )}
        </div>
      )}
      <div className="session-id mono">{s.session_id}</div>
    </div>
  )
}

export default function SessionsPage() {
  const [data, setData] = useState<SessionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.sessions()
      .then(r => { setData(r); setError(null) })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  function refresh() {
    setLoading(true)
    api.sessions()
      .then(r => { setData(r); setError(null) })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }

  if (loading) return (
    <div className="loading-state">
      <RefreshCw size={20} className="spin" color="var(--green)" />
      <p>Loading sessions…</p>
    </div>
  )
  if (error) return (
    <div className="error-banner"><XCircle size={16} /> {error}</div>
  )

  const active = data?.active ?? []
  const completed = data?.completed ?? []

  return (
    <div className="page-content">
      <div className="kpi-row">
        <StatCard
          icon={<Layers size={20} />}
          label="Active Sessions"
          value={active.length}
          sub="in progress"
          accent={active.length > 0 ? 'var(--green)' : 'var(--text-dim)'}
        />
        <StatCard icon={<CheckCircle size={20} />} label="Completed" value={completed.length} sub="archived" accent="var(--blue)" />
        <StatCard
          icon={<Activity size={20} />}
          label="Total Findings"
          value={[...active, ...completed].reduce((s, x) => s + x.total_findings, 0)}
          sub="across all sessions"
          accent="var(--amber)"
        />
        <StatCard
          icon={<Target size={20} />}
          label="Unique Targets"
          value={new Set([...active, ...completed].map(s => s.target)).size}
          sub="scanned"
          accent="var(--purple)"
        />
      </div>

      <section className="section">
        <div className="section-header">
          <h3>Active Sessions <span className="badge">{active.length}</span></h3>
          <button className="icon-btn" onClick={refresh} title="Refresh">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
          </button>
        </div>
        {active.length === 0 ? (
          <div className="tasks-empty">
            <Layers size={28} color="var(--text-dim)" />
            <p>No active sessions. Start a bug bounty or CTF workflow via the MCP to create one.</p>
          </div>
        ) : (
          <div className="sessions-grid">
            {active.map(s => <SessionCard key={s.session_id} s={s} />)}
          </div>
        )}
      </section>

      <section className="section">
        <div className="section-header">
          <h3>Completed Sessions <span className="badge">{completed.length}</span></h3>
        </div>
        {completed.length === 0 ? (
          <p className="empty-state">No completed sessions yet.</p>
        ) : (
          <div className="sessions-grid">
            {completed.map(s => <SessionCard key={s.session_id} s={s} />)}
          </div>
        )}
      </section>
    </div>
  )
}
