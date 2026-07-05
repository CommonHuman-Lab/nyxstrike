import React, { useEffect, useRef, useState } from 'react'
import { api, type Tool } from '../../api'
import type { RunHistoryEntry } from '../../shared/types'
import { RunResultModal } from '../../components/RunResultModal'
import { usePersistentState } from '../../hooks/usePersistentState'
import { buildRunPayload } from '../../components/tool-run/payload'
import { filterToolsByOptions, getToolCategories } from '../../shared/toolUtils'
import { buildRunDiff } from './compare'
import { RunToolPicker } from './RunToolPicker'
import { RunPanel } from './RunPanel'
import { RunHistoryPanel } from './RunHistoryPanel'
import { RunQuickBar } from './RunQuickBar'
import { deriveTargetFromParams, RUN_FAVORITES_KEY, RUN_RECENT_TARGETS_KEY } from './storage'
import '../../components/tool-run/shared.css'
import './RunPage.css'

// ─── Run Page ─────────────────────────────────────────────────────────────────

interface RunPageProps {
  tools: Tool[]
  toolsStatus: Record<string, boolean>
  runHistory: RunHistoryEntry[]
  setRunHistory: React.Dispatch<React.SetStateAction<RunHistoryEntry[]>>
  commandToolRequest?: { toolName: string; requestId: number } | null
  onCommandToolHandled?: () => void
  onRefresh?: () => void
  onClearHistory?: () => Promise<void>
}

export function RunPage({
  tools,
  toolsStatus,
  runHistory: history,
  setRunHistory: setHistory,
  commandToolRequest,
  onCommandToolHandled,
  onRefresh,
  onClearHistory,
}: RunPageProps) {
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
  const [liveOutput, setLiveOutput] = useState<string | null>(null)
  const [favorites, setFavorites] = usePersistentState<string[]>(RUN_FAVORITES_KEY, [])
  const [recentTargets, setRecentTargets] = usePersistentState<string[]>(RUN_RECENT_TARGETS_KEY, [])
  const runIdRef = useRef(0)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const liveStreamRef = useRef<EventSource | null>(null)

  function stopLiveTracking() {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    liveStreamRef.current?.close()
    liveStreamRef.current = null
  }

  useEffect(() => stopLiveTracking, [])

  const cats = getToolCategories(tools)
  const filtered = filterToolsByOptions(tools, {
    toolsStatus,
    activeCategory: activeCat,
    search,
    requireAvailable: true,
  })

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

  function toggleFavoriteSelected() {
    if (!selected) return
    const name = selected.name
    setFavorites(prev => prev.includes(name) ? prev.filter(t => t !== name) : [name, ...prev].slice(0, 30))
  }

  function applyTarget(target: string) {
    const targetKeys = ['target', 'url', 'domain', 'host', 'ip', 'rhost', 'hostname']
    setFieldValues(prev => {
      const next = { ...prev }
      for (const key of targetKeys) {
        if (Object.prototype.hasOwnProperty.call(next, key)) {
          next[key] = target
          break
        }
      }
      return next
    })
  }

  async function runTool() {
    if (!selected) return
    const { payload, missing } = buildRunPayload(selected, fieldValues)
    if (missing.length) { setRunError(`Missing required: ${missing.join(', ')}`); return }
    setRunError(null)
    setRunning(true)
    setViewEntry(null)
    setLiveOutput(null)
    const id = ++runIdRef.current
    stopLiveTracking()
    try {
      const { task_id } = await api.executeToolAsync(selected.name, payload)

      const liveSource = api.processesStream()
      liveStreamRef.current = liveSource
      liveSource.onmessage = e => {
        try {
          const streamPayload = JSON.parse(e.data) as { processes?: Record<string, { task_id?: string | null; last_output?: string }> }
          const match = Object.values(streamPayload.processes ?? {}).find(p => p.task_id === task_id)
          if (match) setLiveOutput(match.last_output || null)
        } catch {
          // ignore malformed SSE frames — the poll loop is the source of truth for completion
        }
      }

      const result = await new Promise<import('../../api').ToolExecResponse>((resolve, reject) => {
        pollRef.current = setInterval(async () => {
          try {
            const res = await api.getTaskResult(task_id)
            const { status } = res.result
            if (status === 'completed') {
              stopLiveTracking()
              resolve(res.result.result as import('../../api').ToolExecResponse)
            } else if (status === 'failed' || status === 'not_found') {
              stopLiveTracking()
              reject(new Error(res.result.error || `Tool execution ${status}`))
            }
          } catch (e) {
            stopLiveTracking()
            reject(e)
          }
        }, 1500)
      })

      const entry: RunHistoryEntry = { id, tool: selected.name, params: payload, result, ts: new Date(), source: 'browser' }
      setHistory(h => [entry, ...h].slice(0, 100)) // Limit to last 100 runs
      setViewEntry(entry)
      const target = deriveTargetFromParams(payload)
      if (target) {
        setRecentTargets(prev => [target, ...prev.filter(t => t !== target)].slice(0, 10))
      }
    } catch (e) {
      setRunError(String(e))
    } finally {
      stopLiveTracking()
      setLiveOutput(null)
      setRunning(false)
    }
  }

  useEffect(() => {
    onRefresh?.()
  }, [])

  useEffect(() => {
    if (!commandToolRequest) return
    const tool = tools.find(t => t.name === commandToolRequest.toolName)
    if (tool) {
      selectTool(tool)
      setSearch('')
    }
    onCommandToolHandled?.()
  }, [commandToolRequest, tools, onCommandToolHandled])

  const compareText = modalEntry
    ? (() => {
        const prev = history.find(e => e.id !== modalEntry.id && e.tool === modalEntry.tool)
        return prev ? buildRunDiff(modalEntry, prev) : undefined
      })()
    : undefined

  const favoriteTools = filtered
    .filter(tool => favorites.includes(tool.name))
    .sort((a, b) => favorites.indexOf(a.name) - favorites.indexOf(b.name))

  const nonFavoriteTools = filtered.filter(tool => !favorites.includes(tool.name))

  return (
    <div className="run-page">
      {modalEntry && (
        <RunResultModal
          entry={modalEntry}
          compareText={compareText}
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
        filtered={nonFavoriteTools}
        favorites={favoriteTools}
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
        liveOutput={liveOutput}
        isFavorite={selected ? favorites.includes(selected.name) : false}
        onToggleFavorite={toggleFavoriteSelected}
        onRunTool={runTool}
        viewEntry={viewEntry}
      />

      <RunQuickBar
        recentTargets={recentTargets}
        onPickTarget={applyTarget}
        onClearRecentTargets={() => setRecentTargets([])}
      />

      <RunHistoryPanel
        history={history}
        setHistory={setHistory}
        onRefresh={onRefresh}
        onClearHistory={onClearHistory}
        histSearch={histSearch}
        setHistSearch={setHistSearch}
        viewEntry={viewEntry}
        onOpenModalEntry={setModalEntry}
      />
    </div>
  )
}
