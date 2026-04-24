import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { FileText, RefreshCw, CheckCircle, XCircle, X } from 'lucide-react'
import { useReportGenState } from '../hooks/useReportGenerating'
import { reportGenDismiss, reportGenNavigate } from '../app/reportGeneration'
import './ReportGenerationBubble.css'

/**
 * Floating bubble rendered in the bottom-left of the screen.
 * Shows while a report is generating, then shows result with saved path.
 * Mounts globally via portal so it survives page navigation.
 */
export function ReportGenerationBubble() {
  const state = useReportGenState()

  // Auto-dismiss after 8 s when done or errored
  useEffect(() => {
    if (state.status !== 'done' && state.status !== 'error') return
    const t = setTimeout(reportGenDismiss, 8000)
    return () => clearTimeout(t)
  }, [state.status])

  if (state.status === 'idle') return null

  const bubble = (
    <div className={`report-bubble report-bubble--${state.status}`}>
      <div className="report-bubble-icon">
        {state.status === 'generating' && <RefreshCw size={14} className="spin" />}
        {state.status === 'done' && <CheckCircle size={14} />}
        {state.status === 'error' && <XCircle size={14} />}
      </div>

      <div
        className={`report-bubble-body${state.status === 'done' && state.savedPath ? ' report-bubble-body--clickable' : ''}`}
        onClick={state.status === 'done' && state.savedPath ? () => { reportGenNavigate(state.savedPath); reportGenDismiss() } : undefined}
        title={state.status === 'done' && state.savedPath ? 'Open in Notes' : undefined}
      >
        <div className="report-bubble-title">
          <FileText size={11} />
          {state.status === 'generating' && 'Generating report…'}
          {state.status === 'done' && 'Report saved — click to open'}
          {state.status === 'error' && 'Report failed'}
        </div>
        <div className="report-bubble-label">{state.label}</div>
        {state.status === 'done' && (
          <div className="report-bubble-path mono">{state.savedPath}</div>
        )}
        {state.status === 'error' && (
          <div className="report-bubble-error">{state.message}</div>
        )}
      </div>

      {(state.status === 'done' || state.status === 'error') && (
        <button
          className="report-bubble-dismiss"
          onClick={reportGenDismiss}
          title="Dismiss"
        >
          <X size={12} />
        </button>
      )}
    </div>
  )

  return createPortal(bubble, document.body)
}
