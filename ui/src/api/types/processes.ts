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
