import React, { useState, useRef } from 'react'
import { api, type Tool } from '../api'
import type { RunHistoryEntry } from '../types'
import { RunResultModal } from '../components/RunResultModal'
import { buildRunPayload } from '../components/tool-run/payload'
import { RunToolPicker } from './run/RunToolPicker'
import { RunPanel } from './run/RunPanel'
import { RunHistoryPanel } from './run/RunHistoryPanel'
import { getCategories, getFilteredTools } from './run/utils'
import '../components/tool-run/shared.css'
import './RunPage.css'

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

  const cats = getCategories(tools)
  const filtered = getFilteredTools(tools, toolsStatus, activeCat, search)

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
    const { payload, missing } = buildRunPayload(selected, fieldValues)
    if (missing.length) { setRunError(`Missing required: ${missing.join(', ')}`); return }
    setRunError(null)
    setRunning(true)
    setViewEntry(null)
    const id = ++runIdRef.current
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
      <RunToolPicker
        search={search}
        setSearch={setSearch}
        activeCat={activeCat}
        setActiveCat={setActiveCat}
        cats={cats}
        filtered={filtered}
        selected={selected}
        onSelectTool={selectTool}
      />

      <RunPanel
        selected={selected}
        toolsStatus={toolsStatus}
        fieldValues={fieldValues}
        setFieldValues={setFieldValues}
        showOptional={showOptional}
        setShowOptional={setShowOptional}
        running={running}
        runError={runError}
        onRunTool={runTool}
        viewEntry={viewEntry}
      />

      <RunHistoryPanel
        history={history}
        setHistory={setHistory}
        onRefresh={onRefresh}
        histSearch={histSearch}
        setHistSearch={setHistSearch}
        viewEntry={viewEntry}
        onOpenModalEntry={setModalEntry}
      />
    </div>
  )
}
