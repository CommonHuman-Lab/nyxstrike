import { ChevronDown, ChevronUp, Download, FileText, Play, RefreshCw, Send, Square, Terminal, Trash2, Power } from 'lucide-react'
import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react'
import { ParamField } from '../../components/tool-run/ParamField'
import type { AttackChainStep, Tool, ToolExecResponse } from '../../api'
import type { RunHistoryEntry } from '../../shared/types'
import { exportEntry, safeFixed } from '../../shared/utils'
import { resultText, type StepState } from './sessionDetailUtils'
import type { ChainSuggestion } from './sessionDetailUtils'
import { ActionButton } from '../../components/ActionButton'
import { api } from '../../api'
import { useToast } from '../../components/ToastProvider'

interface SessionDetailWorkbenchProps {
  isCompleted: boolean
  sessionId: string
  steps: AttackChainStep[]
  selectedStep: AttackChainStep | null
  selectedStepIndex: number
  setSelectedStepIndex: (value: number) => void
  selectedStepKey: string | null
  selectedTool: Tool | null
  stepState: Record<string, StepState>
  runningStepKey: string | null
  targetValue: string
  setTargetValue: (value: string) => void
  stepFieldValues: Record<string, Record<string, string>>
  setStepFieldValues: Dispatch<SetStateAction<Record<string, Record<string, string>>>>
  showOptionalByStep: Record<string, boolean>
  setShowOptionalByStep: Dispatch<SetStateAction<Record<string, boolean>>>
  selectedResult: { result?: ToolExecResponse; error?: string; priorResults?: ToolExecResponse[] } | undefined
  chainSuggestion: ChainSuggestion | null
  selectedChainFields: Record<string, boolean>
  onSetChainFieldSelected: (param: string, enabled: boolean) => void
  onPinChainField: (param: string) => void
  onApplyChainSuggestion: () => void
  onRunStep: (step: AttackChainStep, index: number) => Promise<void>
  onStopRunningStep: () => Promise<void>
  onApplyAttackChainFromResult: () => Promise<void>
  onRemoveTool: (index: number) => Promise<void>
  showAddTool: boolean
  setShowAddTool: Dispatch<SetStateAction<boolean>>
  addToolSearch: string
  setAddToolSearch: Dispatch<SetStateAction<string>>
  addCandidates: Tool[]
  onAddTool: (tool: Tool) => Promise<void>
}

type RemoteTerminalState = {
  command: string
  busy: boolean
  transcript: string[]
  prompt: string
  awaitingSensitiveInput: boolean
}

const EMPTY_REMOTE_TERMINAL_STATE: RemoteTerminalState = {
  command: '',
  busy: false,
  transcript: [],
  prompt: '$',
  awaitingSensitiveInput: false,
}

function exportResultEntry(
  format: 'txt' | 'json',
  tool: string,
  params: Record<string, string>,
  result: ToolExecResponse
) {
  const entry: RunHistoryEntry = {
    id: Date.now(),
    tool,
    params,
    result,
    ts: new Date(result.timestamp),
    source: 'browser',
  }
  exportEntry(entry, format)
}

function buildNoteContent(
  tool: string,
  params: Record<string, string>,
  result: ToolExecResponse
): string {
  const date = new Date(result.timestamp).toISOString()
  const lines: string[] = [
    `# ${tool}`,
    '',
    `**Date:** ${date}`,
    `**Status:** ${result.success ? 'Success' : 'Failed'} | exit ${result.return_code} | ${result.execution_time.toFixed(2)}s`,
    '',
  ]
  if (Object.keys(params).length > 0) {
    lines.push('## Parameters', '')
    for (const [k, v] of Object.entries(params)) {
      lines.push(`- **${k}:** \`${v}\``)
    }
    lines.push('')
  }
  if (result.stdout) {
    lines.push('## Output', '', '```', result.stdout, '```', '')
  }
  if (result.stderr) {
    lines.push('## Stderr', '', '```', result.stderr, '```', '')
  }
  return lines.join('\n')
}

