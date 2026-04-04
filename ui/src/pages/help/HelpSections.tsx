import { Terminal, FlaskConical } from 'lucide-react'
import { CodeBlock } from '../../components/CodeBlock'
import type { IdeConfig } from './ideConfigs'

const MCP_FLAGS: Array<[string, string, string]> = [
  ['--server URL', 'HexStrike server URL', 'http://127.0.0.1:8888'],
  ['--profile PROFILE', 'Tool profile(s) to load', 'full  |  web_recon  |  exploit_framework  |  …'],
  ['--compact', 'Load only classify_task + run_tool — ideal for small/local LLMs', '—'],
  ['--auth-token TOKEN', 'Bearer token if HEXSTRIKE_API_TOKEN is set on the server', '—'],
  ['--timeout SECS', 'Request timeout in seconds', '300'],
  ['--debug', 'Enable verbose debug logging', '—'],
  ['--disable-ssl-verify', 'Skip SSL verification (reverse proxy setups)', '—'],
]

export function IdeConfigSection({
  installPath,
  setInstallPath,
  pathDetected,
  activeIde,
  setActiveIde,
  ideConfigs,
  selectedIde,
}: {
  installPath: string
  setInstallPath: (value: string) => void
  pathDetected: boolean
  activeIde: string
  setActiveIde: (ideId: string) => void
  ideConfigs: IdeConfig[]
  selectedIde: IdeConfig
}) {
  return (
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
        {pathDetected && <span className="help-path-detected">Detected from server</span>}
      </div>

      <div className="ide-tabs">
        {ideConfigs.map(ide => (
          <button
            key={ide.id}
            className={`ide-tab ${activeIde === ide.id ? 'active' : ''}`}
            onClick={() => setActiveIde(ide.id)}
          >
            {ide.icon} {ide.label}
          </button>
        ))}
      </div>

      <div className="ide-panel">
        <div className="ide-config-path">
          <Terminal size={13} color="var(--text-dim)" />
          <span className="mono">{selectedIde.configPath}</span>
        </div>
        {selectedIde.note && <p className="ide-note">{selectedIde.note}</p>}
        <CodeBlock language="json" code={selectedIde.json(installPath)} />
      </div>
    </section>
  )
}

export function FlagsSection() {
  return (
    <section className="section">
      <div className="section-header"><h3>MCP Client Flags</h3></div>
      <div className="flags-table">
        {MCP_FLAGS.map(([flag, description, defaultValue]) => (
          <div key={flag} className="flag-row">
            <code className="flag-name mono">{flag}</code>
            <span className="flag-desc">{description}</span>
            {defaultValue !== '—' && <code className="flag-default mono">{defaultValue}</code>}
          </div>
        ))}
      </div>
    </section>
  )
}

export function AuthenticationSection() {
  return (
    <section className="section">
      <div className="section-header"><h3>Authentication</h3></div>
      <p className="help-body">
        If you set <code>HEXSTRIKE_API_TOKEN</code> on the server, every request must carry a Bearer token.
        Pass it to the MCP client with <code>--auth-token</code>, or set it in the IDE config under <code>args</code>.
        The dashboard will prompt for it automatically when the server returns 401.
      </p>
      <CodeBlock language="bash" code={`# Server side\nexport HEXSTRIKE_API_TOKEN=your-secret-token\npython3 hexstrike_server.py\n\n# MCP client side\nhexstrike-env/bin/python3 hexstrike_mcp.py \\\n+  --server http://localhost:8888 \\\n+  --auth-token your-secret-token \\\n+  --profile full`} />
    </section>
  )
}

export function DemoModeSection() {
  return (
    <section className="section help-about-section">
      <div className="section-header"><h3>Demo Mode</h3></div>
      <div className="help-about">
        <p className="help-about-desc">
          Activate demo mode to explore the dashboard. All data is synthetic but designed to feel realistic. Ideal for learning, demos, or just satisfying your curiosity!
        </p>
        <button
          className="help-demo-btn"
          onClick={() => { window.location.href = window.location.pathname + '?demo=1' + window.location.hash }}
        >
          <FlaskConical size={13} />
          Try demo mode
        </button>
      </div>
    </section>
  )
}
