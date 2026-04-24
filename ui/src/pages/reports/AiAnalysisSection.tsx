import { useState } from 'react'
import { Brain, RefreshCw } from 'lucide-react'
import { api } from '../../api'
import type { LlmSession, LlmVulnerability } from '../../api/types/llm'
import { CollapseChevron } from '../../components/CollapseChevron'

const RISK_COLOR: Record<string, string> = {
  CRITICAL: 'var(--red)',
  HIGH:     'var(--red)',
  MEDIUM:   'var(--amber)',
  LOW:      'var(--green)',
  UNKNOWN:  'var(--text-dim)',
}

function riskColor(level: string | null): string {
  return RISK_COLOR[(level ?? '').toUpperCase()] ?? 'var(--text-dim)'
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString()
}

interface SessionRowProps {
  session: LlmSession
}

function SessionRow({ session }: SessionRowProps) {
  const [open, setOpen] = useState(false)
  const [vulns, setVulns] = useState<LlmVulnerability[] | null>(null)
  const [loading, setLoading] = useState(false)

  async function toggle() {
    if (!open && vulns === null) {
      setLoading(true)
      try {
        const detail = await api.llmSessionDetail(session.session_id)
        setVulns(detail.vulnerabilities)
      } catch {
        setVulns([])
      } finally {
        setLoading(false)
      }
    }
    setOpen(o => !o)
  }

  const color = riskColor(session.risk_level)

  return (
    <div className="reports-group">
      <button className="ai-report-row" onClick={toggle}>
        <span className="reports-chevron">
          <CollapseChevron open={open} size={12} />
        </span>
        <span className="mono ai-report-target">{session.target || '—'}</span>
        <span className="mono" style={{ color, fontWeight: 600 }}>
          {session.risk_level ?? 'UNKNOWN'}
        </span>
        <span className="mono ai-report-session">{session.session_id}</span>
        <span className="mono ai-report-date">{fmtDate(session.completed_at ?? session.started_at)}</span>
        <span className="mono ai-report-model" title={`${session.provider ?? ''} / ${session.model ?? ''}`}>
          {session.model ?? '—'}
        </span>
      </button>

      {open && (
        <div className="ai-report-detail">
          {session.summary && (
            <p className="ai-report-summary">{session.summary}</p>
          )}

          {loading && (
            <div className="ai-report-loading">
              <RefreshCw size={12} className="spin" /> Loading findings…
            </div>
          )}

          {vulns && vulns.length === 0 && !loading && (
            <p className="ai-report-no-vulns">No findings recorded.</p>
          )}

          {vulns && vulns.length > 0 && (
            <div className="ai-report-vulns">
              {vulns.map(v => (
                <div key={v.id} className="ai-report-vuln">
                  <span
                    className="ai-report-vuln-badge"
                    style={{ background: riskColor(v.severity), color: '#000' }}
                  >
                    {v.severity || 'INFO'}
                  </span>
                  <span className="ai-report-vuln-name">{v.vuln_name || 'Unnamed finding'}</span>
                  {(v.port || v.service) && (
                    <span className="mono ai-report-vuln-port">
                      {[v.port, v.service].filter(Boolean).join(' / ')}
                    </span>
                  )}
                  {v.description && (
                    <p className="ai-report-vuln-desc">{v.description}</p>
                  )}
                  {v.fix_text && (
                    <p className="ai-report-vuln-fix">Fix: {v.fix_text}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function AiAnalysisSection() {
  const [sectionOpen, setSectionOpen] = useState(false)
  const [sessions, setSessions] = useState<LlmSession[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await api.llmSessions(100)
      setSessions(res.sessions)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  function handleToggle() {
    if (!sectionOpen && sessions === null) {
      void load()
    }
    setSectionOpen(o => !o)
  }

  return (
    <section className="section">
      <div className="section-header" style={{ cursor: 'pointer' }} onClick={handleToggle}>
        <h3>
          <CollapseChevron open={sectionOpen} size={13} className="section-chevron" />
          <Brain size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} />
          AI Analysis Reports
          {sessions !== null && (
            <span className="badge" style={{ marginLeft: 8 }}>{sessions.length}</span>
          )}
        </h3>
        {sectionOpen && (
          <button
            className="icon-btn"
            onClick={e => { e.stopPropagation(); void load() }}
            title="Refresh"
          >
            <RefreshCw size={14} className={loading ? 'spin' : undefined} />
          </button>
        )}
      </div>

      {sectionOpen && (
        <>
          {loading && sessions === null && (
            <div className="tasks-empty">
              <RefreshCw size={24} className="spin" color="var(--text-dim)" />
              <p>Loading AI analysis reports…</p>
            </div>
          )}

          {error && (
            <div className="tasks-empty">
              <p style={{ color: 'var(--red)' }}>{error}</p>
            </div>
          )}

          {sessions !== null && sessions.length === 0 && !loading && (
            <div className="tasks-empty">
              <Brain size={32} color="var(--text-dim)" />
              <p>No AI analysis reports yet. Run the AI Analyze step inside a session.</p>
            </div>
          )}

          {sessions !== null && sessions.length > 0 && (
            <div className="reports-table">
              <div className="ai-report-thead">
                <span></span>
                <span>Target</span>
                <span>Risk</span>
                <span>Session</span>
                <span>Date</span>
                <span>Model</span>
              </div>
              {sessions.map(s => (
                <SessionRow key={s.session_id} session={s} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
