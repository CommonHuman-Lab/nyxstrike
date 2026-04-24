export interface ProcessEntry {
  pid: number | null;
  task_id?: string | null;
  ai_task?: boolean;
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

export interface ProcessListEntry {
  pid: number | null;
  task_id?: string | null;
  ai_task?: boolean;
  command: string;
  status: string;
  start_time: number;
  progress: number;
  last_output: string;
  bytes_processed: number;
  /** Present on AI tasks — identifies which NyxStrike session spawned the task. */
  session_id?: string;
}

export interface ProcessListResponse {
  success: boolean;
  active_processes: Record<string, ProcessListEntry>;
  total_count: number;
 }

/** Payload emitted by the unified /api/processes/stream SSE endpoint. */
export interface ProcessesStreamResponse {
  success: boolean;
  timestamp: string;
  processes: Record<string, ProcessListEntry>;
  total_count: number;
  system_load: ProcessSystemLoad;
  pool_stats: Record<string, unknown>;
}
