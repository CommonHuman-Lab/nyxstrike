import {
  RefreshCw, XCircle,
} from 'lucide-react'
import type { ProcessDashboardResponse } from '../../api'
import { useProcessDashboard } from './useProcessDashboard'
import { ProcessesSection, WorkerPoolSection } from './TasksSections'
import './TasksPage.css'

interface TasksPageProps {
  demoData?: { processes: ProcessDashboardResponse }
}

export default function TasksPage({ demoData }: TasksPageProps) {
  const {
    data,
    poolStats,
    loading,
    error,
    actionMsg,
    streamStatus,
    fetchData,
    pauseProcess,
    resumeProcess,
    terminateProcess,
    cancelAiTask,
  } = useProcessDashboard(demoData)

  if (loading && !data) return (
    <div className="loading-state">
      <RefreshCw size={20} className="spin" color="var(--green)" />
      <p>Loading tasks…</p>
    </div>
  )
  if (error && !data) return (
    <div className="error-banner"><XCircle size={16} /> {error}</div>
  )

  const processes = (data?.processes ?? []).slice(-100)

  return (
    <div className="page-content">
      {poolStats && (
        <WorkerPoolSection data={data} streamStatus={streamStatus} />
      )}

      <ProcessesSection
        processes={processes}
        actionMsg={actionMsg}
        streamStatus={streamStatus}
        onRefresh={fetchData}
        onPause={pauseProcess}
        onResume={resumeProcess}
        onTerminate={terminateProcess}
        onCancelAiTask={cancelAiTask}
      />
    </div>
  )
}
