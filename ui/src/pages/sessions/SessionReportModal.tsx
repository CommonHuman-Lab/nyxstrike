import { useState } from 'react'
import { Download, FileText, Brain, Archive, RefreshCw } from 'lucide-react'
import { api } from '../../api'
import { useEscapeClose } from '../../hooks/useEscapeClose'
import { reportGenStart, reportGenDone, reportGenError } from '../../app/reportGeneration'
import type { SessionSummary } from '../../api'

type ReportMode = 'structured' | 'ai'

interface Props {
  isOpen: boolean
  session: SessionSummary
  onClose: () => void
  llmAvailable?: boolean
}

function todaySlug(): string {
  return new Date().toISOString().slice(0, 10)
}

export function SessionReportModal({ isOpen, session, onClose, llmAvailable = false }: Props) {
  useEscapeClose(isOpen, onClose)

  const [mode, setMode] = useState<ReportMode>('structured')
  const [includeNotes, setIncludeNotes] = useState(false)
  const [includeEventLog, setIncludeEventLog] = useState(true)
  const [focus, setFocus] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  if (!isOpen) return null

  function downloadText(text: string, filename: string) {
    const blob = new Blob([text], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  /** Structured: preview inline (stays open) */
  async function previewStructured() {
    setLoading(true)
    setError(null)
    setPreview(null)
    try {
      const res = await api.generateSessionReport(session.session_id, {
        include_notes: includeNotes,
        include_event_log: includeEventLog,
        download: false,
      })
      if (!res.success || !res.report) {
        setError(res.error ?? 'Report generation failed.')
        return
      }
      setPreview(res.report)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  /** Structured: download .md file (stays open) */
  async function downloadStructured() {
    setLoading(true)
    setError(null)
    try {
      const res = await api.generateSessionReport(session.session_id, {
        include_notes: includeNotes,
        include_event_log: includeEventLog,
        download: false,
      })
      if (!res.success || !res.report) {
        setError(res.error ?? 'Report generation failed.')
        return
      }
      downloadText(res.report, `report-structured-${todaySlug()}.md`)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  /** Both modes: generate → close → backend saves → bubble shows result */
  function generateAndSave() {
    const isAi = mode === 'ai'
    const label = isAi
      ? `AI report — ${session.target}`
      : `Report — ${session.target}`

    // Close immediately; bubble takes over
    onClose()
    reportGenStart(label)

    const run = async () => {
      try {
        let savedPath: string | undefined
        if (isAi) {
          const res = await api.generateSessionAiReport(session.session_id, {
            include_notes: includeNotes,
            include_event_log: includeEventLog,
            focus: focus.trim() || undefined,
            download: false,
            save_to_notes: true,
          })
          if (!res.success) {
            reportGenError(label, res.error ?? 'AI report generation failed.')
            return
          }
          savedPath = res.saved_path
        } else {
          const res = await api.generateSessionReport(session.session_id, {
            include_notes: includeNotes,
            include_event_log: includeEventLog,
            download: false,
            save_to_notes: true,
          })
          if (!res.success) {
            reportGenError(label, res.error ?? 'Report generation failed.')
            return
          }
          savedPath = res.saved_path
        }
        reportGenDone(label, savedPath ?? 'notes/reports/')
      } catch (e) {
        reportGenError(label, String(e))
      }
    }

    run()
  }

  function handleNotesExport() {
    const url = api.exportSessionNotesUrl(session.session_id)
    window.open(url, '_blank')
  }

  return (
    <div className="report-modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="report-modal">
        <div className="report-modal-header">
          <div className="modal-title-row">
            <FileText size={14} />
            <span className="modal-name">Generate Report</span>
            <span className="section-meta mono">{session.target}</span>
          </div>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="report-modal-tabs">
          <button
            className={`report-modal-tab${mode === 'structured' ? ' report-modal-tab--active' : ''}`}
            onClick={() => { setMode('structured'); setPreview(null); setError(null) }}
          >
            <FileText size={12} /> Structured
          </button>
          <button
            className={`report-modal-tab${mode === 'ai' ? ' report-modal-tab--active' : ''}`}
            onClick={() => { setMode('ai'); setPreview(null); setError(null) }}
            disabled={!llmAvailable}
            title={!llmAvailable ? 'No LLM configured. Start the server with --ai or --ai-small to enable AI-assisted reports.' : undefined}
          >
            <Brain size={12} /> AI-Assisted
          </button>
        </div>

        <div className="report-modal-body">
          {mode === 'ai' && (
            <div className="report-modal-note section-meta">
              Generates a structured report with an AI executive summary.
              Saved automatically to <span className="mono">notes/reports/</span> when done.
              Requires a configured LLM provider.
            </div>
          )}

          <div className="report-modal-options">
            <label className="report-option-row">
              <input
                type="checkbox"
                checked={includeNotes}
                onChange={e => setIncludeNotes(e.target.checked)}
              />
              <span>Include session notes</span>
            </label>
            <label className="report-option-row">
              <input
                type="checkbox"
                checked={includeEventLog}
                onChange={e => setIncludeEventLog(e.target.checked)}
              />
              <span>Include activity timeline</span>
            </label>
            {mode === 'ai' && (
              <div className="report-option-focus">
                <label className="section-meta">Focus / context (optional)</label>
                <input
                  className="findings-form-input"
                  placeholder="e.g. focus on RCE and privilege escalation findings"
                  value={focus}
                  onChange={e => setFocus(e.target.value)}
                />
              </div>
            )}
          </div>

          {error && (
            <div className="report-modal-error">{error}</div>
          )}

          <div className="report-modal-actions">
            {/* Generate & save — works for both modes, closes the modal */}
            <button
              className="session-action-btn session-action-btn--primary"
              onClick={generateAndSave}
            >
              {mode === 'ai'
                ? <><Brain size={12} /> Generate &amp; Save</>
                : <><FileText size={12} /> Generate &amp; Save</>
              }
            </button>

            {/* Structured-only extras */}
            {mode === 'structured' && (
              <>
                <button
                  className="session-action-btn"
                  onClick={previewStructured}
                  disabled={loading}
                >
                  {loading ? <><RefreshCw size={12} className="spin" /> Generating…</> : 'Preview'}
                </button>
                <button
                  className="session-action-btn"
                  onClick={downloadStructured}
                  disabled={loading}
                >
                  <Download size={12} /> Download .md
                </button>
              </>
            )}

            <button
              className="session-action-btn"
              onClick={handleNotesExport}
              title="Download all session notes as a ZIP archive"
            >
              <Archive size={12} /> Export Notes (.zip)
            </button>
          </div>

          {preview && (
            <div className="report-preview">
              <pre className="report-preview-content">{preview}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
