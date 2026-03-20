import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Activity, Cpu, HardDrive, MemoryStick, Shield, Server,
  CheckCircle, XCircle, AlertCircle, RefreshCw, Lock, Eye, EyeOff,
  ChevronDown, ChevronRight, Clock, Database, Zap, Wifi,
  Settings as SettingsIcon, HelpCircle, LayoutDashboard,
  Terminal, Copy, Check, Save,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import {
  api, setToken, clearToken, hasToken,
  type HealthResponse, type ResourceUsageResponse, type Tool,
  type Settings,
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

// ─── Code Block ──────────────────────────────────────────────────────────────

function CodeBlock({ code, language = '' }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-lang mono">{language || 'code'}</span>
        <button className="icon-btn code-copy" onClick={copy} title="Copy">
          {copied ? <Check size={13} color="var(--green)" /> : <Copy size={13} />}
        </button>
      </div>
      <pre className="code-pre mono">{code}</pre>
    </div>
  )
}

// ─── Help Page ────────────────────────────────────────────────────────────────

const IDE_CONFIGS = [
  {
    id: 'claude',
    label: 'Claude Desktop',
    icon: '🤖',
    configPath: '~/.config/Claude/claude_desktop_config.json',
    note: 'Also works for Cursor — same config format.',
    json: (p: string) => JSON.stringify({
      mcpServers: {
        "hexstrike-ai": {
          command: `${p}/hexstrike-env/bin/python3`,
          args: [`${p}/hexstrike_mcp.py`, "--server", "http://localhost:8888", "--profile", "full"],
          description: "HexStrike AI Community Edition",
          timeout: 300,
          disabled: false,
        }
      }
    }, null, 2),
  },
  {
    id: 'vscode',
    label: 'VS Code Copilot',
    icon: '🔷',
    configPath: '.vscode/settings.json  (workspace) or User settings',
    note: 'Place in your workspace .vscode/settings.json or open User Settings JSON.',
    json: (p: string) => JSON.stringify({
      servers: {
        hexstrike: {
          type: "stdio",
          command: `${p}/hexstrike-env/bin/python3`,
          args: [`${p}/hexstrike_mcp.py`, "--server", "http://localhost:8888", "--profile", "full"],
        }
      },
      inputs: []
    }, null, 2),
  },
  {
    id: 'opencode',
    label: 'OpenCode',
    icon: '⚡',
    configPath: '~/.config/opencode/opencode.json',
    note: 'OpenCode reads this on startup.',
    json: (p: string) => JSON.stringify({
      $schema: "https://opencode.ai/config.json",
      mcp: {
        "hexstrike-ai": {
          type: "local",
          timeout: 300,
          command: [`${p}/hexstrike-env/bin/python3`, `${p}/hexstrike_mcp.py`, "--server", "http://localhost:8888", "--profile", "full"],
          enabled: true,
        }
      }
    }, null, 2),
  },
  {
    id: 'roo',
    label: 'Roo Code',
    icon: '🦘',
    configPath: 'MCP Servers panel  →  Edit Config',
    note: 'Open Roo Code → MCP Servers → Edit Config and paste the block below.',
    json: (p: string) => JSON.stringify({
      mcpServers: {
        "hexstrike-ai": {
          command: `${p}/hexstrike-env/bin/python3`,
          args: [`${p}/hexstrike_mcp.py`, "--server", "http://localhost:8888", "--profile", "full"],
          timeout: 300,
        }
      }
    }, null, 2),
  },
]

