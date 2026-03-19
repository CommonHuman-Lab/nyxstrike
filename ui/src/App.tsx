import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Activity, Cpu, HardDrive, MemoryStick, Shield, Server,
  CheckCircle, XCircle, AlertCircle, RefreshCw, Lock, Eye, EyeOff,
  ChevronDown, ChevronRight, Clock, Database, Zap, Wifi
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import {
  api, setToken, clearToken, hasToken,
  type HealthResponse, type ResourceUsageResponse, type Tool
} from './api'
import './App.css'

// ─── helpers ────────────────────────────────────────────────────────────────

function fmt(n: number, dec = 1) { return n.toFixed(dec) }

function uptimeStr(secs: number) {
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.floor(secs % 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

// ─── Token Gate ─────────────────────────────────────────────────────────────

function TokenGate({ onUnlocked }: { onUnlocked: () => void }) {
  const [val, setVal] = useState('')
  const [show, setShow] = useState(false)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function tryToken() {
    setLoading(true)
    setErr('')
    setToken(val.trim())
    try {
      await api.health()
      onUnlocked()
    } catch (e: unknown) {
      clearToken()
      setErr(e instanceof Error && e.message === 'UNAUTHORIZED'
        ? 'Invalid token'
        : 'Could not reach server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="token-gate">
      <div className="token-card">
        <Lock size={32} color="var(--green)" />
        <h2>Authentication Required</h2>
        <p>Enter your <code>HEXSTRIKE_API_TOKEN</code> to continue</p>
        <div className="token-input-row">
          <input
            type={show ? 'text' : 'password'}
            placeholder="Bearer token…"
            value={val}
            onChange={e => setVal(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && tryToken()}
            className="mono"
            autoFocus
          />
          <button className="icon-btn" onClick={() => setShow(s => !s)} title="Toggle visibility">
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        {err && <p className="token-err">{err}</p>}
        <button className="btn-primary" onClick={tryToken} disabled={loading || !val.trim()}>
          {loading ? 'Checking…' : 'Connect'}
        </button>
      </div>
    </div>
  )
}

// ─── Stat Card ───────────────────────────────────────────────────────────────

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  accent?: string
}

function StatCard({ icon, label, value, sub, accent }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ color: accent || 'var(--green)' }}>{icon}</div>
      <div className="stat-body">
        <div className="stat-label">{label}</div>
        <div className="stat-value" style={{ color: accent || 'var(--text-h)' }}>{value}</div>
        {sub && <div className="stat-sub">{sub}</div>}
      </div>
    </div>
  )
}

// ─── Gauge Bar ───────────────────────────────────────────────────────────────

function GaugeBar({ label, value, max = 100, unit = '%', color }: {
  label: string, value: number, max?: number, unit?: string, color?: string
}) {
  const pct = Math.min(100, (value / max) * 100)
  const col = color || (pct > 80 ? 'var(--red)' : pct > 60 ? 'var(--amber)' : 'var(--green)')
  return (
    <div className="gauge-row">
      <div className="gauge-label">{label}</div>
      <div className="gauge-bar-wrap">
        <div className="gauge-bar-bg">
          <div className="gauge-bar-fill" style={{ width: `${pct}%`, background: col }} />
        </div>
      </div>
      <div className="gauge-val" style={{ color: col }}>{fmt(value)}{unit}</div>
    </div>
  )
}

// ─── Mini Area Chart ─────────────────────────────────────────────────────────

interface HistoryPoint { t: number; cpu: number; mem: number }

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

// ─── Tool Availability Section ───────────────────────────────────────────────

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  essential: <Shield size={14} />,
  network: <Wifi size={14} />,
  web_security: <Activity size={14} />,
  vuln_scanning: <AlertCircle size={14} />,
  password: <Lock size={14} />,
  binary: <Cpu size={14} />,
  forensics: <Database size={14} />,
  cloud: <Server size={14} />,
  osint: <Eye size={14} />,
  exploitation: <Zap size={14} />,
  api: <Activity size={14} />,
  wireless: <Wifi size={14} />,
  additional: <Server size={14} />,
}

