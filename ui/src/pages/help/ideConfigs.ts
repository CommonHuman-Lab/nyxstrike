export interface IdeConfig {
  id: string
  label: string
  icon: string
  configPath: string
  note: string
  json: (installPath: string) => string
}

export const IDE_CONFIGS: IdeConfig[] = [
  {
    id: 'claude',
    label: 'Claude Desktop',
    icon: '🤖',
    configPath: '~/.config/Claude/claude_desktop_config.json',
    note: 'Also works for Cursor — same config format.',
    json: (p: string) => JSON.stringify({
      mcpServers: {
        'nyxstrike-ai': {
          command: `${p}/nyxstrike-env/bin/python3`,
          args: [`${p}/nyxstrike_mcp.py`, '--server', 'http://localhost:8888', '--profile', 'full'],
          description: 'NyxStrike',
          timeout: 300,
          disabled: false,
        },
      },
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
        nyxstrike: {
          type: 'stdio',
          command: `${p}/nyxstrike-env/bin/python3`,
          args: [`${p}/nyxstrike_mcp.py`, '--server', 'http://127.0.0.1:8888', '--profile', 'full'],
        },
      },
      inputs: [],
    }, null, 2),
  },
  {
    id: 'opencode',
    label: 'OpenCode',
    icon: '⚡',
    configPath: '~/.config/opencode/opencode.json',
    note: 'OpenCode reads this on startup.',
    json: (p: string) => JSON.stringify({
      $schema: 'https://opencode.ai/config.json',
      mcp: {
        nyxstrike: {
          type: 'local',
          command: [
            `${p}/nyxstrike-env/bin/python3`,
            `${p}/nyxstrike_mcp.py`,
            '--server',
            'http://127.0.0.1:8888',
            '--profile',
            'default',
          ],
          enabled: true,
        },
      },
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
        nyxstrike: {
          command: `${p}/nyxstrike-env/bin/python3`,
          args: [`${p}/nyxstrike_mcp.py`, '--server', 'http://127.0.0.1:8888', '--profile', 'full'],
          timeout: 300,
        },
      },
    }, null, 2),
  },
]
