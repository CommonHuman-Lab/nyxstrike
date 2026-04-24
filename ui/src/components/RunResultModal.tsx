import { createPortal } from 'react-dom'
import { CheckCircle, XCircle, Play, Download, GitCompare } from 'lucide-react'
import { type RunHistoryEntry } from '../shared/types'
import { exportEntry, safeFixed } from '../shared/utils'
import { useEscapeClose } from '../hooks/useEscapeClose'

export function RunResultModal({ entry, onClose, onRerun, compareText }: {
  entry: RunHistoryEntry
  onClose: () => void
  onRerun?: () => void
  compareText?: string
}) {
  const r = entry.result

  useEscapeClose(true, onClose)

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal run-result-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-name mono">{entry.tool}</span>
            <span className={`run-output-status ${r.success ? 'ok' : 'fail'}`} style={{ fontSize: 12 }}>
              {r.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
              {r.success ? 'success' : 'failed'}
            </span>
          </div>
          <button className="modal-close" onClick={onClose}><XCircle size={18} /></button>
        </div>

        <div className="run-result-modal-meta">
          <span className="run-output-meta mono">exit {r.return_code}</span>
          <span className="run-output-meta mono">{safeFixed(r.execution_time, 2)}s</span>
          <span className="run-output-meta mono">
            {entry.ts.toLocaleDateString('en-GB')} {entry.ts.toLocaleTimeString('en-GB')}
          </span>
          {r.timed_out && <span className="run-output-meta amber">timed out</span>}
          {r.partial_results && <span className="run-output-meta amber">partial results</span>}
          <div className="run-export-btns">
            {onRerun && (
              <button className="run-export-btn run-rerun-btn" onClick={onRerun} title="Re-run with same params">
                <Play size={11} /> Re-run
              </button>
            )}
            {compareText && (
              <button
                className="run-export-btn"
                onClick={() => navigator.clipboard?.writeText(compareText).catch(() => {})}
                title="Copy comparison with previous run"
              >
                <GitCompare size={11} /> Compare
              </button>
            )}
            <button className="run-export-btn" onClick={() => exportEntry(entry, 'txt')} title="Export as .txt">
              <Download size={11} /> TXT
            </button>
            <button className="run-export-btn" onClick={() => exportEntry(entry, 'json')} title="Export as .json">
              <Download size={11} /> JSON
            </button>
          </div>
        </div>

        {Object.keys(entry.params).length > 0 && (
          <div className="run-result-modal-params">
            {Object.entries(entry.params).map(([k, v]) => (
              <span key={k} className="run-result-param mono">{k}=<em>{String(v)}</em></span>
            ))}
          </div>
        )}

        <pre className="run-result-modal-output mono">
          {r.stdout || r.stderr || '(no output)'}
        </pre>
        {compareText && (
          <pre className="run-result-modal-compare mono">
            {compareText}
          </pre>
        )}
      </div>
    </div>,
    document.body
  )
}
