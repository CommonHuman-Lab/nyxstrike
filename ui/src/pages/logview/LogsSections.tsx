import type { RefObject } from 'react'
import { getLogLevelClass } from './utils'

interface LogsToolbarProps {
  logAutoScroll: boolean
  setLogAutoScroll: (v: boolean) => void
  showHttpAccess: boolean
  setShowHttpAccess: (v: boolean) => void
  logLimit: number
  setLogLimit: (v: number) => void
  visibleCount: number
  totalCount: number
}

export function LogsToolbar({
  logAutoScroll,
  setLogAutoScroll,
  showHttpAccess,
  setShowHttpAccess,
  logLimit,
  setLogLimit,
  visibleCount,
  totalCount,
}: LogsToolbarProps) {
  return (
    <div className="log-toolbar">
      <label className="log-toggle">
        <input
          type="checkbox"
          checked={logAutoScroll}
          onChange={e => setLogAutoScroll(e.target.checked)}
        />
        Auto-scroll
      </label>
      <label className="log-toggle">
        <input
          type="checkbox"
          checked={showHttpAccess}
          onChange={e => setShowHttpAccess(e.target.checked)}
        />
        Show Dashboard Logs
      </label>
      <label className="log-limit-label">
        Show
        <select
          className="log-limit-select"
          value={logLimit}
          onChange={e => setLogLimit(Number(e.target.value))}
        >
          <option value={50}>50</option>
          <option value={100}>100</option>
          <option value={200}>200</option>
          <option value={500}>500</option>
        </select>
        lines
      </label>
      <span className="section-meta mono">{visibleCount} / {totalCount} lines</span>
    </div>
  )
}

interface LogsViewerProps {
  visible: string[]
  logLimit: number
  logEndRef: RefObject<HTMLDivElement | null>
}

export function LogsViewer({ visible, logLimit, logEndRef }: LogsViewerProps) {
  return (
    <div className="log-viewer log-viewer--full">
      {visible.length === 0
        ? <span className="log-empty">Waiting for log data…</span>
        : visible.slice(-logLimit).map((line, i) => (
            <div key={i} className={`log-line ${getLogLevelClass(line)}`}>{line}</div>
          ))}
      <div ref={logEndRef} />
    </div>
  )
}
