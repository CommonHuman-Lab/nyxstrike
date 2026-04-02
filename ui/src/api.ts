// Typed API wrappers for the HexStrike Flask backend

export interface WebDashboardResponse {
  // Server identity
  status: string;
  version: string;
  uptime: number;

  // Telemetry
  telemetry: {
    commands_executed: number;
    success_rate: string;
    average_execution_time: string;
  };

  // Tool availability
  tools_status: Record<string, boolean>;
  all_essential_tools_available: boolean;
  total_tools_available: number;
  total_tools_count: number;
  category_stats: Record<string, { total: number; available: number }>;
  tool_availability_age_seconds: number | null;

  // System resources
  resources: {
    cpu_percent: number;
    memory_total_gb: number;
    memory_percent: number;
    memory_available_gb: number;
    memory_used_gb: number;
    disk_percent: number;
    disk_free_gb: number;
    disk_used_gb: number;
    disk_total_gb: number;
    load_avg?: number[];
    network_bytes_sent: number;
    network_bytes_recv: number;
  };
  resources_timestamp: string;

  // Cache stats
  cache_stats: {
    evictions: number;
    hit_rate: string;
    hits: number;
    max_size: number;
    misses: number;
    size: number;
  };
}

// Keep legacy aliases so callers can use familiar field names
export type HealthResponse = WebDashboardResponse;
export type ResourceUsageResponse = { current_usage: WebDashboardResponse['resources']; timestamp: string };

export interface Tool {
  name: string;
  desc: string;
  category: string;
  endpoint: string;
  method: string;
  params: Record<string, { required?: boolean }>;
  optional: Record<string, string | number | boolean>;
  effectiveness: number;
  parent_tool?: string | null;
}

export interface ToolsCatalogResponse {
  success: boolean;
  total: number;
  categories: string[];
  tools: Tool[];
}

let _token: string | null = sessionStorage.getItem('hexstrike_token');

export function setToken(t: string) {
  _token = t;
  sessionStorage.setItem('hexstrike_token', t);
}

export function clearToken() {
  _token = null;
  sessionStorage.removeItem('hexstrike_token');
}

export function hasToken(): boolean {
  return !!_token;
}

