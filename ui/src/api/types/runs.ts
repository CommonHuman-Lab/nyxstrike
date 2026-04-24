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

/** Lightweight run record returned by /api/runs/history/summary — no stdout/stderr/params. */
export interface RunHistorySummaryEntry {
  id: number;
  tool: string;
  timestamp: string;
  success: boolean;
  execution_time: number;
}

export interface RunHistorySummaryResponse {
  success: boolean;
  total: number;
  runs: RunHistorySummaryEntry[];
}
