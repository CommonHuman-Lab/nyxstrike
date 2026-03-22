import React, { useState, useRef } from 'react'
import {
  CheckCircle, XCircle, RefreshCw, Play, AlertCircle,
  ChevronUp, ChevronDown, Server, Download,
} from 'lucide-react'
import { api, type Tool } from '../api'
import { exportEntry } from '../utils'
import type { RunHistoryEntry } from '../types'
import { RunResultModal } from '../components/RunResultModal'
import './RunPage.css'

// ─── Param Field ──────────────────────────────────────────────────────────────

function ParamField({
  name, value, onChange, required,
}: {
  name: string
  value: string
  onChange: (v: string) => void
  required?: boolean
}) {
  return (
    <div className="run-field">
      <label className="run-field-label mono">
        {name}
        {required && <span className="run-required">*</span>}
      </label>
      <input
        className="run-field-input mono"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={required ? 'required' : 'optional'}
      />
    </div>
  )
}

// ─── Run Page ─────────────────────────────────────────────────────────────────

interface RunPageProps {
  tools: Tool[]
  toolsStatus: Record<string, boolean>
  runHistory: RunHistoryEntry[]
  setRunHistory: React.Dispatch<React.SetStateAction<RunHistoryEntry[]>>
  onRefresh?: () => void
}

