import { useState } from 'react'
import type { RunHistoryEntry } from '../../shared/types'
import { getGroupStats, groupByDate, type GroupBy } from './reportUtils'
import { safeFixed } from '../../shared/utils'
import { CollapseChevron } from '../../components/CollapseChevron'

export function ReportsTimelineSection({
  runHistory,
  onOpenEntry,
}: {
  runHistory: RunHistoryEntry[]
  onOpenEntry: (entry: RunHistoryEntry) => void
}) {
  const timeline = [...runHistory].sort((a, b) => b.ts.getTime() - a.ts.getTime()).slice(0, 60)
  const timelineGroups = groupByDate(timeline)

  return (
    <section className="section">
      <div className="section-header">
        <h3>Run Timeline <span className="section-meta">last {timeline.length}</span></h3>
      </div>
      <div className="reports-timeline-wrap">
        {timelineGroups.map(({ label, entries }) => (
          <div key={label} className="reports-timeline-group">
            <span className="reports-timeline-date">{label}</span>
            <div className="reports-timeline-dots">
              {entries.map((entry, index) => (
                <button
                  key={index}
                  className={`reports-timeline-dot ${entry.result.success ? 'ok' : 'fail'}`}
                  title={`${entry.tool} — ${entry.ts.toLocaleTimeString('en-GB')} — ${entry.result.success ? 'ok' : 'failed'} (${safeFixed(entry.result.execution_time, 1)}s)`}
                  onClick={() => onOpenEntry(entry)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export function ReportsBreakdownSection({
  grouped,
  keys,
  groupBy,
  search,
  setSearch,
  setGroupBy,
  expanded,
  toggleExpanded,
  onOpenEntry,
}: {
  grouped: Record<string, RunHistoryEntry[]>
  keys: string[]
  groupBy: GroupBy
  search: string
  setSearch: (value: string) => void
  setGroupBy: (value: GroupBy) => void
  expanded: Set<string>
  toggleExpanded: (key: string) => void
  onOpenEntry: (entry: RunHistoryEntry) => void
}) {
  const [sectionOpen, setSectionOpen] = useState(false)

  return (
    <section className="section">
      <div className="section-header section-header--clickable" onClick={() => setSectionOpen(o => !o)}>
        <h3>
          <CollapseChevron open={sectionOpen} size={13} className="section-chevron" />
          Breakdown
        </h3>
        {sectionOpen && (
          <div className="section-header-controls" onClick={e => e.stopPropagation()}>
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
        )}
      </div>

      {sectionOpen && (
        <div className="reports-table">
          <div className="reports-thead table-thead">
            <span></span>
            <span>{groupBy === 'tool' ? 'Tool' : 'Target'}</span>
            <span>Runs</span>
            <span>Success</span>
            <span>Failed</span>
            <span>Avg Time</span>
            <span>Last Run</span>
          </div>

          {keys.map(key => {
            const groupEntries = grouped[key]
            const stats = getGroupStats(groupEntries)
            const pct = (stats.ok / stats.total) * 100
            const color = pct >= 80 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--red)'
            const isOpen = expanded.has(key)
            const rowEntries = [...groupEntries].sort((a, b) => b.ts.getTime() - a.ts.getTime())

            return (
              <div key={key} className="reports-group">
                <button className="reports-row reports-row--clickable" onClick={() => toggleExpanded(key)}>
                  <span className="reports-chevron">
                    <CollapseChevron open={isOpen} size={12} />
                  </span>
                  <span className="mono reports-key">{key}</span>
                  <span className="mono">{stats.total}</span>
                  <span className="mono" style={{ color: 'var(--green)' }}>{stats.ok}</span>
                  <span className="mono" style={{ color: stats.failed > 0 ? 'var(--red)' : 'var(--text-dim)' }}>{stats.failed}</span>
                  <span className="mono">{safeFixed(stats.avgTime, 1)}s</span>
                  <div className="reports-last-cell">
                    <span className="progress-bar">
                      <span className="progress-bar__fill" style={{ width: `${pct}%`, background: color }} />
                    </span>
                    <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                      {stats.last.ts.toLocaleDateString('en-GB')} {stats.last.ts.toLocaleTimeString('en-GB')}
                    </span>
                  </div>
                </button>

                {isOpen && (
                  <div className="reports-runs">
                    {rowEntries.map((entry, index) => (
                      <button key={index} className="reports-run-row" onClick={() => onOpenEntry(entry)}>
                        <span className={`reports-run-dot ${entry.result.success ? 'ok' : 'fail'}`} />
                        <span className="mono reports-run-tool">{entry.tool}</span>
                        <span className="mono reports-run-time">
                          {entry.ts.toLocaleDateString('en-GB')} {entry.ts.toLocaleTimeString('en-GB')}
                        </span>
                        <span className="mono reports-run-duration">{safeFixed(entry.result.execution_time, 1)}s</span>
                        {Object.entries(entry.params).map(([paramKey, paramValue]) => (
                          <span key={paramKey} className="mono reports-run-param">{paramKey}=<em>{String(paramValue)}</em></span>
                        ))}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
