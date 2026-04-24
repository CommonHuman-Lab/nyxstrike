import type { Tool } from './tools';

export interface AttackChainStep {
  tool: string;
  parameters: Record<string, unknown>;
  expected_outcome?: string;
  success_probability?: number;
  execution_time_estimate?: number;
  dependencies?: string[];
  selection_reason?: {
    summary?: string;
    objective?: string;
    objective_match?: boolean;
    target_type?: string;
    target_type_match?: boolean;
    capabilities?: string[];
    covers_required?: string[];
    new_capabilities_added?: string[];
    noise_score?: number;
    effective_score?: number;
  };
}

export interface SessionFinding {
  finding_id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  description?: string;
  tool?: string;
  step_key?: string;
  evidence?: string;
  recommendation?: string;
  cve?: string;
  tags?: string[];
  status?: 'open' | 'confirmed' | 'false_positive' | 'resolved';
  created_at: number;
  updated_at: number;
}

export interface SessionEvent {
  type: string;
  message: string;
  timestamp: number;
  data?: Record<string, unknown>;
}

export interface SessionSummary {
  session_id: string;
  name?: string;
  description?: string;
  target: string;
  status?: string;
  total_findings: number;
  risk_level?: string;
  iterations: number;
  tools_executed: string[];
  workflow_steps?: AttackChainStep[];
  source?: string;
  objective?: string;
  metadata?: Record<string, unknown>;
  handover_history?: Array<{
    timestamp: string;
    session_id: string;
    category: string;
    confidence: number;
    note?: string;
  }>;
  findings?: SessionFinding[];
  event_log?: SessionEvent[];
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

export interface SessionDeleteResponse {
  success: boolean;
  deleted?: {
    active: boolean;
    completed: boolean;
  };
  session_id?: string;
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

export interface SessionTemplate {
  template_id: string;
  name: string;
  workflow_steps: AttackChainStep[];
  source_session_id?: string;
  created_at: number;
  updated_at: number;
}

export interface SessionTemplatesResponse {
  success: boolean;
  templates: SessionTemplate[];
  total: number;
  error?: string;
}

export interface SessionTemplateMutationResponse {
  success: boolean;
  template?: SessionTemplate;
  timestamp?: string;
  error?: string;
}

export interface SessionTemplateDeleteResponse {
  success: boolean;
  template_id?: string;
  timestamp?: string;
  error?: string;
}

export interface CreateSessionPayload {
  target: string;
  name?: string;
  description?: string;
  workflow_steps?: AttackChainStep[];
  source?: string;
  objective?: string;
  session_id?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateSessionFromTemplatePayload {
  target: string;
  template_id: string;
  source?: string;
  objective?: string;
  metadata?: Record<string, unknown>;
  session_id?: string;
}

export type UpdateSessionPayload = Partial<{
  name: string;
  description: string;
  target: string;
  status: string;
  total_findings: number;
  iterations: number;
  workflow_steps: AttackChainStep[];
  objective: string;
  source: string;
  metadata: Record<string, unknown>;
}>;

export interface CreateSessionTemplatePayload {
  name: string;
  workflow_steps: AttackChainStep[];
  source_session_id?: string;
}

export type UpdateSessionTemplatePayload = Partial<{
  name: string;
  workflow_steps: AttackChainStep[];
}>;

// ── Session Notes ──────────────────────────────────────────────────────────

export interface SessionNote {
  /** Note title without .md extension */
  filename: string;
  /** Sub-folder name (empty string = root) */
  folder: string;
  /** File size in bytes */
  size: number;
  /** Unix timestamp (seconds) of last modification */
  updated_at: number;
}

export interface SessionNotesResponse {
  success: boolean;
  notes: SessionNote[];
}

export interface SessionNoteContentResponse {
  success: boolean;
  filename: string;
  folder: string;
  content: string;
}

export interface SessionNoteMutationResponse {
  success: boolean;
  filename?: string;
  folder?: string;
  error?: string;
}

export interface SessionNoteConflictResponse {
  success: false;
  conflict: true;
  filename: string;
  folder: string;
}

export interface SessionNoteFoldersResponse {
  success: boolean;
  folders: string[];
}

export interface SessionNoteFolderMutationResponse {
  success: boolean;
  folder?: string;
  error?: string;
}

export interface SessionNoteSearchResult extends SessionNote {
  /** Context snippet around the first match (empty if match was on filename only) */
  snippet: string;
  /** True when the query matched the note filename */
  name_match: boolean;
}

export interface SessionNoteSearchResponse {
  success: boolean;
  query: string;
  results: SessionNoteSearchResult[];
}

// ── Session Findings ───────────────────────────────────────────────────────────

export interface SessionFindingsResponse {
  success: boolean;
  findings: SessionFinding[];
  total: number;
  error?: string;
}

export interface SessionFindingMutationResponse {
  success: boolean;
  finding?: SessionFinding;
  total_findings?: number;
  risk_level?: string;
  timestamp?: string;
  error?: string;
}

export interface SessionFindingDeleteResponse {
  success: boolean;
  finding_id?: string;
  total_findings?: number;
  risk_level?: string;
  timestamp?: string;
  error?: string;
}

export type CreateFindingPayload = {
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  description?: string;
  tool?: string;
  step_key?: string;
  evidence?: string;
  recommendation?: string;
  cve?: string;
  tags?: string[];
};

export type UpdateFindingPayload = Partial<CreateFindingPayload & { status: string }>;

// ── Session Reports ────────────────────────────────────────────────────────────

export interface SessionReportResponse {
  success: boolean;
  report?: string;
  session_id?: string;
  timestamp?: string;
  saved_path?: string;
  error?: string;
}

export interface SessionAiReportResponse extends SessionReportResponse {
  executive_summary?: string;
  ai_generated?: boolean;
}

export interface GenerateReportPayload {
  include_notes?: boolean;
  include_event_log?: boolean;
  download?: boolean;
  save_to_notes?: boolean;
}

export interface GenerateAiReportPayload extends GenerateReportPayload {
  focus?: string;
}