export function RunPage({ tools, toolsStatus, runHistory: history, setRunHistory: setHistory, onRefresh }: RunPageProps) {
  const [search, setSearch] = useState('')
  const [activeCat, setActiveCat] = useState('all')
  const [selected, setSelected] = useState<Tool | null>(null)
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [showOptional, setShowOptional] = useState(true)
  const [running, setRunning] = useState(false)
  const [viewEntry, setViewEntry] = useState<RunHistoryEntry | null>(null)
  const [modalEntry, setModalEntry] = useState<RunHistoryEntry | null>(null)
  const [histSearch, setHistSearch] = useState('')
  const [runError, setRunError] = useState<string | null>(null)
  const runIdRef = useRef(0)

  const cats = ['all', ...Array.from(new Set(tools.map(t => t.category))).sort()]
  const filtered = tools.filter(t => {
    if (toolsStatus[t.name] !== true) return false
    const matchCat = activeCat === 'all' || t.category === activeCat
    const q = search.toLowerCase()
    return matchCat && (!q || t.name.includes(q) || t.desc.toLowerCase().includes(q))
  }).sort((a, b) => a.name.localeCompare(b.name))

  function selectTool(t: Tool) {
    setSelected(t)
    setShowOptional(true)
    setRunError(null)
    setViewEntry(null)
    const defaults: Record<string, string> = {}
    for (const k of Object.keys(t.params)) defaults[k] = ''
    for (const [k, v] of Object.entries(t.optional)) defaults[k] = String(v)
    setFieldValues(defaults)
  }

  async function runTool() {
    if (!selected) return
    const required = Object.keys(selected.params)
    const missing = required.filter(k => !fieldValues[k]?.trim())
    if (missing.length) { setRunError(`Missing required: ${missing.join(', ')}`); return }
    setRunError(null)
    setRunning(true)
    setViewEntry(null)
    const id = ++runIdRef.current
    const payload: Record<string, unknown> = {}
    for (const k of required) payload[k] = fieldValues[k].trim()
    for (const k of Object.keys(selected.optional)) {
      const v = fieldValues[k]
      if (v !== undefined && v !== '') payload[k] = v
    }
    try {
      const result = await api.runTool(selected.endpoint, payload)
      const entry: RunHistoryEntry = { id, tool: selected.name, params: payload, result, ts: new Date(), source: 'browser' }
      setHistory(h => [entry, ...h].slice(0, 100)) // Limit to last 100 runs
      setViewEntry(entry)
    } catch (e) {
      setRunError(String(e))
    } finally {
      setRunning(false)
    }
  }

  const requiredKeys = selected ? Object.keys(selected.params) : []
  const optionalKeys = selected ? Object.keys(selected.optional) : []

  return (
    <div className="run-page">
      {modalEntry && (
        <RunResultModal
          entry={modalEntry}
          onClose={() => setModalEntry(null)}
          onRerun={() => {
            const t = tools.find(t => t.name === modalEntry.tool)
            if (t) {
              selectTool(t)
              setFieldValues(prev => {
                const next = { ...prev }
                for (const [k, v] of Object.entries(modalEntry.params)) next[k] = String(v)
                return next
              })
            }
            setModalEntry(null)
          }}
        />
      )}
      {/* ── Left: tool picker ── */}
      <div className="run-picker">
        <div className="run-picker-controls">
          <input
            className="search-input mono"
            placeholder="Search tools…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <div className="cat-tabs run-cat-tabs">
            {cats.map(c => (
              <button
                key={c}
                className={`cat-tab ${activeCat === c ? 'active' : ''}`}
                onClick={() => setActiveCat(c)}
              >
                {c.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>
        <div className="run-tool-list">
          {filtered.map(t => (
            <button
              key={t.name}
              className={`run-tool-item${selected?.name === t.name ? ' active' : ''}`}
              onClick={() => selectTool(t)}
            >
              <span className="run-tool-name mono">{t.name}</span>
              <span className="run-tool-cat">{t.category.replace(/_/g, ' ')}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Centre: form + output ── */}
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
              {requiredKeys.map(k => (
                <ParamField
                  key={k} name={k}
                  value={fieldValues[k] ?? ''}
                  onChange={v => setFieldValues(fv => ({ ...fv, [k]: v }))}
                  required
                />
              ))}

              {optionalKeys.length > 0 && (
                <button className="run-opt-btn" onClick={() => setShowOptional(o => !o)}>
                  {showOptional ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  Optional parameters ({optionalKeys.length})
                </button>
              )}
              {showOptional && optionalKeys.map(k => (
                <ParamField
                  key={k} name={k}
                  value={fieldValues[k] ?? ''}
                  onChange={v => setFieldValues(fv => ({ ...fv, [k]: v }))}
                />
              ))}

              {runError && (
                <div className="run-error"><AlertCircle size={13} /> {runError}</div>
              )}

              <button className="run-submit" onClick={runTool} disabled={running}>
                {running
                  ? <><RefreshCw size={13} className="spin" /> Running…</>
                  : <><Play size={13} /> Run {selected.name}</>}
              </button>
            </div>

            {/* Output */}
            {(running || viewEntry) && (
              <div className="run-output">
                <div className="run-output-header">
                  {running ? (
                    <span className="run-output-status running">
                      <RefreshCw size={12} className="spin" /> running…
                    </span>
                  ) : viewEntry && (
                    <>
                      <span className={`run-output-status ${viewEntry.result.success ? 'ok' : 'fail'}`}>
                        {viewEntry.result.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
                        {viewEntry.result.success ? 'success' : 'failed'}
                      </span>
                      <span className="run-output-meta mono">exit {viewEntry.result.return_code}</span>
                      <span className="run-output-meta mono">{viewEntry.result.execution_time.toFixed(2)}s</span>
                      {viewEntry.result.timed_out && <span className="run-output-meta amber">timed out</span>}
                      {viewEntry.result.partial_results && <span className="run-output-meta amber">partial</span>}
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

      {/* ── Right: history ── */}
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
        {(() => {
          const q = histSearch.toLowerCase()
          const visible = q
            ? history.filter(e => e.tool.includes(q) || Object.values(e.params).some(v => String(v).toLowerCase().includes(q)))
            : history
          if (visible.length === 0) return <p className="run-history-empty">{histSearch ? 'No matches' : 'No runs yet'}</p>
          return visible.map(e => (
            <button
              key={e.id}
              className={`run-history-item${viewEntry?.id === e.id ? ' active' : ''}`}
              onClick={() => setModalEntry(e)}
            >
              <span className={`run-hist-dot ${e.result.success ? 'ok' : 'fail'}`} />
              <span className="run-hist-name mono">{e.tool}</span>
              {e.source === 'server' && <span title="Recorded server-side" className="run-hist-server-icon"><Server size={10} /></span>}
              <span className="run-hist-time">{e.ts.toLocaleTimeString('en-GB')}</span>
            </button>
          ))
        })()}
      </div>
    </div>
  )
}
