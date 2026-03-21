import React, { useState, useEffect, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import faviconUrl from './favicon-16x16.png'
import {
  Activity, Cpu, HardDrive, MemoryStick, Shield, Server,
  CheckCircle, XCircle, AlertCircle, RefreshCw, Lock, Eye, EyeOff,
  ChevronDown, ChevronRight, Clock, Database, Zap, Wifi,
  Settings as SettingsIcon, HelpCircle, LayoutDashboard,
  Terminal, Copy, Check, Save, Play, ChevronUp, Download,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import {
  api, setToken, clearToken, hasToken,
  type WebDashboardResponse, type Tool,
  type Settings, type ToolExecResponse,
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
      await api.dashboard()
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

  const toolsInCat = Object.entries(toolStatuses)

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

// ─── Tool Install Hints ───────────────────────────────────────────────────────

const INSTALL_HINTS: Record<string, string> = {
  nmap:              'sudo apt install nmap',
  masscan:           'sudo apt install masscan',
  rustscan:          'cargo install rustscan  # or: sudo apt install rustscan',
  autorecon:         'pip3 install autorecon',
  gobuster:          'sudo apt install gobuster',
  ffuf:              'sudo apt install ffuf',
  feroxbuster:       'sudo apt install feroxbuster',
  dirb:              'sudo apt install dirb',
  dirsearch:         'pip3 install dirsearch',
  nikto:             'sudo apt install nikto',
  nuclei:            'go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest',
  sqlmap:            'sudo apt install sqlmap',
  wpscan:            'sudo apt install wpscan  # or: gem install wpscan',
  hydra:             'sudo apt install hydra',
  john:              'sudo apt install john',
  hashcat:           'sudo apt install hashcat',
  medusa:            'sudo apt install medusa',
  patator:           'sudo apt install patator',
  hashid:            'pip3 install hashid',
  ophcrack:          'sudo apt install ophcrack',
  amass:             'sudo apt install amass',
  subfinder:         'go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest',
  fierce:            'pip3 install fierce',
  dnsenum:           'sudo apt install dnsenum',
  theharvester:      'sudo apt install theharvester',
  sherlock:          'pip3 install sherlock-project',
  whois:             'sudo apt install whois',
  httpx:             'go install github.com/projectdiscovery/httpx/cmd/httpx@latest',
  katana:            'go install github.com/projectdiscovery/katana/cmd/katana@latest',
  hakrawler:         'go install github.com/hakluke/hakrawler@latest',
  gau:               'go install github.com/lc/gau/v2/cmd/gau@latest',
  waybackurls:       'go install github.com/tomnomnom/waybackurls@latest',
  wafw00f:           'pip3 install wafw00f',
  dalfox:            'go install github.com/hahwul/dalfox/v2@latest',
  jaeles:            'go install github.com/jaeles-project/jaeles@latest',
  arjun:             'pip3 install arjun',
  paramspider:       'pip3 install paramspider',
  x8:                'cargo install x8',
  gdb:               'sudo apt install gdb',
  radare2:           'sudo apt install radare2',
  binwalk:           'sudo apt install binwalk',
  ropgadget:         'pip3 install ropgadget',
  checksec:          'sudo apt install checksec  # or: pip3 install checksec',
  objdump:           'sudo apt install binutils',
  ghidra:            'sudo apt install ghidra  # or download from ghidra.re',
  pwntools:          'pip3 install pwntools',
  ropper:            'pip3 install ropper',
  angr:              'pip3 install angr',
  pwninit:           'cargo install pwninit',
  'one-gadget':      'gem install one_gadget',
  'libc-database':   'git clone https://github.com/niklasb/libc-database',
  vol:               'pip3 install volatility3',
  volatility:        'pip3 install volatility3',
  steghide:          'sudo apt install steghide',
  foremost:          'sudo apt install foremost',
  exiftool:          'sudo apt install libimage-exiftool-perl',
  strings:           'sudo apt install binutils',
  xxd:               'sudo apt install xxd',
  photorec:          'sudo apt install testdisk',
  testdisk:          'sudo apt install testdisk',
  scalpel:           'sudo apt install scalpel',
  zsteg:             'gem install zsteg',
  outguess:          'sudo apt install outguess',
  hashpump:          'sudo apt install hashpump  # or: git clone https://github.com/bwall/HashPump',
  prowler:           'pip3 install prowler',
  'scout-suite':     'pip3 install scoutsuite',
  trivy:             'sudo apt install trivy',
  'kube-hunter':     'pip3 install kube-hunter',
  'kube-bench':      'sudo apt install kube-bench',
  'docker-bench-security': 'git clone https://github.com/docker/docker-bench-security',
  checkov:           'pip3 install checkov',
  terrascan:         'brew install terrascan  # or download from github.com/tenable/terrascan',
  falco:             'sudo apt install falco',
  clair:             'docker pull quay.io/projectquay/clair',
  msfconsole:        'sudo apt install metasploit-framework',
  msfvenom:          'sudo apt install metasploit-framework',
  searchsploit:      'sudo apt install exploitdb',
  smbmap:            'pip3 install smbmap',
  enum4linux:        'sudo apt install enum4linux',
  'enum4linux-ng':   'pip3 install enum4linux-ng',
  nbtscan:           'sudo apt install nbtscan',
  rpcclient:         'sudo apt install samba-common-bin',
  responder:         'sudo apt install responder',
  nxc:               'pip3 install netexec',
  'evil-winrm':      'gem install evil-winrm',
  'airmon-ng':       'sudo apt install aircrack-ng',
  'aircrack-ng':     'sudo apt install aircrack-ng',
  'airodump-ng':     'sudo apt install aircrack-ng',
  'aireplay-ng':     'sudo apt install aircrack-ng',
  'airbase-ng':      'sudo apt install aircrack-ng',
  'airdecap-ng':     'sudo apt install aircrack-ng',
  kismet:            'sudo apt install kismet',
  wireshark:         'sudo apt install wireshark',
  tshark:            'sudo apt install tshark',
  tcpdump:           'sudo apt install tcpdump',
  wifite:            'sudo apt install wifite',
  bettercap:         'sudo apt install bettercap',
  mdk4:              'sudo apt install mdk4',
  bbot:              'pip3 install bbot',
  curl:              'sudo apt install curl',
  httpie:            'pip3 install httpie',
  anew:              'go install github.com/tomnomnom/anew@latest',
  qsreplace:         'go install github.com/tomnomnom/qsreplace@latest',
  uro:               'pip3 install uro',
  'graphql-scanner': 'npm install -g graphql-voyager',
  'jwt-analyzer':    'pip3 install jwt-tool',
  'api-schema-analyzer': 'npm install -g @stoplight/spectral-cli',
  wfuzz:             'pip3 install wfuzz',
  dotdotpwn:         'sudo apt install dotdotpwn',
  xsser:             'sudo apt install xsser',
  commix:            'sudo apt install commix',
  tplmap:            'git clone https://github.com/epinna/tplmap',
  nosqlmap:          'git clone https://github.com/codingo/NoSQLMap',
  whatweb:           'sudo apt install whatweb',
  testssl:           'sudo apt install testssl.sh',
  sslscan:           'sudo apt install sslscan',
  sslyze:            'pip3 install sslyze',
  'recon-ng':        'sudo apt install recon-ng',
  maltego:           'Download from maltego.com',
  spiderfoot:        'pip3 install spiderfoot',
  'social-analyzer': 'pip3 install social-analyzer',
  sleuthkit:         'sudo apt install sleuthkit',
  autopsy:           'sudo apt install autopsy',
  'bulk-extractor':  'sudo apt install bulk-extractor',
  'hashcat-utils':   'sudo apt install hashcat-utils',
}

function installHint(name: string): string {
  return INSTALL_HINTS[name] ?? `sudo apt install ${name}  # check project docs for exact install`
}

// ─── Export helper ────────────────────────────────────────────────────────────

function exportEntry(entry: RunHistoryEntry, format: 'txt' | 'json') {
  const r = entry.result
  const ts = entry.ts.toISOString().replace(/[:.]/g, '-')
  const filename = `${entry.tool}_${ts}.${format}`

  let content: string
  if (format === 'json') {
    content = JSON.stringify({
      tool: entry.tool,
      timestamp: entry.ts.toISOString(),
      params: entry.params,
      success: r.success,
      return_code: r.return_code,
      execution_time: r.execution_time,
      timed_out: r.timed_out,
      partial_results: r.partial_results,
      stdout: r.stdout,
      stderr: r.stderr,
    }, null, 2)
  } else {
    const paramStr = Object.entries(entry.params).map(([k, v]) => `  ${k}=${v}`).join('\n')
    content = [
      `Tool:       ${entry.tool}`,
      `Timestamp:  ${entry.ts.toISOString()}`,
      `Success:    ${r.success}`,
      `Exit code:  ${r.return_code}`,
      `Time:       ${r.execution_time.toFixed(2)}s`,
      r.timed_out ? `Timed out:  yes` : '',
      r.partial_results ? `Partial:    yes` : '',
      paramStr ? `\nParams:\n${paramStr}` : '',
      `\n--- stdout ---\n${r.stdout || '(empty)'}`,
      r.stderr ? `\n--- stderr ---\n${r.stderr}` : '',
    ].filter(Boolean).join('\n')
  }

  const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// ─── Run Result Modal ─────────────────────────────────────────────────────────

function RunResultModal({ entry, onClose }: { entry: RunHistoryEntry; onClose: () => void }) {
  const r = entry.result

  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal run-result-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-name mono">{entry.tool}</span>
            <span className={`run-output-status ${r.success ? 'ok' : 'fail'}`} style={{ fontSize: 12 }}>
              {r.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
              {r.success ? 'success' : 'failed'}
            </span>
          </div>
          <button className="modal-close" onClick={onClose}><XCircle size={18} /></button>
        </div>

        <div className="run-result-modal-meta">
          <span className="run-output-meta mono">exit {r.return_code}</span>
          <span className="run-output-meta mono">{r.execution_time.toFixed(2)}s</span>
          <span className="run-output-meta mono">{entry.ts.toLocaleTimeString('en-GB')}</span>
          {r.timed_out && <span className="run-output-meta amber">timed out</span>}
          {r.partial_results && <span className="run-output-meta amber">partial results</span>}
          <div className="run-export-btns">
            <button className="run-export-btn" onClick={() => exportEntry(entry, 'txt')} title="Export as .txt">
              <Download size={11} /> TXT
            </button>
            <button className="run-export-btn" onClick={() => exportEntry(entry, 'json')} title="Export as .json">
              <Download size={11} /> JSON
            </button>
          </div>
        </div>

        {Object.keys(entry.params).length > 0 && (
          <div className="run-result-modal-params">
            {Object.entries(entry.params).map(([k, v]) => (
              <span key={k} className="run-result-param mono">{k}=<em>{String(v)}</em></span>
            ))}
          </div>
        )}

        <pre className="run-result-modal-output mono">
          {r.stdout || r.stderr || '(no output)'}
        </pre>
      </div>
    </div>,
    document.body
  )
}

// ─── Run Page ─────────────────────────────────────────────────────────────────

interface RunHistoryEntry {
  id: number
  tool: string
  params: Record<string, unknown>
  result: ToolExecResponse
  ts: Date
}

function ParamField({
  name, value, onChange, required,
}: {
  name: string
  value: string
  onChange: (v: string) => void
  required?: boolean
}) {
  return (
    <div className="run-field">
      <label className="run-field-label mono">
        {name}
        {required && <span className="run-required">*</span>}
      </label>
      <input
        className="run-field-input mono"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={required ? 'required' : 'optional'}
      />
    </div>
  )
}

function RunPage({ tools, toolsStatus, runHistory: history, setRunHistory: setHistory }: {
  tools: Tool[]
  toolsStatus: Record<string, boolean>
  runHistory: RunHistoryEntry[]
  setRunHistory: React.Dispatch<React.SetStateAction<RunHistoryEntry[]>>
}) {
  const [search, setSearch] = useState('')
  const [activeCat, setActiveCat] = useState('all')
  const [selected, setSelected] = useState<Tool | null>(null)
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [showOptional, setShowOptional] = useState(false)
  const [running, setRunning] = useState(false)
  const [viewEntry, setViewEntry] = useState<RunHistoryEntry | null>(null)
  const [modalEntry, setModalEntry] = useState<RunHistoryEntry | null>(null)
  const [histSearch, setHistSearch] = useState('')
  const [runError, setRunError] = useState<string | null>(null)
  const runIdRef = useRef(0)

  const cats = ['all', ...Array.from(new Set(tools.map(t => t.category))).sort()]
  const filtered = tools.filter(t => {
    if (toolsStatus[t.name] !== true) return false
    const matchCat = activeCat === 'all' || t.category === activeCat
    const q = search.toLowerCase()
    return matchCat && (!q || t.name.includes(q) || t.desc.toLowerCase().includes(q))
  })

  function selectTool(t: Tool) {
    setSelected(t)
    setShowOptional(false)
    setRunError(null)
    setViewEntry(null)
    const defaults: Record<string, string> = {}
    for (const k of Object.keys(t.params)) defaults[k] = ''
    for (const [k, v] of Object.entries(t.optional)) defaults[k] = String(v)
    setFieldValues(defaults)
  }

  async function runTool() {
    if (!selected) return
    const required = Object.keys(selected.params)
    const missing = required.filter(k => !fieldValues[k]?.trim())
    if (missing.length) { setRunError(`Missing required: ${missing.join(', ')}`); return }
    setRunError(null)
    setRunning(true)
    setViewEntry(null)
    const id = ++runIdRef.current
    const payload: Record<string, unknown> = {}
    for (const k of required) payload[k] = fieldValues[k].trim()
    for (const k of Object.keys(selected.optional)) {
      const v = fieldValues[k]
      if (v !== undefined && v !== '') payload[k] = v
    }
    try {
      const result = await api.runTool(selected.endpoint, payload)
      const entry: RunHistoryEntry = { id, tool: selected.name, params: payload, result, ts: new Date() }
      setHistory(h => [entry, ...h])
      setViewEntry(entry)
    } catch (e) {
      setRunError(String(e))
    } finally {
      setRunning(false)
    }
  }

  const requiredKeys = selected ? Object.keys(selected.params) : []
  const optionalKeys = selected ? Object.keys(selected.optional) : []

  return (
    <div className="run-page">
      {modalEntry && <RunResultModal entry={modalEntry} onClose={() => setModalEntry(null)} />}
      {/* ── Left: tool picker ── */}
      <div className="run-picker">
        <div className="run-picker-controls">
          <input
            className="search-input mono"
            placeholder="Search tools…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <div className="cat-tabs run-cat-tabs">
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
        <div className="run-tool-list">
          {filtered.map(t => (
              <button
                key={t.name}
                className={`run-tool-item${selected?.name === t.name ? ' active' : ''}`}
                onClick={() => selectTool(t)}
              >
                <span className="run-tool-name mono">{t.name}</span>
                <span className="run-tool-cat">{t.category.replace(/_/g, ' ')}</span>
              </button>
            ))}
        </div>
      </div>

      {/* ── Centre: form + output ── */}
      <div className="run-main">
        {!selected ? (
          <div className="run-empty">
            <Play size={36} color="var(--text-dim)" />
            <p>Select a tool from the list</p>
          </div>
        ) : (
          <>
            <div className="run-form-header">
              <span className="run-form-name mono">{selected.name}</span>
              <span className="modal-cat">{selected.category.replace(/_/g, ' ')}</span>
              {toolsStatus[selected.name] === true && (
                <span className="modal-status modal-status--installed"><CheckCircle size={11} /> installed</span>
              )}
              {toolsStatus[selected.name] === false && (
                <span className="modal-status modal-status--missing"><XCircle size={11} /> not installed</span>
              )}
            </div>
            <p className="run-form-desc">{selected.desc}</p>

            <div className="run-form">
              {requiredKeys.map(k => (
                <ParamField
                  key={k} name={k}
                  value={fieldValues[k] ?? ''}
                  onChange={v => setFieldValues(fv => ({ ...fv, [k]: v }))}
                  required
                />
              ))}

              {optionalKeys.length > 0 && (
                <button className="run-opt-btn" onClick={() => setShowOptional(o => !o)}>
                  {showOptional ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  Optional parameters ({optionalKeys.length})
                </button>
              )}
              {showOptional && optionalKeys.map(k => (
                <ParamField
                  key={k} name={k}
                  value={fieldValues[k] ?? ''}
                  onChange={v => setFieldValues(fv => ({ ...fv, [k]: v }))}
                />
              ))}

              {runError && (
                <div className="run-error"><AlertCircle size={13} /> {runError}</div>
              )}

              <button className="run-submit" onClick={runTool} disabled={running}>
                {running
                  ? <><RefreshCw size={13} className="spin" /> Running…</>
                  : <><Play size={13} /> Run {selected.name}</>}
              </button>
            </div>

            {/* Output */}
            {(running || viewEntry) && (
              <div className="run-output">
                <div className="run-output-header">
                  {running ? (
                    <span className="run-output-status running">
                      <RefreshCw size={12} className="spin" /> running…
                    </span>
                  ) : viewEntry && (
                    <>
                      <span className={`run-output-status ${viewEntry.result.success ? 'ok' : 'fail'}`}>
                        {viewEntry.result.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
                        {viewEntry.result.success ? 'success' : 'failed'}
                      </span>
                      <span className="run-output-meta mono">exit {viewEntry.result.return_code}</span>
                      <span className="run-output-meta mono">{viewEntry.result.execution_time.toFixed(2)}s</span>
                      {viewEntry.result.timed_out && <span className="run-output-meta amber">timed out</span>}
                      {viewEntry.result.partial_results && <span className="run-output-meta amber">partial</span>}
                      <div className="run-export-btns">
                        <button className="run-export-btn" onClick={() => exportEntry(viewEntry, 'txt')} title="Export as .txt">
                          <Download size={11} /> TXT
                        </button>
                        <button className="run-export-btn" onClick={() => exportEntry(viewEntry, 'json')} title="Export as .json">
                          <Download size={11} /> JSON
                        </button>
                      </div>
                    </>
                  )}
                </div>
                {viewEntry && (
                  <pre className="run-output-pre">
                    {viewEntry.result.stdout || viewEntry.result.stderr || '(no output)'}
                  </pre>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Right: history ── */}
      <div className="run-history">
        <div className="run-history-header">
          <span>History</span>
          <span className="badge">{history.length}</span>
          {history.length > 0 && (
            <button
              className="run-history-clear"
              title="Clear history"
              onClick={() => { setHistory([]); setHistSearch('') }}
            >
              <XCircle size={12} />
            </button>
          )}
        </div>
        {history.length > 0 && (
          <div className="run-history-search">
            <input
              className="run-history-search-input mono"
              placeholder="Filter…"
              value={histSearch}
              onChange={e => setHistSearch(e.target.value)}
            />
            {histSearch && (
              <button className="run-history-search-clear" onClick={() => setHistSearch('')}>
                <XCircle size={11} />
              </button>
            )}
          </div>
        )}
        {(() => {
          const q = histSearch.toLowerCase()
          const visible = q
            ? history.filter(e => e.tool.includes(q) || Object.values(e.params).some(v => String(v).toLowerCase().includes(q)))
            : history
          if (visible.length === 0) return <p className="run-history-empty">{histSearch ? 'No matches' : 'No runs yet'}</p>
          return visible.map(e => (
            <button
              key={e.id}
              className={`run-history-item${viewEntry?.id === e.id ? ' active' : ''}`}
              onClick={() => setModalEntry(e)}
            >
              <span className={`run-hist-dot ${e.result.success ? 'ok' : 'fail'}`} />
              <span className="run-hist-name mono">{e.tool}</span>
              <span className="run-hist-time">{e.ts.toLocaleTimeString('en-GB')}</span>
            </button>
          ))
        })()}
      </div>
    </div>
  )
}

// ─── Tool Detail Modal ────────────────────────────────────────────────────────

function ToolModal({ tool, onClose, installed }: { tool: Tool; onClose: () => void; installed: boolean | undefined }) {
  const eff = Math.round(tool.effectiveness * 100)
  const effColor = eff >= 90 ? 'var(--green)' : eff >= 75 ? 'var(--amber)' : 'var(--red)'
  const requiredParams = Object.entries(tool.params).filter(([, v]) => v.required)
  const optionalParams = Object.entries(tool.optional)

  // Close on backdrop click
  function onBackdrop(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose()
  }

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-backdrop" onClick={onBackdrop}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-name mono">{tool.name}</span>
            <span className="modal-cat">{tool.category.replace(/_/g, ' ')}</span>
            {installed === true && (
              <span className="modal-status modal-status--installed">
                <CheckCircle size={11} /> installed
              </span>
            )}
            {installed === false && (
              <span className="modal-status modal-status--missing">
                <XCircle size={11} /> not installed
              </span>
            )}
          </div>
          <button className="modal-close" onClick={onClose}><XCircle size={18} /></button>
        </div>

        <div className="modal-body">
          <p className="modal-desc">{tool.desc}</p>

          {/* Effectiveness */}
          <div className="modal-eff-row">
            <span className="modal-label">Effectiveness</span>
            <div className="modal-eff-bar">
              <div className="modal-eff-fill" style={{ width: `${eff}%`, background: effColor }} />
            </div>
            <span className="modal-eff-pct" style={{ color: effColor }}>{eff}%</span>
          </div>

          {/* Install — only shown when tool is not installed (or status unknown) */}
          {installed !== true && (
            <div className="modal-section">
              <span className="modal-label">Install</span>
              <div className="modal-code mono">{installHint(tool.name)}</div>
            </div>
          )}

          {/* API Endpoint */}
          <div className="modal-section">
            <span className="modal-label">API Endpoint</span>
            <div className="modal-code mono">{tool.method} {tool.endpoint}</div>
          </div>

          {/* Required params */}
          {requiredParams.length > 0 && (
            <div className="modal-section">
              <span className="modal-label">Required Parameters</span>
              <div className="modal-params">
                {requiredParams.map(([k]) => (
                  <span key={k} className="modal-param modal-param--required mono">{k}</span>
                ))}
              </div>
            </div>
          )}

          {/* Optional params */}
          {optionalParams.length > 0 && (
            <div className="modal-section">
              <span className="modal-label">Optional Parameters</span>
              <table className="modal-table">
                <thead>
                  <tr><th>Parameter</th><th>Default</th></tr>
                </thead>
                <tbody>
                  {optionalParams.map(([k, v]) => (
                    <tr key={k}>
                      <td className="mono">{k}</td>
                      <td className="mono">{String(v) || <em>—</em>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Tool Registry Section ────────────────────────────────────────────────────

function ToolRegistrySection({ tools, toolsStatus }: { tools: Tool[]; toolsStatus: Record<string, boolean> }) {
  const [search, setSearch] = useState('')
  const [activeCat, setActiveCat] = useState<string>('all')
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [missingOnly, setMissingOnly] = useState(false)

  const cats = ['all', ...Array.from(new Set(tools.map(t => t.category))).sort()]
  const filtered = tools.filter(t => {
    const matchCat = activeCat === 'all' || t.category === activeCat
    const q = search.toLowerCase()
    const matchSearch = !q || t.name.includes(q) || t.desc.toLowerCase().includes(q)
    const matchMissing = !missingOnly || toolsStatus[t.name] === false
    return matchCat && matchSearch && matchMissing
  })

  const missingCount = tools.filter(t => toolsStatus[t.name] === false).length

  return (
    <>
      {selectedTool && <ToolModal tool={selectedTool} onClose={() => setSelectedTool(null)} installed={toolsStatus[selectedTool.name]} />}
      <section className="section">
        <div className="section-header">
          <h3>Tool Registry <span className="badge">{tools.length}</span></h3>
        </div>
        <div className="registry-controls">
          <div className="registry-controls-top">
            <input
              className="search-input mono"
              placeholder="Search tools…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <button
              className={`registry-missing-toggle${missingOnly ? ' active' : ''}`}
              onClick={() => setMissingOnly(o => !o)}
              title="Show only tools that are not installed"
            >
              <XCircle size={12} />
              Not installed
              {missingCount > 0 && <span className="badge">{missingCount}</span>}
            </button>
          </div>
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
            <div
              key={t.name}
              className="registry-card registry-card--clickable"
              onClick={() => setSelectedTool(t)}
              title={`Click for details on ${t.name}`}
            >
              <div className="registry-card-top">
                <span className="registry-name mono">{t.name}</span>
                <span className="registry-cat">{t.category.replace(/_/g, ' ')}</span>
                {toolsStatus[t.name] === true && (
                  <span className="registry-installed" title="Installed"><CheckCircle size={11} color="var(--green)" /></span>
                )}
                {toolsStatus[t.name] === false && (
                  <span className="registry-installed" title="Not installed"><XCircle size={11} color="var(--red)" /></span>
                )}
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
    </>
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
type Page = 'dashboard' | 'settings' | 'help' | 'logs' | 'run'

export default function App() {
  const [authed, setAuthed] = useState(hasToken())
  const [needsAuth, setNeedsAuth] = useState(false)
  const [page, setPage] = useState<Page>('dashboard')

  const [health, setHealth] = useState<WebDashboardResponse | null>(null)
  const [tools, setTools] = useState<Tool[]>([])
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [runHistory, setRunHistory] = useState<RunHistoryEntry[]>([])
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashCacheSize, setDashCacheSize] = useState<number | null>(null)
  const [dashCacheTtl, setDashCacheTtl] = useState<number | null>(null)
  const [logLines, setLogLines] = useState<string[]>([])
  const [logAutoScroll, setLogAutoScroll] = useState(true)
  const [logLimit, setLogLimit] = useState(500)
  const logEndRef = useRef<HTMLDivElement>(null)
  const sseRef = useRef<EventSource | null>(null)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const h = await api.dashboard()
      setHealth(h)
      setHistory(prev => {
        const next = [
          ...prev.slice(-29),
          { t: Date.now(), cpu: h.resources.cpu_percent, mem: h.resources.memory_percent },
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
    api.dashboard().then(h => {
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

  // SSE log stream
  useEffect(() => {
    const es = api.logStream(150)
    sseRef.current = es
    es.onmessage = (e) => {
      setLogLines(prev => {
        const next = [...prev, e.data]
        return next.length > 500 ? next.slice(-500) : next
      })
    }
    return () => { es.close() }
  }, [])

  // Auto-scroll log to bottom (only when on logs page and autoscroll enabled)
  useEffect(() => {
    if (page === 'logs' && logAutoScroll) logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logLines, page, logAutoScroll])

  if (needsAuth && !authed) {
    return <TokenGate onUnlocked={() => { setAuthed(true); setNeedsAuth(false) }} />
  }

  const cu = health?.resources

  return (
    <div className="layout">
      {/* ── Top Bar ── */}
      <header className="topbar">
        <div className="topbar-brand">
          <img src={faviconUrl} width={18} height={18} alt="" />
          <span className="brand-text">HexStrike Community Edition</span>
          <span className="brand-version mono">{health?.version ?? '…'}</span>
        </div>

        {/* ── Nav Tabs ── */}
        <nav className="topbar-nav">
          <button className={`nav-tab ${page === 'dashboard' ? 'active' : ''}`} onClick={() => setPage('dashboard')}>
            <LayoutDashboard size={13} /> Dashboard
          </button>
          <button className={`nav-tab ${page === 'run' ? 'active' : ''}`} onClick={() => setPage('run')}>
            <Play size={13} /> Run
          </button>
          <button className={`nav-tab ${page === 'logs' ? 'active' : ''}`} onClick={() => setPage('logs')}>
            <Terminal size={13} /> Logs
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

        {/* ── Run Page ── */}
        {page === 'run' && (
          <RunPage tools={tools} toolsStatus={health?.tools_status ?? {}} runHistory={runHistory} setRunHistory={setRunHistory} />
        )}

        {/* ── Logs Page ── */}
        {page === 'logs' && (
          <div className="page-content">
            <section className="section">
              <div className="section-header">
                <h3>Server Log</h3>
                <div className="log-toolbar">
                  <label className="log-toggle">
                    <input
                      type="checkbox"
                      checked={logAutoScroll}
                      onChange={e => setLogAutoScroll(e.target.checked)}
                    />
                    Auto-scroll
                  </label>
                  <label className="log-limit-label">
                    Show last
                    <select
                      className="log-limit-select"
                      value={logLimit}
                      onChange={e => setLogLimit(Number(e.target.value))}
                    >
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                      <option value={200}>200</option>
                      <option value={500}>500</option>
                    </select>
                    lines
                  </label>
                  <span className="section-meta mono">{logLines.length} buffered</span>
                </div>
              </div>
              <div className="log-viewer log-viewer--full">
                {logLines.length === 0
                  ? <span className="log-empty">Waiting for log data…</span>
                  : logLines.slice(-logLimit).map((line, i) => {
                      const lvl = /\bERROR\b/.test(line) ? 'error'
                        : /\bWARN(ING)?\b/.test(line) ? 'warn'
                        : /\bDEBUG\b/.test(line) ? 'debug'
                        : ''
                      return <div key={i} className={`log-line ${lvl}`}>{line}</div>
                    })
                }
                <div ref={logEndRef} />
              </div>
            </section>
          </div>
        )}

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
                    label="Commands"
                    value={health.telemetry?.commands_executed ?? 0}
                    sub={(() => {
                      const total = health.telemetry?.commands_executed ?? 0
                      const rate = parseFloat(health.telemetry?.success_rate ?? '0')
                      const ok = Math.round(total * rate / 100)
                      const failed = total - ok
                      return `${ok} ok · ${failed} failed`
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
                    {Object.entries(health.category_stats).map(([cat, stats]) => {
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

                {/* ── Tool Registry ── */}
                {tools.length > 0 && <ToolRegistrySection tools={tools} toolsStatus={health?.tools_status ?? {}} />}
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