function RemoteCommandTerminal({
  endpoint,
  baseParams,
  label,
  terminalId,
  terminalState,
  updateTerminalState,
}: {
  endpoint: string
  baseParams: Record<string, string>
  label: string
  terminalId: string
  terminalState: RemoteTerminalState
  updateTerminalState: (terminalId: string, updater: (prev: RemoteTerminalState) => RemoteTerminalState) => void
}) {
  const { command, busy, transcript, prompt, awaitingSensitiveInput } = terminalState
  const transcriptRef = useRef<HTMLPreElement | null>(null)
  const inputRef = useRef<HTMLInputElement | null>(null)

  function patchTerminal(targetTerminalId: string, patch: Partial<RemoteTerminalState>) {
    updateTerminalState(targetTerminalId, prev => ({ ...prev, ...patch }))
  }

  function appendTranscript(targetTerminalId: string, lines: string[]) {
    updateTerminalState(targetTerminalId, prev => ({
      ...prev,
      transcript: [...prev.transcript, ...lines],
    }))
  }

  useEffect(() => {
    transcriptRef.current?.scrollTo({ top: transcriptRef.current.scrollHeight })
    if (!busy) inputRef.current?.focus()
  }, [transcript])

  useEffect(() => {
    if (!busy) inputRef.current?.focus()
  }, [busy])

  async function runTerminalCommand() {
    const nextCommand = command
    if (busy) return
    const activeTerminalId = terminalId
    const activePrompt = prompt
    const activeSensitiveInput = awaitingSensitiveInput
    patchTerminal(activeTerminalId, { busy: true, command: '' })
    appendTranscript(activeTerminalId, [
      activeSensitiveInput ? '[input hidden]' : `${activePrompt} ${nextCommand}`,
    ])

    try {
      const result = await api.runTool(endpoint, {
        ...baseParams,
        command: nextCommand,
        interactive: true,
        terminal_disconnect: false,
        terminal_mode: 'raw',
      })
      const nextPrompt = (result as unknown as Record<string, unknown>).prompt
      const nextSensitiveInput = (result as unknown as Record<string, unknown>).awaiting_sensitive_input
      const output = [resultText(result, 'stdout'), resultText(result, 'stderr')].filter(Boolean).join('\n').trim()
      updateTerminalState(activeTerminalId, prev => ({
        ...prev,
        prompt: typeof nextPrompt === 'string' && nextPrompt.trim() ? `${nextPrompt.trim()}$` : prev.prompt,
        awaitingSensitiveInput: nextSensitiveInput === true,
        transcript: output ? [...prev.transcript, output] : prev.transcript,
      }))
    } catch (e) {
      appendTranscript(activeTerminalId, [`error: ${String(e)}`])
    } finally {
      patchTerminal(activeTerminalId, { busy: false })
    }
  }

  async function disconnectTerminal() {
    if (busy) return
    const activeTerminalId = terminalId
    patchTerminal(activeTerminalId, { busy: true })
    try {
      const result = await api.runTool(endpoint, {
        ...baseParams,
        command: '',
        terminal_disconnect: true,
      })
      updateTerminalState(activeTerminalId, prev => ({
        ...prev,
        prompt: '$',
        awaitingSensitiveInput: false,
        transcript: [...prev.transcript, resultText(result, 'stdout') || resultText(result, 'stderr') || 'Disconnected'],
      }))
    } catch (e) {
      appendTranscript(activeTerminalId, [`error: ${String(e)}`])
    } finally {
      patchTerminal(activeTerminalId, { busy: false })
    }
  }

  return (
    <div className="session-ssh-terminal">
      <div className="session-ssh-terminal-head">
        <span><Terminal size={12} /> {label} terminal</span>
        <button onClick={disconnectTerminal} disabled={busy} title={`Disconnect ${label} session`}>
          <Power size={12} />
        </button>
      </div>
      <pre ref={transcriptRef} className="session-ssh-terminal-body">
        {[...transcript, `${prompt} `].join('\n')}
      </pre>
      <div className="session-ssh-terminal-input">
        <input
          ref={inputRef}
          value={command}
          onChange={e => patchTerminal(terminalId, { command: e.target.value })}
          onKeyDown={e => { if (e.key === 'Enter') void runTerminalCommand() }}
          disabled={busy}
          autoComplete="off"
          type={awaitingSensitiveInput ? 'password' : 'text'}
          spellCheck={false}
        />
        <button onClick={() => void runTerminalCommand()} disabled={busy} title="Run command">
          {busy ? <RefreshCw size={12} className="spin" /> : <Send size={12} />}
        </button>
      </div>
    </div>
  )
}

