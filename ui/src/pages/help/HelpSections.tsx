import { Terminal, FlaskConical, Keyboard, Layout } from 'lucide-react'
import { CodeBlock } from '../../components/CodeBlock'
import { CollapsibleSection } from '../../components/CollapsibleSection'
import type { IdeConfig } from './ideConfigs'

const MCP_FLAGS: Array<[string, string, string]> = [
  ['--server URL', 'NyxStrike server URL', 'http://127.0.0.1:8888'],
  ['--profile PROFILE', 'Tool profile(s) to load', 'full  |  web_recon  |  exploit_framework  |  …'],
  ['--compact', 'Load only classify_task + run_tool — ideal for small/local LLMs', '—'],
  ['--auth-token TOKEN', 'Bearer token if NYXSTRIKE_API_TOKEN is set on the server', '—'],
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
    <CollapsibleSection title="IDE / Agent Configuration" defaultOpen>
      <div className="help-path-row">
        <label className="help-path-label">Installation path</label>
        <input
          className="search-input mono help-path-input"
          name="install-path"
          value={installPath}
          onChange={e => setInstallPath(e.target.value)}
          placeholder="/path/to/nyxstrike"
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
    </CollapsibleSection>
  )
}

export function FlagsSection() {
  return (
    <CollapsibleSection title="MCP Client Flags">
      <div className="flags-table">
        {MCP_FLAGS.map(([flag, description, defaultValue]) => (
          <div key={flag} className="flag-row">
            <code className="flag-name mono">{flag}</code>
            <span className="flag-desc">{description}</span>
            {defaultValue !== '—' && <code className="flag-default mono">{defaultValue}</code>}
          </div>
        ))}
      </div>
    </CollapsibleSection>
  )
}

export function AuthenticationSection() {
  return (
    <CollapsibleSection title="Authentication">
      <p className="help-body">
        If you set <code>NYXSTRIKE_API_TOKEN</code> on the server, every request must carry a Bearer token.
        Pass it to the MCP client with <code>--auth-token</code>, or set it in the IDE config under <code>args</code>.
        The dashboard will prompt for it automatically when the server returns 401.
      </p>
      <CodeBlock language="bash" code={`# Server side\nexport NYXSTRIKE_API_TOKEN=your-secret-token\npython3 nyxstrike_server.py\n\n# MCP client side\nnyxstrike-env/bin/python3 nyxstrike_mcp.py \\\n+  --server http://localhost:8888 \\\n+  --auth-token your-secret-token \\\n+  --profile full`} />
    </CollapsibleSection>
  )
}

const UI_FEATURES: Array<{ shortcut: string; title: string; description: string }> = [
  {
    shortcut: 'Ctrl+K',
    title: 'Command Palette',
    description: 'Open the command palette to navigate pages or launch any of the security tools directly.',
  },
  {
    shortcut: 'Ctrl+Shift+C',
    title: 'Chat Panel',
    description: 'Toggle the floating AI chat panel. Supports multi-session history, streaming responses, and tool-call confirmation.',
  },
]

export function CommandPaletteSection() {
  return (
    <CollapsibleSection title="Command Palette">
      <div className="help-feature-row">
        <Keyboard size={14} color="var(--green)" />
        <p className="help-body" style={{ padding: 0, margin: 0 }}>
          Press <code>Ctrl+K</code> (or <code>Cmd+K</code> on macOS) anywhere in the app to open the Command Palette.
        </p>
      </div>
      <p className="help-body">
        The palette lets you jump to any page or instantly launch one of the registered security tools — just start typing to filter. Selecting a tool navigates to the Run page with that tool pre-selected.
      </p>
      <div className="flags-table" style={{ marginTop: 4 }}>
        {[
          ['ArrowUp / ArrowDown', 'Move through results'],
          ['Enter', 'Execute the selected action'],
          ['Escape', 'Close the palette'],
        ].map(([key, desc]) => (
          <div key={key} className="flag-row" style={{ gridTemplateColumns: '200px 1fr' }}>
            <code className="flag-name mono">{key}</code>
            <span className="flag-desc">{desc}</span>
          </div>
        ))}
      </div>
    </CollapsibleSection>
  )
}

export function UIFeaturesSection() {
  return (
    <CollapsibleSection title="UI Features">
      <p className="help-body">
        A few quality-of-life features worth knowing about:
      </p>
      <div className="flags-table">
        {UI_FEATURES.map(({ shortcut, title, description }) => (
          <div key={shortcut} className="flag-row" style={{ gridTemplateColumns: '200px 1fr' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <code className="flag-name mono">{shortcut}</code>
              <span style={{ fontSize: 11, color: 'var(--text-dim)', paddingLeft: 2 }}>{title}</span>
            </div>
            <span className="flag-desc">{description}</span>
          </div>
        ))}
        <div className="flag-row" style={{ gridTemplateColumns: '200px 1fr' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <span className="flag-name mono" style={{ color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 5 }}>
              <Layout size={11} color="var(--green)" /> Navigation
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-dim)', paddingLeft: 2 }}>Page Visibility</span>
          </div>
          <span className="flag-desc">Show or hide individual nav pages from <strong>Settings → Pages</strong>. Dashboard and Settings are always visible.</span>
        </div>
      </div>
    </CollapsibleSection>
  )
}

export function DemoModeSection() {
  return (
    <CollapsibleSection title="Demo Mode" className="help-about-section">
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
    </CollapsibleSection>
  )
}
