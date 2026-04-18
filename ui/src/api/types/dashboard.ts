export interface WebDashboardResponse {
  status: string;
  version: string;
  update: {
    current_version: string;
    latest_version: string;
    update_available: boolean;
    checked_at: string;
    source: string;
    error: string | null;
  };
  uptime: number;
  telemetry: {
    commands_executed: number;
    success_rate: string;
    average_execution_time: string;
  };
  tools_status: Record<string, boolean>;
  all_essential_tools_available: boolean;
  total_tools_available: number;
  total_tools_count: number;
  category_stats: Record<string, { total: number; available: number }>;
  tool_availability_age_seconds: number | null;
  // Optional: present in REST /web-dashboard responses and DEMO_HEALTH, but
  // intentionally omitted from /web-dashboard/stream (served instead by the
  // dedicated /api/system/resources/stream endpoint).
  resources?: ResourceUsage;
  resources_timestamp?: string;
  cache_stats: {
    evictions: number;
    hit_rate: string;
    hits: number;
    max_size: number;
    misses: number;
    size: number;
  };
  llm_status?: {
    available: boolean;
    provider?: string;
    model?: string;
    error?: string;
  };
}

export type HealthResponse = WebDashboardResponse;

/** Concrete resource usage shape — always present in dedicated stream payloads. */
export interface ResourceUsage {
  cpu_percent: number;
  memory_total_gb: number;
  memory_percent: number;
  /** Not emitted by /api/system/resources/stream (unused by UI). */
  memory_available_gb?: number;
  memory_used_gb: number;
  disk_percent: number;
  disk_free_gb?: number;
  disk_used_gb: number;
  disk_total_gb: number;
  load_avg?: number[];
  network_bytes_sent: number;
  network_bytes_recv: number;
}

/** Shape of the /api/system/resources/stream SSE payload. */
export interface SystemResourcesResponse {
  resources: ResourceUsage;
  resources_timestamp: string;
}

export type ResourceUsageResponse = {
  current_usage: ResourceUsage;
  timestamp: string;
};
