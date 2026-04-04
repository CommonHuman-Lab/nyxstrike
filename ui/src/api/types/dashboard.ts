export interface WebDashboardResponse {
  status: string;
  version: string;
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
  cache_stats: {
    evictions: number;
    hit_rate: string;
    hits: number;
    max_size: number;
    misses: number;
    size: number;
  };
}

export type HealthResponse = WebDashboardResponse;

export type ResourceUsageResponse = {
  current_usage: WebDashboardResponse['resources'];
  timestamp: string;
};
