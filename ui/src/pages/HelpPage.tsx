import { useState } from 'react'
import { Terminal, FlaskConical } from 'lucide-react'
import { CodeBlock } from '../components/CodeBlock'
import './HelpPage.css'

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

export default function HelpPage() {
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

      <section className="section help-about-section">
        <div className="section-header"><h3>Demo Mode</h3></div>
        <div className="help-about">
          <p className="help-about-desc">
            Activate demo mode to explore the dashboard and IDE integration. All data is synthetic but designed to feel realistic. Ideal for learning, demos, or just satisfying your curiosity!
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
    </div>
  )
}
