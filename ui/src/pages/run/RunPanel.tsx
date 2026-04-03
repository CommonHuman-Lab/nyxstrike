import {
  CheckCircle, XCircle, RefreshCw, Play, AlertCircle,
  ChevronUp, ChevronDown, Download,
} from 'lucide-react'
import type { Dispatch, SetStateAction } from 'react'
import type { Tool } from '../../api'
import type { RunHistoryEntry } from '../../types'
import { exportEntry } from '../../utils'
import { ParamField } from '../../components/tool-run/ParamField'

interface RunPanelProps {
  selected: Tool | null
  toolsStatus: Record<string, boolean>
  fieldValues: Record<string, string>
  setFieldValues: Dispatch<SetStateAction<Record<string, string>>>
  showOptional: boolean
  setShowOptional: Dispatch<SetStateAction<boolean>>
  running: boolean
  runError: string | null
  onRunTool: () => Promise<void>
  viewEntry: RunHistoryEntry | null
}

export function RunPanel({
  selected,
  toolsStatus,
  fieldValues,
  setFieldValues,
  showOptional,
  setShowOptional,
  running,
  runError,
  onRunTool,
  viewEntry,
}: RunPanelProps) {
  const requiredKeys = selected ? Object.keys(selected.params) : []
  const optionalKeys = selected ? Object.keys(selected.optional) : []

  return (
    <div className="run-main">
      {!selected ? (
        <div className="run-empty">
          <Play size={36} color="var(--text-dim)" />
          <p>Select a tool from the list</p>
        </div>
      ) : (
        <>
          <div className="run-form-header">
            <span className="run-form-name mono">{selected.name}</span>
            <span className="modal-cat">{selected.category.replace(/_/g, ' ')}</span>
            {toolsStatus[selected.name] === true && (
              <span className="modal-status modal-status--installed"><CheckCircle size={11} /> installed</span>
            )}
            {toolsStatus[selected.name] === false && (
              <span className="modal-status modal-status--missing"><XCircle size={11} /> not installed</span>
            )}
          </div>
          <p className="run-form-desc">{selected.desc}</p>

          <div className="run-form">
            {requiredKeys.map(key => (
              <ParamField
                key={key}
                name={key}
                value={fieldValues[key] ?? ''}
                onChange={value => setFieldValues(prev => ({ ...prev, [key]: value }))}
                required
              />
            ))}

            {optionalKeys.length > 0 && (
              <button className="run-opt-btn" onClick={() => setShowOptional(show => !show)}>
                {showOptional ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                Optional parameters ({optionalKeys.length})
              </button>
            )}

            {showOptional && optionalKeys.map(key => (
              <ParamField
                key={key}
                name={key}
                value={fieldValues[key] ?? ''}
                onChange={value => setFieldValues(prev => ({ ...prev, [key]: value }))}
              />
            ))}

            {runError && (
              <div className="run-error"><AlertCircle size={13} /> {runError}</div>
            )}

            <button className="run-submit" onClick={onRunTool} disabled={running}>
              {running
                ? <><RefreshCw size={13} className="spin" /> Running…</>
                : <><Play size={13} /> Run {selected.name}</>}
            </button>
          </div>

          {(running || viewEntry) && (
            <div className="run-output">
              <div className="run-output-header">
                {running ? (
                  <span className="run-output-status running">
                    <RefreshCw size={12} className="spin" /> Running…
                  </span>
                ) : viewEntry && (
                  <>
                    <span className={`run-output-status ${viewEntry.result.success ? 'ok' : 'fail'}`}>
                      {viewEntry.result.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
                      {viewEntry.result.success ? 'Success' : 'Failed'}
                    </span>
                    <span className="run-output-meta mono">exit {viewEntry.result.return_code}</span>
                    <span className="run-output-meta mono">{viewEntry.result.execution_time.toFixed(2)}s</span>
                    {viewEntry.result.timed_out && <span className="run-output-meta amber">Timed out</span>}
                    {viewEntry.result.partial_results && <span className="run-output-meta amber">Partial</span>}
                    <div className="run-export-btns">
                      <button className="run-export-btn" onClick={() => exportEntry(viewEntry, 'txt')} title="Export as .txt">
                        <Download size={11} /> TXT
                      </button>
                      <button className="run-export-btn" onClick={() => exportEntry(viewEntry, 'json')} title="Export as .json">
                        <Download size={11} /> JSON
                      </button>
                    </div>
                  </>
                )}
              </div>
              {viewEntry && (
                <pre className="run-output-pre">
                  {viewEntry.result.stdout || viewEntry.result.stderr || '(no output)'}
                </pre>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