function HelpPage() {
  const [activeIde, setActiveIde] = useState('claude')
  const [installPath, setInstallPath] = useState('/path/to/hexstrike-ai-community-edition')
  const ide = IDE_CONFIGS.find(i => i.id === activeIde)!

  return (
    <div className="help-page">
      <section className="section">
        <div className="section-header"><h3>Quick Start</h3></div>
        <ol className="help-steps">
          <li>
            <strong>Start the HexStrike server</strong>
            <CodeBlock language="bash" code="python3 hexstrike_server.py" />
          </li>
          <li>
            <strong>Verify it is running</strong>
            <CodeBlock language="bash" code="curl http://localhost:8888/health" />
          </li>
          <li>
            <strong>Configure your IDE</strong> — choose below and paste the config into the correct file.
          </li>
          <li>
            <strong>Restart your IDE / reload the MCP server</strong> — the hexstrike-ai tools will appear.
          </li>
        </ol>
      </section>

      <section className="section">
        <div className="section-header"><h3>IDE / Agent Configuration</h3></div>

        <div className="help-path-row">
          <label className="help-path-label">Installation path</label>
          <input
            className="search-input mono help-path-input"
            value={installPath}
            onChange={e => setInstallPath(e.target.value)}
            placeholder="/path/to/hexstrike-ai-community-edition"
          />
        </div>

        <div className="ide-tabs">
          {IDE_CONFIGS.map(i => (
            <button
              key={i.id}
              className={`ide-tab ${activeIde === i.id ? 'active' : ''}`}
              onClick={() => setActiveIde(i.id)}
            >
              {i.icon} {i.label}
            </button>
          ))}
        </div>

        <div className="ide-panel">
          <div className="ide-config-path">
            <Terminal size={13} color="var(--text-dim)" />
            <span className="mono">{ide.configPath}</span>
          </div>
          {ide.note && <p className="ide-note">{ide.note}</p>}
          <CodeBlock language="json" code={ide.json(installPath)} />
        </div>
      </section>

      <section className="section">
        <div className="section-header"><h3>MCP Client Flags</h3></div>
        <div className="flags-table">
          {[
            ['--server URL', 'HexStrike server URL', 'http://127.0.0.1:8888'],
            ['--profile PROFILE', 'Tool profile(s) to load', 'full  |  web_recon  |  exploit_framework  |  …'],
            ['--compact', 'Load only classify_task + run_tool — ideal for small/local LLMs', '—'],
            ['--auth-token TOKEN', 'Bearer token if HEXSTRIKE_API_TOKEN is set on the server', '—'],
            ['--timeout SECS', 'Request timeout in seconds', '300'],
            ['--debug', 'Enable verbose debug logging', '—'],
            ['--disable-ssl-verify', 'Skip SSL verification (reverse proxy setups)', '—'],
          ].map(([flag, desc, def]) => (
            <div key={flag} className="flag-row">
              <code className="flag-name mono">{flag}</code>
              <span className="flag-desc">{desc}</span>
              {def !== '—' && <code className="flag-default mono">{def}</code>}
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-header"><h3>Authentication</h3></div>
        <p className="help-body">
          If you set <code>HEXSTRIKE_API_TOKEN</code> on the server, every request must carry a Bearer token.
          Pass it to the MCP client with <code>--auth-token</code>, or set it in the IDE config under <code>args</code>.
          The dashboard will prompt for it automatically when the server returns 401.
        </p>
        <CodeBlock language="bash" code={`# Server side\nexport HEXSTRIKE_API_TOKEN=your-secret-token\npython3 hexstrike_server.py\n\n# MCP client side\nhexstrike-env/bin/python3 hexstrike_mcp.py \\\n  --server http://localhost:8888 \\\n  --auth-token your-secret-token \\\n  --profile full`} />
      </section>

      <section className="section">
        <div className="section-header"><h3>Prompt Tips</h3></div>
        <p className="help-body">
          Most LLMs have ethics guardrails. Always establish context before asking for a pentest:
        </p>
        <CodeBlock language="prompt" code={`"I'm a security researcher. My company owns example.com and I have written authorisation to conduct a penetration test. Please use the hexstrike-ai MCP tools to run a full web application assessment."`} />
      </section>
    </div>
  )
}

// ─── Settings Page ────────────────────────────────────────────────────────────

function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  // Editable runtime fields
  const [timeout, setTimeout_] = useState('')
  const [cacheSize, setCacheSize] = useState('')
  const [cacheTtl, setCacheTtl] = useState('')
  const [toolTtl, setToolTtl] = useState('')

  useEffect(() => {
    api.getSettings().then(r => {
      setSettings(r.settings)
      setTimeout_(String(r.settings.runtime.command_timeout))
      setCacheSize(String(r.settings.runtime.cache_size))
      setCacheTtl(String(r.settings.runtime.cache_ttl))
      setToolTtl(String(r.settings.runtime.tool_availability_ttl))
      setLoading(false)
    }).catch(e => {
      setError(String(e))
      setLoading(false)
    })
  }, [])

  async function save() {
    setSaving(true)
    setSaveMsg(null)
    try {
      const res = await api.patchSettings({
        command_timeout: Number(timeout),
        cache_size: Number(cacheSize),
        cache_ttl: Number(cacheTtl),
        tool_availability_ttl: Number(toolTtl),
      })
      if (res.success && res.settings) {
        setSettings(res.settings)
        setSaveMsg('Saved')
      } else {
        setSaveMsg('Error: ' + JSON.stringify(res.errors || res.error))
      }
    } catch (e) {
      setSaveMsg('Error: ' + String(e))
    } finally {
      setSaving(false)
      setTimeout(() => setSaveMsg(null), 3000)
    }
  }

  if (loading) return <div className="loading-state"><RefreshCw size={20} className="spin" color="var(--green)" /><p>Loading settings…</p></div>
  if (error) return <div className="error-banner"><XCircle size={16} /> {error}</div>
  if (!settings) return null

  return (
    <div className="settings-page">
      {/* ── Server Environment ── */}
      <section className="section">
        <div className="section-header"><h3>Server Environment <span className="badge">read-only</span></h3></div>
        <div className="settings-grid">
          <SettingsRow label="Host" value={settings.server.host} mono />
          <SettingsRow label="Port" value={String(settings.server.port)} mono />
          <SettingsRow label="Auth Enabled" value={settings.server.auth_enabled ? 'Yes (HEXSTRIKE_API_TOKEN set)' : 'No'} accent={settings.server.auth_enabled ? 'var(--green)' : 'var(--amber)'} />
          <SettingsRow label="Debug Mode" value={settings.server.debug_mode ? 'On' : 'Off'} accent={settings.server.debug_mode ? 'var(--amber)' : 'var(--text-dim)'} />
          <SettingsRow label="Data Directory" value={settings.server.data_dir} mono />
        </div>
        <p className="settings-hint">
          Change these by setting environment variables before starting the server:
          <code> HEXSTRIKE_HOST</code>, <code>HEXSTRIKE_PORT</code>, <code>HEXSTRIKE_API_TOKEN</code>,
          <code> DEBUG_MODE</code>, <code>HEXSTRIKE_DATA_DIR</code>.
        </p>
      </section>

      {/* ── Runtime Config ── */}
      <section className="section">
        <div className="section-header">
          <h3>Runtime Config</h3>
          <span className="section-meta">changes apply immediately, reset on server restart</span>
        </div>
        <div className="settings-grid">
          <SettingsField
            label="Command Timeout" unit="seconds"
            hint="Max time a tool process is allowed to run."
            value={timeout} onChange={setTimeout_}
          />
          <SettingsField
            label="Cache Size" unit="entries"
            hint="Maximum number of cached tool results."
            value={cacheSize} onChange={setCacheSize}
          />
          <SettingsField
            label="Cache TTL" unit="seconds"
            hint="How long a cache entry lives before expiry."
            value={cacheTtl} onChange={setCacheTtl}
          />
          <SettingsField
            label="Tool Availability TTL" unit="seconds"
            hint="How long the tool availability check is cached."
            value={toolTtl} onChange={setToolTtl}
          />
        </div>
        <div className="settings-actions">
          <button className="btn-primary" onClick={save} disabled={saving}>
            <Save size={14} /> {saving ? 'Saving…' : 'Save Changes'}
          </button>
          {saveMsg && (
            <span className={`save-msg ${saveMsg.startsWith('Error') ? 'err' : 'ok'}`}>{saveMsg}</span>
          )}
        </div>
      </section>

      {/* ── Wordlists ── */}
      <section className="section">
        <div className="section-header"><h3>Wordlists <span className="badge">{settings.wordlists.length}</span></h3></div>
        <div className="wordlist-table">
          <div className="wordlist-head">
            <span>Name</span><span>Type</span><span>Speed</span><span>Coverage</span><span>Path</span>
          </div>
          {settings.wordlists.map(w => (
            <div key={w.name} className="wordlist-row">
              <span className="mono">{w.name}</span>
              <span className="badge-small">{w.type}</span>
              <span>{w.speed}</span>
              <span>{w.coverage}</span>
              <span className="mono wl-path">{w.path}</span>
            </div>
          ))}
        </div>
        <p className="settings-hint">Edit wordlists via <code>GET/POST /api/wordlists</code> or modify <code>config.py</code> and restart.</p>
      </section>
    </div>
  )
}

function SettingsRow({ label, value, mono, accent }: { label: string; value: string; mono?: boolean; accent?: string }) {
  return (
    <div className="settings-row">
      <span className="settings-label">{label}</span>
      <span className={`settings-value ${mono ? 'mono' : ''}`} style={accent ? { color: accent } : {}}>{value}</span>
    </div>
  )
}

function SettingsField({ label, unit, hint, value, onChange }: {
  label: string; unit: string; hint: string; value: string; onChange: (v: string) => void
}) {
  return (
    <div className="settings-field">
      <label className="settings-label">{label}</label>
      <div className="settings-input-row">
        <input
          className="settings-input mono"
          type="number"
          min={1}
          value={value}
          onChange={e => onChange(e.target.value)}
        />
        <span className="settings-unit">{unit}</span>
      </div>
      <span className="settings-hint-inline">{hint}</span>
    </div>
  )
}

// ─── Main Dashboard ──────────────────────────────────────────────────────────

const POLL_MS = 10_000
type Page = 'dashboard' | 'settings' | 'help'

export default function App() {
  const [authed, setAuthed] = useState(hasToken())
  const [needsAuth, setNeedsAuth] = useState(false)
  const [page, setPage] = useState<Page>('dashboard')

  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [resources, setResources] = useState<ResourceUsageResponse | null>(null)
  const [tools, setTools] = useState<Tool[]>([])
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashCacheSize, setDashCacheSize] = useState<number | null>(null)
  const [dashCacheTtl, setDashCacheTtl] = useState<number | null>(null)

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

  const fetchDashSettings = useCallback(async () => {
    try {
      const r = await api.getSettings()
      setDashCacheSize(r.settings.runtime.cache_size)
      setDashCacheTtl(r.settings.runtime.cache_ttl)
    } catch { /* non-critical */ }
  }, [])

  useEffect(() => {
    if (!authed) return
    setLoading(true)
    fetchAll()
    fetchTools()
    fetchDashSettings()
    timerRef.current = setInterval(fetchAll, POLL_MS)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [authed, fetchAll, fetchTools, fetchDashSettings])

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
        setAuthed(true)
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

        {/* ── Nav Tabs ── */}
        <nav className="topbar-nav">
          <button className={`nav-tab ${page === 'dashboard' ? 'active' : ''}`} onClick={() => setPage('dashboard')}>
            <LayoutDashboard size={13} /> Dashboard
          </button>
          <button className={`nav-tab ${page === 'settings' ? 'active' : ''}`} onClick={() => setPage('settings')}>
            <SettingsIcon size={13} /> Settings
          </button>
          <button className={`nav-tab ${page === 'help' ? 'active' : ''}`} onClick={() => setPage('help')}>
            <HelpCircle size={13} /> Help
          </button>
        </nav>

        <div className="topbar-right">
          {lastRefresh && (
            <span className="topbar-meta">
              <Clock size={12} /> {lastRefresh.toLocaleTimeString('en-GB')}
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
        {/* ── Settings Page ── */}
        {page === 'settings' && <SettingsPage />}

        {/* ── Help Page ── */}
        {page === 'help' && <HelpPage />}

        {/* ── Dashboard Page ── */}
        {page === 'dashboard' && (
          <>
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
                    label="Tools Installed"
                    value={`${health.total_tools_available} / ${health.total_tools_count}`}
                    sub={health.all_essential_tools_available ? 'all essential ready' : 'some essential missing'}
                    accent={health.all_essential_tools_available ? 'var(--green)' : 'var(--amber)'}
                  />
                  <StatCard
                    icon={<Database size={20} />}
                    label="Cache"
                    value={dashCacheSize !== null ? `${dashCacheSize} entries` : '—'}
                    sub={dashCacheTtl !== null ? `${dashCacheTtl}s TTL` : 'cache config'}
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
    'docker-bench-security', 'checkov', 'terrascan', 'falco', 'clair',
    'cloudmapper', 'pacu'],
  osint: ['amass', 'subfinder', 'fierce', 'dnsenum', 'theharvester', 'sherlock',
    'social-analyzer', 'recon-ng', 'maltego', 'spiderfoot', 'shodan-cli',
    'censys-cli', 'have-i-been-pwned', 'whois', 'bbot'],
  exploitation: ['msfconsole', 'msfvenom', 'searchsploit'],
  api: ['api-schema-analyzer', 'postman', 'insomnia', 'curl', 'httpie', 'anew', 'qsreplace', 'uro'],
  wireless: ['kismet', 'wireshark', 'tshark', 'tcpdump',
    'airbase-ng', 'airdecap-ng', 'hcxdumptool', 'hcxpcapngtool',
    'mdk4', 'eaphammer', 'wifite', 'bettercap'],
  additional: ['smbmap', 'volatility', 'sleuthkit', 'autopsy', 'evil-winrm',
    'airmon-ng', 'airodump-ng', 'aireplay-ng', 'aircrack-ng'],
  database: ['mysql', 'sqlite3'],
}

function getCatTools(cat: string, allStatuses: Record<string, boolean>): string[] {
  const known = HEALTH_CAT_TOOLS[cat] ?? []
  if (known.length > 0) return known
  return Object.keys(allStatuses)
}