function ToolCategoryRow({ category, stats, toolStatuses }: {
  category: string
  stats: { total: number; available: number }
  toolStatuses: Record<string, boolean>
}) {
  const [open, setOpen] = useState(false)
  const pct = stats.total > 0 ? (stats.available / stats.total) * 100 : 0
  const color = pct === 100 ? 'var(--green)' : pct > 50 ? 'var(--amber)' : 'var(--red)'

  const toolsInCat = Object.entries(toolStatuses)
  // we show all tools from toolStatuses that appear to belong to this category group
  // (filtered by the health response category_stats)

  return (
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
          {toolsInCat.map(([name, avail]) => (
            <div key={name} className={`tool-chip ${avail ? 'available' : 'missing'}`}>
              {avail
                ? <CheckCircle size={10} color="var(--green)" />
                : <XCircle size={10} color="var(--red)" />}
              <span className="mono">{name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Tool Registry Section ────────────────────────────────────────────────────

function ToolRegistrySection({ tools }: { tools: Tool[] }) {
  const [search, setSearch] = useState('')
  const [activeCat, setActiveCat] = useState<string>('all')

  const cats = ['all', ...Array.from(new Set(tools.map(t => t.category))).sort()]
  const filtered = tools.filter(t => {
    const matchCat = activeCat === 'all' || t.category === activeCat
    const q = search.toLowerCase()
    const matchSearch = !q || t.name.includes(q) || t.desc.toLowerCase().includes(q)
    return matchCat && matchSearch
  })

  return (
    <section className="section">
      <div className="section-header">
        <h3>Tool Registry <span className="badge">{tools.length}</span></h3>
      </div>
      <div className="registry-controls">
        <input
          className="search-input mono"
          placeholder="Search tools…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="cat-tabs">
          {cats.map(c => (
            <button
              key={c}
              className={`cat-tab ${activeCat === c ? 'active' : ''}`}
              onClick={() => setActiveCat(c)}
            >
              {c.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="registry-grid">
        {filtered.map(t => (
          <div key={t.name} className="registry-card">
            <div className="registry-card-top">
              <span className="registry-name mono">{t.name}</span>
              <span className="registry-cat">{t.category.replace(/_/g, ' ')}</span>
            </div>
            <p className="registry-desc">{t.desc}</p>
            <div className="registry-footer">
              <span className="registry-endpoint mono">{t.method} {t.endpoint}</span>
              <span className="registry-eff" title="Effectiveness">
                {'█'.repeat(Math.round(t.effectiveness * 5))}{'░'.repeat(5 - Math.round(t.effectiveness * 5))}
              </span>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <p className="empty-state">No tools match your filter.</p>}
      </div>
    </section>
  )
}

// ─── Main Dashboard ──────────────────────────────────────────────────────────

const POLL_MS = 10_000

export default function App() {
  const [authed, setAuthed] = useState(hasToken())
  const [needsAuth, setNeedsAuth] = useState(false)

  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [resources, setResources] = useState<ResourceUsageResponse | null>(null)
  const [tools, setTools] = useState<Tool[]>([])
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [h, r] = await Promise.all([api.health(), api.resources()])
      setHealth(h)
      setResources(r)
      setHistory(prev => {
        const next = [
          ...prev.slice(-29),
          { t: Date.now(), cpu: r.current_usage.cpu_percent, mem: r.current_usage.memory_percent },
        ]
        return next
      })
      setLastRefresh(new Date())
      setError(null)
    } catch (e: unknown) {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        setNeedsAuth(true)
        setAuthed(false)
      } else {
        setError('Server unreachable')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchTools = useCallback(async () => {
    try {
      const t = await api.tools()
      setTools(t.tools)
    } catch { /* non-critical */ }
  }, [])

  useEffect(() => {
    if (!authed) return
    setLoading(true)
    fetchAll()
    fetchTools()
    timerRef.current = setInterval(fetchAll, POLL_MS)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [authed, fetchAll, fetchTools])

  // Try without token first
  useEffect(() => {
    if (hasToken()) return
    api.health().then(h => {
      setHealth(h)
      setAuthed(true)
      setLoading(false)
    }).catch(e => {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        setNeedsAuth(true)
      } else {
        setAuthed(true) // server reachable, no auth needed but maybe offline
      }
      setLoading(false)
    })
  }, [])

  if (needsAuth && !authed) {
    return <TokenGate onUnlocked={() => { setAuthed(true); setNeedsAuth(false) }} />
  }

  const cu = resources?.current_usage

  return (
    <div className="layout">
      {/* ── Top Bar ── */}
      <header className="topbar">
        <div className="topbar-brand">
          <Shield size={18} color="var(--green)" />
          <span className="brand-text">HexStrike AI</span>
          <span className="brand-version mono">{health?.version ?? '…'}</span>
        </div>
        <div className="topbar-right">
          {lastRefresh && (
            <span className="topbar-meta">
              <Clock size={12} /> {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <div className={`status-dot ${health?.status === 'healthy' ? 'online' : error ? 'error' : 'loading'}`} />
          <span className="status-label">{health?.status ?? (loading ? 'connecting…' : error ?? 'unknown')}</span>
          <button className="icon-btn" onClick={fetchAll} title="Refresh now">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
          </button>
          {hasToken() && (
            <button className="icon-btn" onClick={() => { clearToken(); setAuthed(false); setNeedsAuth(true) }} title="Sign out">
              <Lock size={14} />
            </button>
          )}
        </div>
      </header>

      <main className="main">
        {loading && !health && (
          <div className="loading-state">
            <RefreshCw size={24} className="spin" color="var(--green)" />
            <p>Connecting to server…</p>
          </div>
        )}

        {error && !health && (
          <div className="error-banner">
            <XCircle size={16} /> {error} — is the server running on port 8888?
          </div>
        )}

        {health && (
          <>
            {/* ── KPI Row ── */}
            <div className="kpi-row">
              <StatCard
                icon={<Activity size={20} />}
                label="Server Status"
                value={health.status}
                sub={`uptime ${uptimeStr(health.uptime)}`}
                accent={health.status === 'healthy' ? 'var(--green)' : 'var(--red)'}
              />
              <StatCard
                icon={<Shield size={20} />}
                label="Tools Available"
                value={`${health.total_tools_available} / ${health.total_tools_count}`}
                sub={health.all_essential_tools_available ? 'all essential ready' : 'some essential missing'}
                accent={health.all_essential_tools_available ? 'var(--green)' : 'var(--amber)'}
              />
              <StatCard
                icon={<Database size={20} />}
                label="Cache"
                value={`${health.cache_stats?.hits ?? 0} hits`}
                sub={`${health.cache_stats?.size ?? 0} entries · ${health.cache_stats?.misses ?? 0} misses`}
                accent="var(--blue)"
              />
              <StatCard
                icon={<Zap size={20} />}
                label="Requests"
                value={health.telemetry?.total_requests ?? 0}
                sub={`${health.telemetry?.successful_requests ?? 0} ok · ${health.telemetry?.failed_requests ?? 0} failed`}
                accent="var(--purple)"
              />
            </div>

            {/* ── Resource Row ── */}
            {cu && (
              <section className="section">
                <div className="section-header">
                  <h3>System Resources</h3>
                  <span className="section-meta mono">{resources?.timestamp?.slice(11, 19)}</span>
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
                        <span>{fmt(cu.memory_used_mb / 1024, 2)} GB / {fmt(cu.memory_total_mb / 1024, 2)} GB</span>
                      </div>
                      {cu.disk_used_gb !== undefined && (
                        <div className="resource-detail">
                          <HardDrive size={12} color="var(--text-dim)" />
                          <span>{fmt(cu.disk_used_gb)} GB / {fmt(cu.disk_total_gb)} GB</span>
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
                  age: {health.tool_availability_age_seconds}s
                </span>
              </div>
              <div className="cat-list">
                {Object.entries(health.category_stats).map(([cat, stats]) => {
                  // Gather the individual tool statuses for this category group
                  // from health.tools_status — we filter by what the health endpoint knows
                  // (category_stats keys match _HEALTH_TOOL_CATEGORIES keys)
                  // For the expanded view we pass all known tool statuses; the component shows them.
                  // We need to pick only tools that the server groups in this category.
                  // Since we don't have per-category tool lists here, we pass the full map and
                  // let the user see all status in the group via a placeholder.
                  // Instead: pass only a slice proportional to the category.
                  const catToolNames = getCatTools(cat, health.tools_status)
                  const catStatuses = Object.fromEntries(
                    catToolNames.map(n => [n, health.tools_status[n] ?? false])
                  )
                  return (
                    <ToolCategoryRow
                      key={cat}
                      category={cat}
                      stats={stats}
                      toolStatuses={catStatuses}
                    />
                  )
                })}
              </div>
            </section>

            {/* ── Tool Registry ── */}
            {tools.length > 0 && <ToolRegistrySection tools={tools} />}
          </>
        )}
      </main>
    </div>
  )
}

// Map health category names to their tool lists (mirrors _HEALTH_TOOL_CATEGORIES in Python)
const HEALTH_CAT_TOOLS: Record<string, string[]> = {
  essential: ['nmap', 'gobuster', 'dirb', 'nikto', 'sqlmap', 'hydra', 'john', 'hashcat'],
  network: ['rustscan', 'masscan', 'autorecon', 'nbtscan', 'arp-scan', 'responder',
    'nxc', 'enum4linux-ng', 'rpcclient', 'enum4linux'],
  web_security: ['ffuf', 'feroxbuster', 'dirsearch', 'dotdotpwn', 'xsser', 'wfuzz',
    'gau', 'waybackurls', 'arjun', 'paramspider', 'x8', 'jaeles', 'dalfox',
    'httpx', 'wafw00f', 'burpsuite', 'zaproxy', 'katana', 'hakrawler'],
  vuln_scanning: ['nuclei', 'wpscan', 'graphql-scanner', 'jwt-analyzer'],
  password: ['medusa', 'patator', 'hashid', 'ophcrack', 'hashcat-utils'],
  binary: ['gdb', 'radare2', 'binwalk', 'ropgadget', 'checksec', 'objdump',
    'ghidra', 'pwntools', 'one-gadget', 'ropper', 'angr', 'libc-database', 'pwninit'],
  forensics: ['vol', 'steghide', 'hashpump', 'foremost', 'exiftool',
    'strings', 'xxd', 'file', 'photorec', 'testdisk', 'scalpel',
    'bulk-extractor', 'stegsolve', 'zsteg', 'outguess'],
  cloud: ['prowler', 'scout-suite', 'trivy', 'kube-hunter', 'kube-bench',
    'docker-bench-security', 'checkov', 'terrascan', 'falco', 'clair'],
  osint: ['amass', 'subfinder', 'fierce', 'dnsenum', 'theharvester', 'sherlock',
    'social-analyzer', 'recon-ng', 'maltego', 'spiderfoot', 'shodan-cli',
    'censys-cli', 'have-i-been-pwned', 'whois', 'bbot'],
  exploitation: ['msfconsole', 'msfvenom', 'searchsploit'],
  api: ['api-schema-analyzer', 'postman', 'insomnia', 'curl', 'httpie', 'anew', 'qsreplace', 'uro'],
  wireless: ['kismet', 'wireshark', 'tshark', 'tcpdump'],
  additional: ['smbmap', 'volatility', 'sleuthkit', 'autopsy', 'evil-winrm',
    'airmon-ng', 'airodump-ng', 'aireplay-ng', 'aircrack-ng'],
}

function getCatTools(cat: string, allStatuses: Record<string, boolean>): string[] {
  const known = HEALTH_CAT_TOOLS[cat] ?? []
  if (known.length > 0) return known
  // fallback: return tools in allStatuses not claimed by any category
  return Object.keys(allStatuses)
}