async function apiFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> || {}),
  };
  if (_token) {
    headers['Authorization'] = `Bearer ${_token}`;
  }
  const res = await fetch(path, { ...opts, headers });
  if (res.status === 401) {
    clearToken();
    throw new Error('UNAUTHORIZED');
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export interface WordlistEntry {
  name: string;
  path: string;
  type: string;
  speed: string;
  coverage: string;
}

export interface Settings {
  server: {
    host: string;
    port: number;
    auth_enabled: boolean;
    debug_mode: boolean;
    data_dir: string;
  };
  runtime: {
    command_timeout: number;
    cache_size: number;
    cache_ttl: number;
    tool_availability_ttl: number;
  };
  wordlists: WordlistEntry[];
}

export interface SettingsResponse {
  success: boolean;
  settings: Settings;
}

export interface PatchSettingsResponse {
  success: boolean;
  updated: Record<string, number>;
  settings?: Settings;
  errors?: Record<string, string>;
  error?: string;
}

export interface ToolExecResponse {
  stdout: string;
  stderr: string;
  return_code: number;
  success: boolean;
  timed_out: boolean;
  partial_results: boolean;
  execution_time: number;
  timestamp: string;
}

export interface RunHistoryEntry {
  id: number;
  tool: string;
  endpoint: string;
  params: Record<string, unknown>;
  stdout: string;
  stderr: string;
  return_code: number;
  success: boolean;
  timed_out: boolean;
  partial_results: boolean;
  execution_time: number;
  timestamp: string;
}

export interface RunHistoryResponse {
  success: boolean;
  total: number;
  runs: RunHistoryEntry[];
}

// ─── Process Dashboard types ─────────────────────────────────────────────────

export interface ProcessEntry {
  pid: number;
  command: string;
  status: string;
  runtime: string;
  progress_percent: string;
  progress_bar: string;
  eta: string;
  bytes_processed: number;
  last_output: string;
}

export interface ProcessSystemLoad {
  cpu_percent: number;
  memory_percent: number;
  active_connections: number;
}

export interface ProcessDashboardResponse {
  timestamp: string;
  total_processes: number;
  visual_dashboard: string;
  processes: ProcessEntry[];
  system_load: ProcessSystemLoad;
}

export interface PoolStatsResponse {
  success?: boolean;
  [key: string]: unknown;
}

// ─── Sessions types ──────────────────────────────────────────────────────────

export interface SessionSummary {
  session_id: string;
  target: string;
  status?: string;
  total_findings: number;
  iterations: number;
  tools_executed: string[];
  workflow_steps?: AttackChainStep[];
  source?: string;
  objective?: string;
  handover_history?: Array<{
    timestamp: string;
    session_id: string;
    category: string;
    confidence: number;
    note?: string;
  }>;
  created_at: number;
  updated_at: number;
}

export interface SessionsResponse {
  success: boolean;
  active: SessionSummary[];
  completed: SessionSummary[];
  total_active: number;
  total_completed: number;
}

export interface AttackChainStep {
  tool: string;
  parameters: Record<string, unknown>;
  expected_outcome?: string;
  success_probability?: number;
  execution_time_estimate?: number;
  dependencies?: string[];
}

export interface AttackChain {
  target: string;
  steps: AttackChainStep[];
  success_probability: number;
  estimated_time: number;
  required_tools: string[];
  risk_level: string;
}

export interface CreateAttackChainResponse {
  success: boolean;
  target: string;
  objective: string;
  attack_chain: AttackChain;
  session_id?: string;
  timestamp: string;
}

export interface ClassifyTaskResponse {
  success: boolean;
  category: string;
  confidence: number;
  category_description: string;
  tools: Tool[];
  tool_summary: string;
  timestamp: string;
}

export interface SessionMutationResponse {
  success: boolean;
  session: SessionSummary;
  timestamp?: string;
  error?: string;
}

export interface SessionDetailResponse {
  success: boolean;
  state: 'active' | 'completed';
  session: SessionSummary;
  error?: string;
}

export interface SessionHandoverResponse {
  success: boolean;
  handover?: {
    timestamp: string;
    session_id: string;
    category: string;
    confidence: number;
    note?: string;
  };
  session?: SessionSummary;
  error?: string;
}

export interface CacheStatsResponse {
  total: number;
  currentsize: number;
  hits: number;
  misses: number;
  evicted: number;
  [key: string]: number;
}

export interface ToolCategoriesResponse {
  categories: Record<string, string[]>;
}

export const api = {
  dashboard: () => apiFetch<WebDashboardResponse>('/web-dashboard'),
  tools: () => apiFetch<ToolsCatalogResponse>('/api/tools'),
  getToolCategories: () => apiFetch<ToolCategoriesResponse>('/api/tools/categories'),
  getSettings: () => apiFetch<SettingsResponse>('/api/settings'),
  patchSettings: (runtime: Partial<Settings['runtime']>) =>
    apiFetch<PatchSettingsResponse>('/api/settings', {
      method: 'PATCH',
      body: JSON.stringify({ runtime }),
    }),
  logStream: (lines = 100): EventSource => new EventSource(`/api/logs/stream?lines=${lines}`),
  runHistory: (limit?: number) =>
    apiFetch<RunHistoryResponse>(`/api/runs/history${limit ? `?limit=${limit}` : ''}`),
  clearRunHistory: () =>
    apiFetch<{ success: boolean }>('/api/runs/clear', { method: 'POST' }),
  runTool: (endpoint: string, params: Record<string, unknown>) =>
    apiFetch<ToolExecResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  processDashboard: () => apiFetch<ProcessDashboardResponse>('/api/processes/dashboard'),
  processPoolStats: () => apiFetch<PoolStatsResponse>('/api/process/pool-stats'),
  terminateProcess: (pid: number) =>
    apiFetch<{ success: boolean; message?: string; error?: string }>(`/api/processes/terminate/${pid}`, { method: 'POST' }),
  cacheStats: () => apiFetch<CacheStatsResponse>('/api/cache/stats'),
  clearCache: () => apiFetch<{success: boolean, message: string}>(
    '/api/cache/clear', { method: 'POST' }),
  pauseProcess: (pid: number) =>
    apiFetch<{ success: boolean; message?: string; error?: string }>(`/api/processes/pause/${pid}`, { method: 'POST' }),
  resumeProcess: (pid: number) =>
    apiFetch<{ success: boolean; message?: string; error?: string }>(`/api/processes/resume/${pid}`, { method: 'POST' }),
  sessions: () => apiFetch<SessionsResponse>('/api/sessions'),
  session: (sessionId: string) => apiFetch<SessionDetailResponse>(`/api/sessions/${sessionId}`),
  createSession: (payload: {
    target: string;
    workflow_steps?: AttackChainStep[];
    source?: string;
    objective?: string;
    session_id?: string;
    metadata?: Record<string, unknown>;
  }) =>
    apiFetch<SessionMutationResponse>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateSession: (sessionId: string, payload: Partial<{
    target: string;
    status: string;
    total_findings: number;
    iterations: number;
    workflow_steps: AttackChainStep[];
    objective: string;
    source: string;
    metadata: Record<string, unknown>;
  }>) =>
    apiFetch<SessionMutationResponse>(`/api/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  handoverSession: (sessionId: string, note = '') =>
    apiFetch<SessionHandoverResponse>(`/api/sessions/${sessionId}/handover`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    }),
  createAttackChain: (target: string, objective = 'comprehensive') =>
    apiFetch<CreateAttackChainResponse>('/api/intelligence/create-attack-chain', {
      method: 'POST',
      body: JSON.stringify({ target, objective }),
    }),
  classifyTask: (description: string) =>
    apiFetch<ClassifyTaskResponse>('/api/intelligence/classify-task', {
      method: 'POST',
      body: JSON.stringify({ description }),
    }),
  dashboardStream: (): EventSource => new EventSource('/web-dashboard/stream'),
  processDashboardStream: (): EventSource => new EventSource('/api/processes/dashboard/stream'),
  processPoolStatsStream: (): EventSource => new EventSource('/api/process/pool-stats/stream'),
  sessionsStream: (): EventSource => new EventSource('/api/sessions/stream'),
};
