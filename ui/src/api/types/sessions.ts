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
  metadata?: Record<string, unknown>;
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
