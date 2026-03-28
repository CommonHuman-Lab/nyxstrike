import React, { useState } from 'react'
import {
  Activity, Cpu, HardDrive, MemoryStick, Shield, Server,
  CheckCircle, XCircle, AlertCircle,
  ChevronDown, ChevronRight, Database, Zap, Wifi,
  Lock, Eye,
  Bug,
  Wrench,
  Box,
  Wand,
  Fingerprint,
  Earth,
  Brain,
  Upload,
  HardDriveDownload,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import { type WebDashboardResponse, type Tool } from '../api'
import { fmt, uptimeStr } from '../utils'
import { StatCard } from '../components/StatCard'
import { GaugeBar } from '../components/GaugeBar'
import { ToolModal } from '../components/ToolModal'
import type { HistoryPoint, RunHistoryEntry } from '../types'
import './DashboardPage.css'

// ─── Mini Area Chart ──────────────────────────────────────────────────────────

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

// ─── Tool Availability Section ────────────────────────────────────────────────
// Icons : https://lucide.dev/icons/
const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  // server health category names
  essential: <Wand size={14} />,
  network_recon: <Wifi size={14} />,
  web_recon: <Activity size={14} />,
  web_vuln: <AlertCircle size={14} />,
  brute_force: <Lock size={14} />,
  binary: <Cpu size={14} />,
  forensics: <Database size={14} />,
  cloud: <Server size={14} />,
  osint: <Eye size={14} />,
  exploitation: <Zap size={14} />,
  api: <Activity size={14} />,
  wifi_pentest: <Wifi size={14} />,
  database: <Database size={14} />,
  vulnerability_intelligence: <Bug size={14} />,
  active_directory: <Box size={14} />,
  fingerprint: <Fingerprint size={14} />,
  ops: <Earth size={14} />,
  intelligence: <Brain size={14} />,
}

