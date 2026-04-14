export interface LlmVulnerability {
  id: number;
  session_id: string;
  vuln_name: string;
  severity: string;
  port: string;
  service: string;
  description: string;
  fix_text: string;
  created_at: string;
}

export interface LlmSession {
  session_id: string;
  target: string;
  objective: string;
  status: string;
  risk_level: string | null;
  summary: string | null;
  provider: string | null;
  model: string | null;
  tool_loops: number;
  started_at: string;
  completed_at: string | null;
}

export interface LlmSessionsResponse {
  success: boolean;
  sessions: LlmSession[];
  count: number;
}

export interface LlmSessionDetailResponse {
  success: boolean;
  session: LlmSession;
  vulnerabilities: LlmVulnerability[];
}

export interface AnalyzeSessionResponse {
  success: boolean;
  session_id?: string;
  target?: string;
  objective?: string;
  risk_level?: string;
  summary?: string;
  vulnerabilities?: LlmVulnerability[];
  next_steps?: Array<{ tool: string; reason: string }>;
  logs_analysed?: number;
  saved_path?: string;
  error?: string;
}

export interface FollowUpSessionResponse {
  success: boolean;
  session_id?: string;
  target?: string;
  objective?: string;
  summary?: string;
  steps?: Array<{ tool: string; params: string; reason: string }>;
  next_steps?: Array<{ tool: string; reason: string }>;
  logs_analysed?: number;
  saved_path?: string;
  error?: string;
}
