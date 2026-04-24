import { XCircle } from 'lucide-react'
import { type WebDashboardResponse, type Tool } from '../../api'
import type { RunHistoryEntry, HistoryPoint } from '../../shared/types'
import { KpiSection } from './KpiSection'
import { ResourceSection } from './ResourceSection'
import { ToolAvailabilitySection } from './ToolAvailabilitySection'
import './DashboardPage.css'

// ─── Dashboard Page ───────────────────────────────────────────────────────────

interface DashboardPageProps {
  health: WebDashboardResponse
  tools: Tool[]
  runHistory: RunHistoryEntry[]
  loading: boolean
  error: string | null
  toolCategories: Record<string, string[]>
  demo?: boolean
  demoCpuHistory?: unknown
}

export function DashboardPage({ health, tools, runHistory, loading, error, toolCategories, demo, demoCpuHistory }: DashboardPageProps) {
  return (
    <>
      {loading && !health && (
        <div className="loading-state">
          <div className="spin spin--sm spin--green" />
          <p>Connecting to server…</p>
        </div>
      )}

      {error && !health && (
        <div className="error-banner">
          <XCircle size={16} /> {error} — is the server running on port 8888?
        </div>
      )}

      <KpiSection health={health} tools={tools} runHistory={runHistory} />
      <ResourceSection
        demoResources={demo ? health?.resources : undefined}
        demoHistory={demo ? demoCpuHistory as HistoryPoint[] | undefined : undefined}
      />
      <ToolAvailabilitySection health={health} tools={tools} toolCategories={toolCategories} />

      <div className="dashboard-signature-wrap">
        <span className="dashboard-signature mono">
            <a
            href="https://github.com/CommonHuman-Lab"
            target="_blank"
            rel="noreferrer">
              Made by CommonHuman
            </a>
          </span>
      </div>
    </>
  )
}
