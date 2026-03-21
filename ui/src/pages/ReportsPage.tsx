import { useState } from 'react'
import {
  BarChart2, CheckCircle, Clock, TrendingUp, FileText, ChevronDown, ChevronRight,
} from 'lucide-react'
import { StatCard } from '../components/StatCard'
import { RunResultModal } from '../components/RunResultModal'
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

// Group timeline entries by date label
function groupByDate(entries: RunHistoryEntry[]): { label: string; entries: RunHistoryEntry[] }[] {
  const map = new Map<string, RunHistoryEntry[]>()
  for (const e of entries) {
    const label = e.ts.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    if (!map.has(label)) map.set(label, [])
    map.get(label)!.push(e)
  }
  return Array.from(map.entries()).map(([label, entries]) => ({ label, entries }))
}

export default function ReportsPage({ runHistory }: ReportsPageProps) {
  const [groupBy, setGroupBy] = useState<GroupBy>('tool')
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [modalEntry, setModalEntry] = useState<RunHistoryEntry | null>(null)

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

  function toggleExpanded(key: string) {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  const q = search.toLowerCase()
  const keys = Object.keys(grouped).filter(k => !q || k.toLowerCase().includes(q)).sort()

  const timeline = [...runHistory].sort((a, b) => a.ts.getTime() - b.ts.getTime()).slice(-60)
  const timelineGroups = groupByDate(timeline)

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
      {modalEntry && (
        <RunResultModal entry={modalEntry} onClose={() => setModalEntry(null)} />
      )}

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

      {/* ── Timeline ── */}
      <section className="section">
        <div className="section-header">
          <h3>Run Timeline <span className="section-meta">last {timeline.length}</span></h3>
        </div>
        <div className="reports-timeline-wrap">
          {timelineGroups.map(({ label, entries }) => (
            <div key={label} className="reports-timeline-group">
              <span className="reports-timeline-date">{label}</span>
              <div className="reports-timeline-dots">
                {entries.map((e, i) => (
                  <button
                    key={i}
                    className={`reports-timeline-dot ${e.result.success ? 'ok' : 'fail'}`}
                    title={`${e.tool} — ${e.ts.toLocaleTimeString('en-GB')} — ${e.result.success ? 'ok' : 'failed'} (${e.result.execution_time.toFixed(1)}s)`}
                    onClick={() => setModalEntry(e)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Breakdown ── */}
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
            <span></span>
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
            const isOpen = expanded.has(k)
            const rowEntries = [...grouped[k]].sort((a, b) => b.ts.getTime() - a.ts.getTime())
            return (
              <div key={k} className="reports-group">
                <button className="reports-row reports-row--clickable" onClick={() => toggleExpanded(k)}>
                  <span className="reports-chevron">
                    {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  </span>
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
                </button>
                {isOpen && (
                  <div className="reports-runs">
                    {rowEntries.map((e, i) => (
                      <button key={i} className="reports-run-row" onClick={() => setModalEntry(e)}>
                        <span className={`reports-run-dot ${e.result.success ? 'ok' : 'fail'}`} />
                        <span className="mono reports-run-tool">{e.tool}</span>
                        <span className="mono reports-run-time">
                          {e.ts.toLocaleDateString('en-GB')} {e.ts.toLocaleTimeString('en-GB')}
                        </span>
                        <span className="mono reports-run-duration">{e.result.execution_time.toFixed(1)}s</span>
                        {Object.entries(e.params).map(([pk, pv]) => (
                          <span key={pk} className="mono reports-run-param">{pk}=<em>{String(pv)}</em></span>
                        ))}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
