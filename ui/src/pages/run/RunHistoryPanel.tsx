import React from 'react'
import { RefreshCw, XCircle, Server } from 'lucide-react'
import type { Dispatch, SetStateAction } from 'react'
import type { RunHistoryEntry } from '../../shared/types'
import { ConfirmActionModal } from '../../components/ConfirmActionModal'
import { CollapseChevron } from '../../components/CollapseChevron'
import { filterHistory, groupHistoryByDate } from './utils'
import { useToast } from '../../components/ToastProvider'

interface RunHistoryPanelProps {
  history: RunHistoryEntry[]
  setHistory: Dispatch<SetStateAction<RunHistoryEntry[]>>
  onRefresh?: () => void
  onClearHistory?: () => Promise<void>
  histSearch: string
  setHistSearch: Dispatch<SetStateAction<string>>
  viewEntry: RunHistoryEntry | null
  onOpenModalEntry: (entry: RunHistoryEntry) => void
}

export function RunHistoryPanel({
  history,
  setHistory,
  onRefresh,
  onClearHistory,
  histSearch,
  setHistSearch,
  viewEntry,
  onOpenModalEntry,
}: RunHistoryPanelProps) {
  const { pushToast } = useToast()
  const [confirmOpen, setConfirmOpen] = React.useState(false)
  const [clearing, setClearing] = React.useState(false)
  const [collapsedDates, setCollapsedDates] = React.useState<Record<string, boolean>>({})
  const visible = filterHistory(history, histSearch)
  const grouped = groupHistoryByDate(visible)

  React.useEffect(() => {
    setCollapsedDates(prev => {
      const next: Record<string, boolean> = {}
      grouped.forEach((group, idx) => {
        if (Object.prototype.hasOwnProperty.call(prev, group.dateLabel)) {
          next[group.dateLabel] = prev[group.dateLabel]
        } else {
          next[group.dateLabel] = idx !== 0
        }
      })
      return next
    })
  }, [grouped])

  async function handleConfirmClear() {
    setClearing(true)
    try {
      if (onClearHistory) {
        await onClearHistory()
      } else {
        setHistory([])
      }
      pushToast('success', 'Run history cleared')
      setHistSearch('')
      setConfirmOpen(false)
    } finally {
      setClearing(false)
    }
  }

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
            onClick={() => setConfirmOpen(true)}
          >
            <XCircle size={12} />
          </button>
        )}
      </div>

      <ConfirmActionModal
        isOpen={confirmOpen}
        title="Clear Run History"
        description="This deletes all recorded runs from the dashboard history. This action is immediate and cannot be undone."
        impactItems={[
          'Run History will be emptied',
          'Reports is based on run history and will lose data'
        ]}
        confirmLabel="Yes, clear history"
        cancelLabel="Keep history"
        confirmVariant="danger"
        isConfirming={clearing}
        onConfirm={handleConfirmClear}
        onClose={() => setConfirmOpen(false)}
      />

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

      <div className="run-history-list">
        {visible.length === 0 ? (
          <p className="run-history-empty">{histSearch ? 'No matches' : 'No runs yet'}</p>
        ) : (
          <>
            {grouped.map(group => (
              <React.Fragment key={group.dateLabel}>
                <button
                  className="run-history-date run-history-date-toggle"
                  onClick={() => setCollapsedDates(prev => ({ ...prev, [group.dateLabel]: !prev[group.dateLabel] }))}
                >
                  <CollapseChevron open={!collapsedDates[group.dateLabel]} size={11} />
                  <span>{group.dateLabel}</span>
                  <span className="run-history-date-count mono">{group.entries.length}</span>
                </button>
                {!collapsedDates[group.dateLabel] && group.entries.map(entry => (
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
    </div>
  )
}
