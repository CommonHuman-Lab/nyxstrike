import React from 'react'
import { RefreshCw, XCircle, Server } from 'lucide-react'
import type { Dispatch, SetStateAction } from 'react'
import type { RunHistoryEntry } from '../../types'
import { filterHistory, groupHistoryByDate } from './utils'

interface RunHistoryPanelProps {
  history: RunHistoryEntry[]
  setHistory: Dispatch<SetStateAction<RunHistoryEntry[]>>
  onRefresh?: () => void
  histSearch: string
  setHistSearch: Dispatch<SetStateAction<string>>
  viewEntry: RunHistoryEntry | null
  onOpenModalEntry: (entry: RunHistoryEntry) => void
}

export function RunHistoryPanel({
  history,
  setHistory,
  onRefresh,
  histSearch,
  setHistSearch,
  viewEntry,
  onOpenModalEntry,
}: RunHistoryPanelProps) {
  const visible = filterHistory(history, histSearch)
  const grouped = groupHistoryByDate(visible)

  return (
    <div className="run-history">
      <div className="run-history-header">
        <span>History</span>
        <span className="badge">{history.length}</span>
        {onRefresh && (
          <button
            className="run-history-refresh"
            title="Fetch server-side runs"
            onClick={onRefresh}
          >
            <RefreshCw size={12} />
          </button>
        )}
        {history.length > 0 && (
          <button
            className="run-history-clear"
            title="Clear history"
            onClick={() => { setHistory([]); setHistSearch('') }}
          >
            <XCircle size={12} />
          </button>
        )}
      </div>

      {history.length > 0 && (
        <div className="run-history-search">
          <input
            className="run-history-search-input mono"
            placeholder="Filter…"
            value={histSearch}
            onChange={e => setHistSearch(e.target.value)}
          />
          {histSearch && (
            <button className="run-history-search-clear" onClick={() => setHistSearch('')}>
              <XCircle size={11} />
            </button>
          )}
        </div>
      )}

      {visible.length === 0 ? (
        <p className="run-history-empty">{histSearch ? 'No matches' : 'No runs yet'}</p>
      ) : (
        <>
          {grouped.map(group => (
            <React.Fragment key={group.dateLabel}>
              <div className="run-history-date">{group.dateLabel}</div>
              {group.entries.map(entry => (
                <button
                  key={entry.id}
                  className={`run-history-item${viewEntry?.id === entry.id ? ' active' : ''}`}
                  onClick={() => onOpenModalEntry(entry)}
                >
                  <span className={`run-hist-dot ${entry.result.success ? 'ok' : 'fail'}`} />
                  <span className="run-hist-name mono">{entry.tool}</span>
                  {entry.source === 'server' && (
                    <span title="Recorded server-side" className="run-hist-server-icon">
                      <Server size={10} />
                    </span>
                  )}
                  <span className="run-hist-time">{entry.ts.toLocaleTimeString('en-GB')}</span>
                </button>
              ))}
            </React.Fragment>
          ))}
        </>
      )}
    </div>
  )
}
