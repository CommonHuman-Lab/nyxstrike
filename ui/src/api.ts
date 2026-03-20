// Typed API wrappers for the HexStrike Flask backend

export interface HealthResponse {
  status: string;
  message: string;
  version: string;
  tools_status: Record<string, boolean>;
  all_essential_tools_available: boolean;
  total_tools_available: number;
  total_tools_count: number;
  category_stats: Record<string, { total: number; available: number }>;
  cache_stats: {
    hits: number;
    misses: number;
    size: number;
    evictions: number;
  };
  telemetry: {
    commands_executed: number;
    success_rate: string;
    average_execution_time: string;
  };
  uptime: number;
  tool_availability_age_seconds: number;
}

export interface ResourceUsageResponse {
  success: boolean;
  current_usage: {
    cpu_percent: number;
    memory_percent: number;
    memory_available_gb: number;
    disk_percent: number;
    disk_free_gb: number;
    disk_used_gb?: number;
    disk_total_gb?: number;
    load_avg?: number[];
    process_count?: number;
  };
  usage_trends?: unknown;
  timestamp: string;
}

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

export const api = {
  health: () => apiFetch<HealthResponse>('/health'),
  resources: () => apiFetch<ResourceUsageResponse>('/api/process/resource-usage'),
  tools: () => apiFetch<ToolsCatalogResponse>('/api/tools'),
  getSettings: () => apiFetch<SettingsResponse>('/api/settings'),
  patchSettings: (runtime: Partial<Settings['runtime']>) =>
    apiFetch<PatchSettingsResponse>('/api/settings', {
      method: 'PATCH',
      body: JSON.stringify({ runtime }),
    }),
  logStream: (lines = 100): EventSource => new EventSource(`/api/logs/stream?lines=${lines}`),
  runTool: (endpoint: string, params: Record<string, unknown>) =>
    apiFetch<ToolExecResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(params),
    }),
};
