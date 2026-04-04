import React, { useState } from 'react'
import { LogsToolbar, LogsViewer } from './LogsSections'
import { getVisibleLogLines } from './utils'
import './LogsPage.css'

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

  const visible = getVisibleLogLines(logLines, showHttpAccess)

  return (
    <div className="page-content">
      <section className="section">
        <div className="section-header">
          <h3>Server Log</h3>
          <LogsToolbar
            logAutoScroll={logAutoScroll}
            setLogAutoScroll={setLogAutoScroll}
            showHttpAccess={showHttpAccess}
            setShowHttpAccess={setShowHttpAccess}
            logLimit={logLimit}
            setLogLimit={setLogLimit}
            visibleCount={visible.length}
            totalCount={logLines.length}
          />
        </div>
        <LogsViewer visible={visible} logLimit={logLimit} logEndRef={logEndRef} />
      </section>
    </div>
  )
}
