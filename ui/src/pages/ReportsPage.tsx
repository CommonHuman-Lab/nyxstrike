import { useState } from 'react'
import {
  BarChart2, CheckCircle, Clock, TrendingUp, FileText,
} from 'lucide-react'
import { StatCard } from '../components/StatCard'
import { type RunHistoryEntry } from '../types'
import './ReportsPage.css'

interface ReportsPageProps {
  runHistory: RunHistoryEntry[]
}

type GroupBy = 'tool' | 'target'

function extractTarget(e: RunHistoryEntry): string {
  const TARGET_KEYS = ['target', 'url', 'host', 'ip', 'domain', 'file']
  for (const k of TARGET_KEYS) {
    const v = e.params[k]
    if (v) return String(v)
  }
  const first = Object.values(e.params)[0]
  return first ? String(first) : '(no target)'
}

export default function ReportsPage({ runHistory }: ReportsPageProps) {
  const [groupBy, setGroupBy] = useState<GroupBy>('tool')
  const [search, setSearch] = useState('')

  const byTool = runHistory.reduce<Record<string, RunHistoryEntry[]>>((acc, e) => {
    ;(acc[e.tool] = acc[e.tool] || []).push(e)
    return acc
  }, {})

  const byTarget = runHistory.reduce<Record<string, RunHistoryEntry[]>>((acc, e) => {
    const t = extractTarget(e)
    ;(acc[t] = acc[t] || []).push(e)
    return acc
  }, {})

  const grouped = groupBy === 'tool' ? byTool : byTarget

  function stats(entries: RunHistoryEntry[]) {
    const ok = entries.filter(e => e.result.success).length
    const avgTime = entries.reduce((s, e) => s + e.result.execution_time, 0) / entries.length
    const last = entries.reduce((a, b) => a.ts > b.ts ? a : b)
    return { total: entries.length, ok, failed: entries.length - ok, avgTime, last }
  }

  const q = search.toLowerCase()
  const keys = Object.keys(grouped).filter(k => !q || k.toLowerCase().includes(q)).sort()

  const timeline = [...runHistory].sort((a, b) => a.ts.getTime() - b.ts.getTime()).slice(-50)

  if (runHistory.length === 0) return (
    <div className="page-content">
      <div className="tasks-empty">
        <FileText size={32} color="var(--text-dim)" />
        <p>No run history yet. Execute tools from the Run tab to see reports.</p>
      </div>
    </div>
  )

  return (
    <div className="page-content">
      <div className="kpi-row">
        <StatCard icon={<BarChart2 size={20} />} label="Total Runs" value={runHistory.length} sub="all time" accent="var(--blue)" />
        <StatCard
          icon={<CheckCircle size={20} />}
          label="Success Rate"
          value={`${((runHistory.filter(e => e.result.success).length / runHistory.length) * 100).toFixed(0)}%`}
          sub={`${runHistory.filter(e => e.result.success).length} ok · ${runHistory.filter(e => !e.result.success).length} failed`}
          accent="var(--green)"
        />
        <StatCard
          icon={<Clock size={20} />}
          label="Avg Time"
          value={`${(runHistory.reduce((s, e) => s + e.result.execution_time, 0) / runHistory.length).toFixed(1)}s`}
          sub="per run"
          accent="var(--purple)"
        />
        <StatCard
          icon={<TrendingUp size={20} />}
          label="Unique Tools"
          value={Object.keys(byTool).length}
          sub="used"
          accent="var(--amber)"
        />
      </div>

      <section className="section">
        <div className="section-header">
          <h3>Run Timeline <span className="section-meta">last {timeline.length}</span></h3>
        </div>
        <div className="reports-timeline">
          {timeline.map((e, i) => (
            <div
              key={i}
              className={`reports-timeline-dot ${e.result.success ? 'ok' : 'fail'}`}
              title={`${e.tool} — ${e.ts.toLocaleTimeString('en-GB')} — ${e.result.success ? 'ok' : 'failed'} (${e.result.execution_time.toFixed(1)}s)`}
            />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h3>Breakdown</h3>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              className="search-input mono"
              style={{ width: 180 }}
              placeholder="Search…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <button className={`cat-tab ${groupBy === 'tool' ? 'active' : ''}`} onClick={() => setGroupBy('tool')}>By Tool</button>
            <button className={`cat-tab ${groupBy === 'target' ? 'active' : ''}`} onClick={() => setGroupBy('target')}>By Target</button>
          </div>
        </div>
        <div className="reports-table">
          <div className="reports-thead">
            <span>{groupBy === 'tool' ? 'Tool' : 'Target'}</span>
            <span>Runs</span>
            <span>Success</span>
            <span>Failed</span>
            <span>Avg Time</span>
            <span>Last Run</span>
          </div>
          {keys.map(k => {
            const s = stats(grouped[k])
            const pct = (s.ok / s.total) * 100
            const col = pct >= 80 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--red)'
            return (
              <div key={k} className="reports-row">
                <span className="mono reports-key">{k}</span>
                <span className="mono">{s.total}</span>
                <span className="mono" style={{ color: 'var(--green)' }}>{s.ok}</span>
                <span className="mono" style={{ color: s.failed > 0 ? 'var(--red)' : 'var(--text-dim)' }}>{s.failed}</span>
                <span className="mono">{s.avgTime.toFixed(1)}s</span>
                <div className="reports-last-cell">
                  <span className="reports-pct-bar-bg">
                    <span className="reports-pct-bar-fill" style={{ width: `${pct}%`, background: col }} />
                  </span>
                  <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                    {s.last.ts.toLocaleDateString('en-GB')} {s.last.ts.toLocaleTimeString('en-GB')}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
