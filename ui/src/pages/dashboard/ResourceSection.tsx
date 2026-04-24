import { Activity, Cpu, HardDrive, HardDriveDownload, MemoryStick, Upload } from 'lucide-react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { WebDashboardResponse } from '../../api'
import type { HistoryPoint } from '../../shared/types'
import { fmt, formatBytes } from '../../shared/utils'
import { GaugeBar } from '../../components/GaugeBar'
import { useSystemResources } from './useSystemResources'

function ResourceChart({ data }: { data: HistoryPoint[] }) {
  const ticks = data.map(d => ({ ...d, time: new Date(d.t).toLocaleTimeString('en-GB') }))
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={120}>
        <AreaChart data={ticks} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
          <defs>
            <linearGradient id="cpu-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--green)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--green)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="mem-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--blue)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--blue)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="time" tick={{ fill: 'var(--text-dim)', fontSize: 10 }} interval="preserveStartEnd" />
          <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-dim)', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-card2)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: 'var(--text-h)' }}
          />
          <Area type="monotone" dataKey="cpu" name="CPU %" stroke="var(--green)" fill="url(#cpu-grad)" strokeWidth={1.5} dot={false} />
          <Area type="monotone" dataKey="mem" name="Mem %" stroke="var(--blue)" fill="url(#mem-grad)" strokeWidth={1.5} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ResourceSection({
  demoResources,
  demoHistory,
}: {
  /** Pass demo resource data when running in demo mode; omit for live stream. */
  demoResources?: WebDashboardResponse['resources']
  /** Pre-seeded history points for demo mode chart. */
  demoHistory?: HistoryPoint[]
}) {
  const { resources, resources_timestamp, history } = useSystemResources(
    demoResources,
    demoHistory
  )

  const localResourcesTime = (() => {
    const raw = resources_timestamp
    if (!raw) return ''

    const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T')
    const sanitized = normalized.replace(/([+-]\d{2}:\d{2})Z$/, '$1')
    const candidates = [sanitized, `${sanitized}Z`, normalized, raw]
    for (const candidate of candidates) {
      const parsed = new Date(candidate)
      if (!Number.isNaN(parsed.getTime())) {
        return parsed.toLocaleTimeString('en-GB', { hour12: false })
      }
    }

    const timeMatch = raw.match(/\b\d{2}:\d{2}:\d{2}\b/)
    return timeMatch?.[0] ?? ''
  })()

  if (!resources) {
    return (
      <section className="section">
        <div className="section-header">
          <h3>System Resources</h3>
        </div>
        <p className="chart-placeholder">Connecting…</p>
      </section>
    )
  }

  return (
    <section className="section">
      <div className="section-header">
        <h3>System Resources</h3>
        <span className="section-meta mono">{localResourcesTime}</span>
      </div>
      <div className="resources-layout">
        <div className="gauges-col">
          <GaugeBar label="CPU" value={resources.cpu_percent} color="var(--green)" />
          <GaugeBar label="Memory" value={resources.memory_percent} color="var(--blue)" />
          {resources.disk_percent !== undefined && (
            <GaugeBar label="Disk" value={resources.disk_percent} color="var(--purple)" />
          )}
          <div className="resource-detail-row">
            <div className="resource-detail">
              <Cpu size={12} color="var(--text-dim)" />
              <span title="CPU Usage">{fmt(resources.cpu_percent)}% CPU</span>
            </div>
            <div className="resource-detail">
              <MemoryStick size={12} color="var(--text-dim)" />
              <span title="Memory Usage">{fmt(resources.memory_used_gb, 1)} / {fmt(resources.memory_total_gb, 1)} GB</span>
            </div>
            {resources.disk_used_gb !== undefined && (
              <div className="resource-detail">
                <HardDrive size={12} color="var(--text-dim)" />
                <span title="Disk Usage">{fmt(resources.disk_used_gb, 1)} / {fmt(resources.disk_total_gb, 1)} GB</span>
              </div>
            )}
            <div className="resource-detail">
              <Upload size={12} color="var(--text-dim)" />
              <span title="Total Sent">{formatBytes(resources.network_bytes_sent)}</span>
            </div>
            <div className="resource-detail">
              <HardDriveDownload size={12} color="var(--text-dim)" />
              <span title="Total Received">{formatBytes(resources.network_bytes_recv)}</span>
            </div>
            {resources.load_avg && (
              <div className="resource-detail">
                <Activity size={12} color="var(--text-dim)" />
                <span>load {resources.load_avg.map(l => fmt(l, 2)).join(' ')}</span>
              </div>
            )}
          </div>
        </div>
        <div className="chart-col">
          <div className="chart-legend">
            <span><span className="legend-dot" style={{ background: 'var(--green)' }} />CPU</span>
            <span><span className="legend-dot" style={{ background: 'var(--blue)' }} />Memory</span>
          </div>
          {history.length > 1
            ? <ResourceChart data={history} />
            : <p className="chart-placeholder">Collecting data…</p>}
        </div>
      </div>
    </section>
  )
}
