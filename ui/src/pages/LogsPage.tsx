import React, { useState } from 'react'
import './LogsPage.css'

// Matches only the specific dashboard polling access log line, e.g.:
// 127.0.0.1 - "GET /web-dashboard HTTP/1.1" 200
const HTTP_ACCESS_RE = /\d+\.\d+\.\d+\.\d+.*"GET \/web-dashboard HTTP\/\d/

interface LogsPageProps {
  logLines: string[]
  logAutoScroll: boolean
  setLogAutoScroll: (v: boolean) => void
  logLimit: number
  setLogLimit: (v: number) => void
  logEndRef: React.RefObject<HTMLDivElement | null>
}

export default function LogsPage({
  logLines,
  logAutoScroll,
  setLogAutoScroll,
  logLimit,
  setLogLimit,
  logEndRef,
}: LogsPageProps) {
  const [showHttpAccess, setShowHttpAccess] = useState(false)

  const visible = showHttpAccess
    ? logLines
    : logLines.filter(line => !HTTP_ACCESS_RE.test(line))

  return (
    <div className="page-content">
      <section className="section">
        <div className="section-header">
          <h3>Server Log</h3>
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
            <span className="section-meta mono">{visible.length} / {logLines.length} lines</span>
          </div>
        </div>
        <div className="log-viewer log-viewer--full">
          {visible.length === 0
            ? <span className="log-empty">Waiting for log data…</span>
            : visible.slice(-logLimit).map((line, i) => {
                const lvl = /\bERROR\b/.test(line) ? 'error'
                  : /\bWARN(ING)?\b/.test(line) ? 'warn'
                  : /\bDEBUG\b/.test(line) ? 'debug'
                  : ''
                return <div key={i} className={`log-line ${lvl}`}>{line}</div>
              })
          }
          <div ref={logEndRef} />
        </div>
      </section>
    </div>
  )
}
