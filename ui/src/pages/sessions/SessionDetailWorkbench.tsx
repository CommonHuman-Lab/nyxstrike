import { ChevronDown, ChevronUp, Download, Play, RefreshCw, Square, Trash2 } from 'lucide-react'
import { useEffect, useRef, type Dispatch, type SetStateAction } from 'react'
import { ParamField } from '../../components/tool-run/ParamField'
import type { AttackChainStep, Tool, ToolExecResponse } from '../../api'
import type { RunHistoryEntry } from '../../shared/types'
import { exportEntry } from '../../shared/utils'
import type { StepState } from './sessionDetailUtils'
import { ActionButton } from '../../components/ActionButton'

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
  selectedResult: { result?: ToolExecResponse; error?: string } | undefined
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
  const selectedRunning = selectedStepKey ? runningStepKey === selectedStepKey : false
  const resultData = selectedResult?.result
  const addToolInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!showAddTool) return
    const frame = window.requestAnimationFrame(() => addToolInputRef.current?.focus())
    return () => window.cancelAnimationFrame(frame)
  }, [showAddTool])

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
                  <ActionButton variant="default" disabled={isCompleted || selectedRunning} onClick={() => onRunStep(selectedStep, selectedStepIndex)}>
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
                        {resultData.success ? 'OK' : 'FAIL'} | exit {resultData.return_code} | {resultData.execution_time.toFixed(2)}s
                      </div>
                      {selectedStepKey && resultData && (
                        <div className="session-result-actions">
                          <ActionButton variant="default" onClick={() => exportResultEntry('txt', selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, resultData)}>
                            <Download size={11} /> Export
                          </ActionButton>
                          <ActionButton variant="default" onClick={() => exportResultEntry('json', selectedStep.tool, stepFieldValues[selectedStepKey] ?? {}, resultData)}>
                            <Download size={11} /> JSON
                          </ActionButton>
                          {selectedStep.tool === 'create-attack-chain' && resultData.success && (
                            <ActionButton disabled={isCompleted} variant="success" onClick={() => { void onApplyAttackChainFromResult() }}>
                              Use Chain
                            </ActionButton>
                          )}
                        </div>
                      )}
                    </div>
                    <pre className="session-result-pre mono">{resultData.stdout || '(no stdout)'}</pre>
                    {resultData.stderr && <pre className="session-result-pre mono">{resultData.stderr}</pre>}
                  </>
                ) : (
                  <p className="section-meta">No result yet for this tool.</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}
