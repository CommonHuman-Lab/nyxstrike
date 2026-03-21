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
    memory_percent: number;
    memory_available_gb: number;
    disk_percent: number;
    disk_free_gb: number;
    load_avg?: number[];
  };
  resources_timestamp: string;
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

export interface CacheStatsResponse {
  total: number;
  currentsize: number;
  hits: number;
  misses: number;
  evicted: number;
  [key: string]: number;
}

export const api = {
  dashboard: () => apiFetch<WebDashboardResponse>('/web-dashboard'),
  tools: () => apiFetch<ToolsCatalogResponse>('/api/tools'),
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
};