export function SessionDetailWorkbench({
  isCompleted,
  sessionId,
  steps,
  selectedStep,
  selectedStepIndex,
  setSelectedStepIndex,
  selectedStepKey,
  selectedTool,
  stepState,
  runningStepKey,
  targetValue,
  setTargetValue,
  stepFieldValues,
  setStepFieldValues,
  showOptionalByStep,
  setShowOptionalByStep,
  selectedResult,
  chainSuggestion,
  selectedChainFields,
  onSetChainFieldSelected,
  onPinChainField,
  onApplyChainSuggestion,
  onRunStep,
  onStopRunningStep,
  onApplyAttackChainFromResult,
  onRemoveTool,
  showAddTool,
  setShowAddTool,
  addToolSearch,
  setAddToolSearch,
  addCandidates,
  onAddTool,
}: SessionDetailWorkbenchProps) {
  const { pushToast } = useToast()
  const selectedRunning = selectedStepKey ? runningStepKey === selectedStepKey : false
  const resultData = selectedResult?.result
  const resultStdout = resultText(resultData, 'stdout')
  const resultStderr = resultText(resultData, 'stderr')
  const selectedStepTool = selectedStep?.tool?.toLowerCase() ?? ''
  const remoteTerminalTool = (() => {
    if (
      selectedStepTool === 'ssh'
      || selectedTool?.endpoint === '/api/plugins/ssh'
      || selectedTool?.name === 'ssh'
      || selectedTool?.endpoint === '/api/tools/ssh'
    ) {
      return { endpoint: '/api/plugins/ssh', label: 'SSH' }
    }
    if (
      selectedStepTool === 'telnet'
      || selectedTool?.endpoint === '/api/plugins/telnet'
      || selectedTool?.name === 'telnet'
      || selectedTool?.endpoint === '/api/tools/telnet'
    ) {
      return { endpoint: '/api/plugins/telnet', label: 'Telnet' }
    }
    return null
  })()
  const showRemoteTerminal = !!remoteTerminalTool && !!selectedStepKey && !isCompleted
  const selectedChainCount = chainSuggestion
    ? chainSuggestion.fields.filter(field => selectedChainFields[field.param] !== false).length
    : 0
  const addToolInputRef = useRef<HTMLInputElement | null>(null)
  const [expandedPriors, setExpandedPriors] = useState<Record<number, boolean>>({})
  const [remoteTerminalStates, setRemoteTerminalStates] = useState<Record<string, RemoteTerminalState>>({})

  function updateRemoteTerminalState(terminalId: string, updater: (prev: RemoteTerminalState) => RemoteTerminalState) {
    setRemoteTerminalStates(prev => ({
      ...prev,
      [terminalId]: updater(prev[terminalId] ?? EMPTY_REMOTE_TERMINAL_STATE),
    }))
  }

  // Reset prior-run expansion state when the selected step changes
  useEffect(() => {
    setExpandedPriors({})
  }, [selectedStepKey])

  useEffect(() => {
    if (!showAddTool) return
    const frame = window.requestAnimationFrame(() => addToolInputRef.current?.focus())
    return () => window.cancelAnimationFrame(frame)
  }, [showAddTool])

  async function exportToNotes(tool: string, params: Record<string, string>, result: ToolExecResponse) {
    const date = new Date(result.timestamp)
    const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '')
    const toolSlug = tool.replace(/[^a-zA-Z0-9_]/g, '_').slice(0, 40)
    const filename = `${toolSlug}_${dateStr}`
    const content = buildNoteContent(tool, params, result)
    try {
      await api.createSessionNote(sessionId, filename, content, 'outputs')
      pushToast('success', `Exported to notes/outputs/${filename}.md`)
    } catch {
      pushToast('error', 'Failed to export to notes')
    }
  }

  return (
    <section className="section">
      <div className="section-header">
        <h3>Manual Tool Execution <span className="badge">{steps.length}</span></h3>
      </div>
      <div className="session-workbench">
        <aside className="session-workbench-tools">
          {!isCompleted && (
            <div className="session-tool-manage">
              <button className="session-add-tool-btn" onClick={() => setShowAddTool(v => !v)}>+ Add tool</button>
              {showAddTool && (
                <div className="session-add-tool-panel">
                  <input
                    ref={addToolInputRef}
                    className="search-input mono"
                    placeholder="Search tool..."
                    value={addToolSearch}
                    onChange={e => setAddToolSearch(e.target.value)}
                  />
                  <div className="session-add-tool-list">
                    {addCandidates.map(tool => (
                      <button key={tool.name} className="session-add-tool-item" onClick={() => onAddTool(tool)}>
                        <span className="mono">{tool.name}</span>
                        <span>{tool.category}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {steps.map((step, idx) => {
            const stepKey = `${sessionId}:${idx}`
            const isRunning = runningStepKey === stepKey
            return (
              <button
                key={stepKey}
                className={`session-workbench-tool session-workbench-tool--${stepState[stepKey] ?? 'idle'} ${isRunning ? 'session-workbench-tool--running' : ''} ${selectedStepIndex === idx ? 'active' : ''}`}
                onClick={() => setSelectedStepIndex(idx)}
              >
                <span className="session-workbench-tool-name mono">{step.tool}</span>
                <span className="session-workbench-tool-actions">
                  {isRunning && (
                    <span className="session-running-indicator mono" title="Tool is running">
                      <RefreshCw size={11} className="spin" /> Running
                    </span>
                  )}
                  {!isCompleted && (
                    <button
                      type="button"
                      className="session-remove-tool"
                      onClick={e => {
                        e.stopPropagation()
                        onRemoveTool(idx)
                      }}
                      title="Remove tool"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </span>
              </button>
            )
          })}
        </aside>

        <div className="session-workbench-center">
          {!selectedStep || !selectedStepKey || !selectedTool ? (
            <p className="empty-state">No tools in this session.</p>
          ) : (
            <>
              <div className="session-target-override">
                <label className="mono">Target</label>
                <input
                  name="session-target"
                  className="search-input mono"
                  value={targetValue}
                  onChange={e => setTargetValue(e.target.value)}
                  placeholder="Target to run this session against"
                  disabled={isCompleted}
                />
              </div>

              <div className="session-step-row">
                <div className="session-step-head">
                  <span className={`session-tool-chip mono session-tool-chip--${stepState[selectedStepKey] ?? 'idle'}`}>{selectedStep.tool}</span>
                  <ActionButton variant={selectedRunning ? 'running' : 'default'} disabled={isCompleted || (selectedRunning ? false : false)} onClick={selectedRunning || isCompleted ? undefined : () => onRunStep(selectedStep, selectedStepIndex)}>
                    {selectedRunning ? <RefreshCw size={12} className="spin" /> : <Play size={12} />}
                    {isCompleted ? 'Completed' : (selectedRunning ? 'Running…' : `Run ${selectedStep.tool}`)}
                  </ActionButton>
                  {selectedRunning && !isCompleted && (
                    <ActionButton variant="danger" onClick={() => { void onStopRunningStep() }}>
                      <Square size={12} /> Stop
                    </ActionButton>
                  )}
                </div>

                {selectedTool.desc && <p className="session-tool-description">{selectedTool.desc}</p>}

                {chainSuggestion && (
                  <div className="session-chain-suggestion">
                    <div className="session-chain-suggestion__text">
                      <strong className="mono">Chain hint from {chainSuggestion.sourceTool}</strong>
                      <span>
                        {chainSuggestion.summary} Confidence {safeFixed((chainSuggestion.confidence ?? 0) * 100, 0)}%
                      </span>
                      <div className="session-chain-fields">
                        {chainSuggestion.fields.map(field => {
                          const enabled = selectedChainFields[field.param] !== false
                          return (
                          <label key={field.param} className={`session-chain-field-row ${enabled ? '' : 'is-disabled'}`}>
                            <input
                              type="checkbox"
                              checked={enabled}
                              onChange={e => onSetChainFieldSelected(field.param, e.target.checked)}
                            />
                            <span className="mono">{field.param}</span>
                            <span className="mono">{field.value}</span>
                            <span className="section-meta">{Math.round(field.confidence * 100)}% {field.reason}</span>
                            <button
                              type="button"
                              className="session-chain-pin-btn"
                              onClick={() => onPinChainField(field.param)}
                              disabled={isCompleted || selectedRunning}
                            >
                              Pin
                            </button>
                          </label>
                        )})}
                      </div>
                    </div>
                    <ActionButton
                      variant="success"
                      disabled={isCompleted || selectedRunning || selectedChainCount === 0}
                      onClick={onApplyChainSuggestion}
                    >
                      Use Prior Output ({selectedChainCount})
                    </ActionButton>
                  </div>
                )}

                <div className="session-param-grid">
                  {Object.keys(selectedTool.params).map(key => (
                    <ParamField
                      key={key}
                      name={key}
                      value={stepFieldValues[selectedStepKey]?.[key] ?? ''}
                      onChange={value => setStepFieldValues(prev => ({
                        ...prev,
                        [selectedStepKey]: { ...(prev[selectedStepKey] ?? {}), [key]: value },
                      }))}
                      required
                      disabled={isCompleted}
                    />
                  ))}

                  {Object.keys(selectedTool.optional).length > 0 && (
                    <button
                      className="run-opt-btn"
                      onClick={() => setShowOptionalByStep(prev => ({ ...prev, [selectedStepKey]: !prev[selectedStepKey] }))}
                    >
                      {showOptionalByStep[selectedStepKey] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      Optional parameters ({Object.keys(selectedTool.optional).length})
                    </button>
                  )}

                  {showOptionalByStep[selectedStepKey] && Object.keys(selectedTool.optional).map(key => (
                    <ParamField
                      key={key}
                      name={key}
                      value={stepFieldValues[selectedStepKey]?.[key] ?? ''}
                      onChange={value => setStepFieldValues(prev => ({
                        ...prev,
                        [selectedStepKey]: { ...(prev[selectedStepKey] ?? {}), [key]: value },
                      }))}
                      disabled={isCompleted}
                    />
                  ))}
                </div>
              </div>

              <div className="session-result-panel">
                <h4>Result</h4>
                {isCompleted && <p className="section-meta">Completed session: results are read-only.</p>}
                {selectedResult?.error && <div className="run-error">{selectedResult.error}</div>}
                {resultData ? (
                  <>
                    <div className="session-result-head">
                      <div className="session-step-result mono">
                        {resultData.success ? 'OK' : 'FAIL'} | exit {resultData.return_code} | {safeFixed(resultData.execution_time, 2)}s
                      </div>
                      {selectedStepKey && resultData && (
                        <div className="session-result-actions">
                          <ActionButton variant="default" onClick={() => exportResultEntry('txt', selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, resultData)}>
                            <Download size={11} /> Export
                          </ActionButton>
                          <ActionButton variant="default" onClick={() => exportResultEntry('json', selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, resultData)}>
                            <Download size={11} /> JSON
                          </ActionButton>
                          <ActionButton variant="default" onClick={() => void exportToNotes(selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, resultData)}>
                            <FileText size={11} /> Notes
                          </ActionButton>
                          {selectedStep.tool === 'create-attack-chain' && resultData.success && (
                            <ActionButton disabled={isCompleted} variant="success" onClick={() => { void onApplyAttackChainFromResult() }}>
                              Use Chain
                            </ActionButton>
                          )}
                        </div>
                      )}
                    </div>
                    <pre className="session-result-pre mono">{resultStdout || '(no stdout)'}</pre>
                    {resultStderr && <pre className="session-result-pre mono">{resultStderr}</pre>}
                  </>
                ) : (
                  <p className="section-meta">No result yet for this tool.</p>
                )}
                {showRemoteTerminal && remoteTerminalTool && selectedStepKey && (
                  <RemoteCommandTerminal
                    key={`${selectedStepKey}:${remoteTerminalTool.endpoint}`}
                    endpoint={remoteTerminalTool.endpoint}
                    baseParams={stepFieldValues[selectedStepKey] ?? {}}
                    label={remoteTerminalTool.label}
                    terminalId={`${selectedStepKey}:${remoteTerminalTool.endpoint}`}
                    terminalState={remoteTerminalStates[`${selectedStepKey}:${remoteTerminalTool.endpoint}`] ?? EMPTY_REMOTE_TERMINAL_STATE}
                    updateTerminalState={updateRemoteTerminalState}
                  />
                )}
                {selectedResult?.priorResults && selectedResult.priorResults.length > 0 && (
                  <div className="session-prior-runs">
                    <p className="session-prior-runs-label">Prior runs ({selectedResult.priorResults.length})</p>
                    {selectedResult.priorResults.map((prior, i) => (
                      <div key={i} className="session-prior-run">
                        <button
                          className="session-prior-run-toggle"
                          onClick={() => setExpandedPriors(p => ({ ...p, [i]: !p[i] }))}
                        >
                          <span className="mono">{prior.success ? 'OK' : 'FAIL'} | exit {prior.return_code} | {safeFixed(prior.execution_time, 2)}s | {new Date(prior.timestamp).toLocaleTimeString()}</span>
                          {expandedPriors[i] ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                        </button>
                        {expandedPriors[i] && selectedStepKey && (
                          <div className="session-prior-run-body">
                            <div className="session-result-actions">
                              <ActionButton variant="default" onClick={() => exportResultEntry('txt', selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, prior)}>
                                <Download size={11} /> Export
                              </ActionButton>
                              <ActionButton variant="default" onClick={() => exportResultEntry('json', selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, prior)}>
                                <Download size={11} /> JSON
                              </ActionButton>
                              <ActionButton variant="default" onClick={() => void exportToNotes(selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, prior)}>
                                <FileText size={11} /> Notes
                              </ActionButton>
                            </div>
                            <pre className="session-result-pre mono">{resultText(prior, 'stdout') || '(no stdout)'}</pre>
                            {resultText(prior, 'stderr') && <pre className="session-result-pre mono">{resultText(prior, 'stderr')}</pre>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}
