import React, { useState } from 'react'
import {
  Activity, Cpu, HardDrive, MemoryStick, Shield, Server,
  CheckCircle, XCircle, AlertCircle,
  ChevronDown, ChevronRight, Database, Zap, Wifi,
  Lock, Eye,
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

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  // server health category names
  essential: <Shield size={14} />,
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

// Map health category names to their tool lists (mirrors _HEALTH_TOOL_CATEGORIES in Python)
// Also includes tool_registry.py category names used by demo mode.
const HEALTH_CAT_TOOLS: Record<string, string[]> = {
    "essential": ["nmap", "gobuster", "dirb", "nikto", "sqlmap", "hydra", "john", "hashcat"],
    "network_recon": ["rustscan", "masscan", "autorecon", "nbtscan", "arp-scan", "responder",
                "nxc", "enum4linux-ng", "rpcclient", "enum4linux", "smbmap", "evil-winrm"],
    "web_recon": ["ffuf", "feroxbuster", "dirsearch", "dotdotpwn", "xsser", "wfuzz",
                     "arjun", "paramspider", "x8", "jaeles", "dalfox",
                     "httpx", "wafw00f", "burpsuite", "katana", "hakrawler", "wpscan"],
    "web_vuln": ["nuclei", "graphql-scanner", "jwt-analyzer", "zaproxy"],
    "brute_force": ["medusa", "patator", "hashid", "ophcrack", "hashcat-utils"],
    "binary": ["gdb", "radare2", "binwalk", "ROPgadget", "checksec", "objdump",
               "ghidra", "pwntools", "one-gadget", "ropper", "angr", "libc-database", "pwninit"],
    "forensics": ["vol", "steghide", "hashpump", "foremost", "exiftool",
                  "strings", "xxd", "file", "photorec", "testdisk", "scalpel",
                  "bulk_extractor", "stegsolve", "zsteg", "outguess", "volatility", "sleuthkit", "autopsy"],
    "cloud": ["prowler", "scout-suite", "trivy", "kube-hunter", "kube-bench",
              "docker-bench-security", "checkov", "terrascan", "falco", "clair",
              "cloudmapper", "pacu"],
    "osint": ["amass", "subfinder", "fierce", "dnsenum", "theharvester", "sherlock",
              "social-analyzer", "recon-ng", "maltego", "spiderfoot", "shodan-cli",
              "censys-cli", "have-i-been-pwned", "whois", "bbot", "gau", "waybackurls"],
    "exploitation": ["msfconsole", "msfvenom", "searchsploit"],
    "api": ["api-schema-analyzer", "postman", "insomnia", "curl", "httpie", "anew", "qsreplace", "uro"],
    "wifi_pentest": ["kismet", "wireshark", "tshark", "tcpdump",
                 "airbase-ng", "airdecap-ng", "hcxdumptool", "hcxpcapngtool",
                 "mdk4", "eaphammer", "wifite", "bettercap", "airmon-ng", "airodump-ng", "aireplay-ng", "aircrack-ng"],
    "database": ["mysql", "sqlite3"],
    //"active_directory": [
    //    "impacket-scripts", "bloodhound-ce-python", "ldapdomaindump",
    //    "certipy-ad", "mitm6", "adidnsdump", "pywerview"
    //]
}

function getCatTools(cat: string, allStatuses: Record<string, boolean>): string[] {
  const known = HEALTH_CAT_TOOLS[cat] ?? []
  if (known.length > 0) return known
  return Object.keys(allStatuses)
}

// ─── Dashboard Page ───────────────────────────────────────────────────────────

interface DashboardPageProps {
  health: WebDashboardResponse
  tools: Tool[]
  history: HistoryPoint[]
  dashCacheSize: number | null
  dashCacheHits: number | null
  runHistory: RunHistoryEntry[]
  loading: boolean
  error: string | null
}

export function DashboardPage({ health, tools, history, dashCacheSize, dashCacheHits, runHistory, loading, error }: DashboardPageProps) {
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
          label="Tools Installed"
          value={`${health.total_tools_available} / ${health.total_tools_count}`}
          sub={health.all_essential_tools_available ? 'all essential ready' : 'some essential missing'}
          accent={health.all_essential_tools_available ? 'var(--green)' : 'var(--amber)'}
        />
        <StatCard
          icon={<Database size={20} />}
          label="Cache"
          value={dashCacheHits !== null ? `${dashCacheHits} hits` : '—'}
          sub={dashCacheSize !== null ? `${dashCacheSize} size` : 'cache config'}
          accent="var(--blue)"
        />
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
                  <span>{fmt(cu.cpu_percent)}% CPU</span>
                </div>
                <div className="resource-detail">
                  <MemoryStick size={12} color="var(--text-dim)" />
                  <span>{fmt(cu.memory_percent, 1)}% used · {fmt(cu.memory_available_gb, 1)} GB free</span>
                </div>
                {cu.disk_free_gb !== undefined && (
                  <div className="resource-detail">
                    <HardDrive size={12} color="var(--text-dim)" />
                    <span>{fmt(cu.disk_percent, 1)}% used · {fmt(cu.disk_free_gb, 1)} GB free</span>
                  </div>
                )}
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
            const catToolNames = getCatTools(cat, health.tools_status)
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