function ToolCategoryRow({ category, stats, toolStatuses, toolsByName }: {
  category: string
  stats: { total: number; available: number }
  toolStatuses: Record<string, boolean>
  toolsByName: Record<string, Tool>
}) {
  const [open, setOpen] = useState(false)
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const pct = stats.total > 0 ? (stats.available / stats.total) * 100 : 0
  const color = pct === 100 ? 'var(--green)' : pct > 50 ? 'var(--amber)' : 'var(--red)'

  const toolsInCat = Object.entries(toolStatuses).sort(([a], [b]) => a.localeCompare(b))

  return (
    <>
      {selectedTool && (
        <ToolModal
          tool={selectedTool}
          onClose={() => setSelectedTool(null)}
          installed={toolStatuses[selectedTool.name]}
        />
      )}
      <div className="cat-row">
        <button className="cat-header" onClick={() => setOpen(o => !o)}>
          <span className="cat-icon" style={{ color }}>{CATEGORY_ICONS[category] || <Shield size={14} />}</span>
          <span className="cat-name">{category.replace(/_/g, ' ')}</span>
          <span className="cat-badge" style={{ background: color + '22', color }}>
            {stats.available}/{stats.total}
          </span>
          <div className="cat-bar-bg">
            <div className="cat-bar-fill" style={{ width: `${pct}%`, background: color }} />
          </div>
          <span className="cat-chevron">{open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</span>
        </button>
        {open && (
          <div className="cat-tools-grid">
            {toolsInCat.map(([name, avail]) => {
              const toolObj = toolsByName[name]
              return (
                <div
                  key={name}
                  className={`tool-chip ${avail ? 'available' : 'missing'}${toolObj ? ' tool-chip--clickable' : ''}`}
                  onClick={toolObj ? () => setSelectedTool(toolObj) : undefined}
                  title={toolObj ? `Click for details on ${name}` : undefined}
                >
                  {avail
                    ? <CheckCircle size={10} color="var(--green)" />
                    : <XCircle size={10} color="var(--red)" />}
                  <span className="mono">{name}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </>
  )
}

function getCatTools(cat: string, allStatuses: Record<string, boolean>, toolCategories: Record<string, string[]>): string[] {
  const fromApi = toolCategories[cat] ?? []
  if (fromApi.length > 0) return fromApi
  return Object.keys(allStatuses)
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = parseFloat((bytes / Math.pow(k, i)).toFixed(2));
  return `${value} ${sizes[i]}`;
}

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
  const cu = health.resources

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

      {/* ── KPI Row ── */}
      <div className="kpi-row">
        <StatCard
          icon={<Activity size={20} />}
          label="Server Status"
          value={health.status.charAt(0).toUpperCase() + health.status.slice(1)}
          sub={`uptime ${uptimeStr(health.uptime)}`}
          accent={health.status === 'healthy' ? 'var(--green)' : 'var(--red)'}
        />
        <StatCard
          icon={<Shield size={20} />}
          label="Kali Tools"
          value={`${health.total_tools_available} / ${health.total_tools_count}`}
          sub={health.all_essential_tools_available ? 'all essential ready' : 'some essential missing'}
          accent={health.all_essential_tools_available ? 'var(--green)' : 'var(--amber)'}
        />
        <StatCard icon={<Wrench size={20} />} label="Server Tools" value={tools.length} sub="in registry" accent="var(--blue)" />
        <StatCard
          icon={<Zap size={20} />}
          label="Commands"
          value={(() => {
            const serverCount = health.telemetry?.commands_executed ?? 0
            return Math.max(serverCount, runHistory.length)
          })()}
          sub={(() => {
            const serverCount = health.telemetry?.commands_executed ?? 0
            const localCount = runHistory.length
            if (localCount > serverCount) {
              const ok = runHistory.filter(e => e.result.success).length
              return `${ok} ok · ${localCount - ok} failed`
            }
            const rate = parseFloat(health.telemetry?.success_rate ?? '0')
            const ok = Math.round(serverCount * rate / 100)
            return `${ok} ok · ${serverCount - ok} failed`
          })()}
          accent="var(--purple)"
        />
      </div>

      {/* ── Resource Row ── */}
      {cu && (
        <section className="section">
          <div className="section-header">
            <h3>System Resources</h3>
            <span className="section-meta mono">{health?.resources_timestamp?.slice(11, 19)}</span>
          </div>
          <div className="resources-layout">
            <div className="gauges-col">
              <GaugeBar label="CPU" value={cu.cpu_percent} />
              <GaugeBar label="Memory" value={cu.memory_percent} />
              {cu.disk_percent !== undefined && (
                <GaugeBar label="Disk" value={cu.disk_percent} />
              )}
              <div className="resource-detail-row">
                <div className="resource-detail">
                  <Cpu size={12} color="var(--text-dim)" />
                  <span title='CPU Usage'>{fmt(cu.cpu_percent)}% CPU</span>
                </div>
                <div className="resource-detail">
                  <MemoryStick size={12} color="var(--text-dim)" />
                  <span title='Memory Usage'>{fmt(cu.memory_used_gb, 1)} / {fmt(cu.memory_total_gb, 1)} GB</span>
                </div>
                {cu.disk_used_gb !== undefined && (
                  <div className="resource-detail">
                    <HardDrive size={12} color="var(--text-dim)" />
                    <span title='Disk Usage'>{fmt(cu.disk_used_gb, 1)} / {fmt(cu.disk_total_gb, 1)} GB</span>
                  </div>
                )} 
                <div className="resource-detail">
                  <Upload size={12} color="var(--text-dim)" />
                  <span title='Total Sent'>{formatBytes(cu.network_bytes_sent)}</span>
                </div>
                <div className="resource-detail">
                  <HardDriveDownload size={12} color="var(--text-dim)" />
                  <span title='Total Received'>{formatBytes(cu.network_bytes_recv)}</span>
                </div>
                {cu.load_avg && (
                  <div className="resource-detail">
                    <Activity size={12} color="var(--text-dim)" />
                    <span>load {cu.load_avg.map(l => fmt(l, 2)).join(' ')}</span>
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
      )}

      {/* ── Tool Availability ── */}
      <section className="section">
        <div className="section-header">
          <h3>Tool Availability</h3>
          <span className="section-meta">
            {(() => {
              const s = health.tool_availability_age_seconds
              if (s === null || s === undefined) return 'not yet checked'
              if (s < 60) return 'just checked'
              if (s < 120) return 'checked a minute ago'
              if (s < 3600) return `checked ${Math.floor(s / 60)} minutes ago`
              if (s < 7200) return 'checked over an hour ago'
              return `checked ${Math.floor(s / 3600)} hours ago`
            })()}
          </span>
        </div>
        <div className="cat-list">
          {Object.entries(health.category_stats).sort(([a], [b]) => a.localeCompare(b)).map(([cat, stats]) => {
            const catToolNames = getCatTools(cat, health.tools_status, toolCategories)
            const catStatuses = Object.fromEntries(
              catToolNames.map(n => [n, health.tools_status[n] ?? false])
            )
            const toolsByName = Object.fromEntries(tools.map(t => [t.name, t]))
            return (
              <ToolCategoryRow
                key={cat}
                category={cat}
                stats={stats}
                toolStatuses={catStatuses}
                toolsByName={toolsByName}
              />
            )
          })}
        </div>
      </section>
    </>
  )
}
