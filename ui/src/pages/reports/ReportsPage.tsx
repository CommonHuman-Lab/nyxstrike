import { useState } from 'react'
import {
  BarChart2, CheckCircle, Clock, TrendingUp, FileText,
} from 'lucide-react'
import { StatCard } from '../../components/StatCard'
import { RunResultModal } from '../../components/RunResultModal'
import { type RunHistoryEntry } from '../../shared/types'
import { ReportsBreakdownSection, ReportsTimelineSection } from './ReportsSections'
import { AiAnalysisSection } from './AiAnalysisSection'
import { extractTarget, type GroupBy } from './reportUtils'
import { safeFixed } from '../../shared/utils'
import './ReportsPage.css'

interface ReportsPageProps {
  runHistory: RunHistoryEntry[]
}

export default function ReportsPage({ runHistory }: ReportsPageProps) {
  const [groupBy, setGroupBy] = useState<GroupBy>('tool')
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [modalEntry, setModalEntry] = useState<RunHistoryEntry | null>(null)

  const byTool = runHistory.reduce<Record<string, RunHistoryEntry[]>>((acc, e) => {
    ;(acc[e.tool] = acc[e.tool] || []).push(e)
    return acc
  }, {})

  const byTarget = runHistory.reduce<Record<string, RunHistoryEntry[]>>((acc, e) => {
    const t = extractTarget(e)
    ;(acc[t] = acc[t] || []).push(e)
    return acc
  }, {})

  const grouped = groupBy === 'tool' ? byTool : byTarget

  function toggleExpanded(key: string) {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  const q = search.toLowerCase()
  const keys = Object.keys(grouped).filter(k => !q || k.toLowerCase().includes(q)).sort()

  if (runHistory.length === 0) return (
    <div className="page-content">
      <div className="tasks-empty">
        <FileText size={32} color="var(--text-dim)" />
        <p>No run history yet. Execute tools from the Run tab to see reports.</p>
      </div>
    </div>
  )

  return (
    <div className="page-content">
      {modalEntry && (
        <RunResultModal entry={modalEntry} onClose={() => setModalEntry(null)} />
      )}

      <div className="kpi-row">
        <StatCard icon={<BarChart2 size={20} />} label="Total Runs" value={runHistory.length} sub="all time" accent="var(--blue)" />
        <StatCard
          icon={<CheckCircle size={20} />}
          label="Success Rate"
          value={runHistory.length > 0 ? `${((runHistory.filter(e => e.result.success).length / runHistory.length) * 100).toFixed(0)}%` : '—'}
          sub={`${runHistory.filter(e => e.result.success).length} ok · ${runHistory.filter(e => !e.result.success).length} failed`}
          accent="var(--green)"
        />
        <StatCard
          icon={<Clock size={20} />}
          label="Avg Time"
          value={`${safeFixed(runHistory.length > 0 ? runHistory.reduce((s, e) => s + (e.result.execution_time ?? 0), 0) / runHistory.length : undefined, 1)}s`}
          sub="per run"
          accent="var(--purple)"
        />
        <StatCard
          icon={<TrendingUp size={20} />}
          label="Unique Tools"
          value={Object.keys(byTool).length}
          sub="used"
          accent="var(--amber)"
        />
      </div>

      <ReportsTimelineSection runHistory={runHistory} onOpenEntry={setModalEntry} />

      <ReportsBreakdownSection
        grouped={grouped}
        keys={keys}
        groupBy={groupBy}
        search={search}
        setSearch={setSearch}
        setGroupBy={setGroupBy}
        expanded={expanded}
        toggleExpanded={toggleExpanded}
        onOpenEntry={setModalEntry}
      />

      <AiAnalysisSection />
    </div>
  )
}
