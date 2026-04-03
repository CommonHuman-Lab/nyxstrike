import { XCircle } from 'lucide-react'
import { type WebDashboardResponse, type Tool } from '../../api'
import type { HistoryPoint, RunHistoryEntry } from '../../shared/types'
import { KpiSection } from './KpiSection'
import { ResourceSection } from './ResourceSection'
import { ToolAvailabilitySection } from './ToolAvailabilitySection'
import './DashboardPage.css'

// ─── Dashboard Page ───────────────────────────────────────────────────────────

interface DashboardPageProps {
  health: WebDashboardResponse
  tools: Tool[]
  history: HistoryPoint[]
  runHistory: RunHistoryEntry[]
  loading: boolean
  error: string | null
  toolCategories: Record<string, string[]>;
}

export function DashboardPage({ health, tools, history, runHistory, loading, error, toolCategories }: DashboardPageProps) {
  return (
    <>
      {loading && !health && (
        <div className="loading-state">
          <div className="spin" style={{ width: 24, height: 24, border: '2px solid var(--green)', borderTopColor: 'transparent', borderRadius: '50%' }} />
          <p>Connecting to server…</p>
        </div>
      )}

      {error && !health && (
        <div className="error-banner">
          <XCircle size={16} /> {error} — is the server running on port 8888?
        </div>
      )}

      <KpiSection health={health} tools={tools} runHistory={runHistory} />
      <ResourceSection health={health} history={history} />
      <ToolAvailabilitySection health={health} tools={tools} toolCategories={toolCategories} />

      <div className="dashboard-signature-wrap">
        <span className="dashboard-signature mono">Made by CommonHuman</span>
      </div>
    </>
  )
}
