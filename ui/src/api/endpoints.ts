import { del, get, patch, post, postWithTimeout, stream } from './client';
import type {
  AttackChainStep,
  CacheStatsResponse,
  ClassifyTaskResponse,
  CreateAttackChainResponse,
  CreateSessionFromTemplatePayload,
  CreateSessionPayload,
  CreateSessionTemplatePayload,
  UpdateSessionTemplatePayload,
  PatchSettingsResponse,
  PatchWordlistsResponse,
  PoolStatsResponse,
  ProcessDashboardResponse,
  ProcessListResponse,
  RunHistoryResponse,
  SessionDeleteResponse,
  SessionDetailResponse,
  SessionHandoverResponse,
  SessionMutationResponse,
  SessionTemplateDeleteResponse,
  SessionTemplateMutationResponse,
  SessionTemplatesResponse,
  SessionsResponse,
  Settings,
  SettingsResponse,
  RefreshToolAvailabilityResponse,
  ToolCategoriesResponse,
  ToolExecResponse,
  ToolsCatalogResponse,
  UpdateSessionPayload,
  WebDashboardResponse,
  WordlistEntry,
} from './types';

type ProcessActionResponse = { success: boolean; message?: string; error?: string };

export const api = {
  dashboard: () => get<WebDashboardResponse>('/web-dashboard'),
  dashboardStream: (): EventSource => stream('/web-dashboard/stream'),

  tools: () => get<ToolsCatalogResponse>('/api/tools'),
  getToolCategories: () => get<ToolCategoriesResponse>('/api/tools/categories'),
  refreshToolAvailability: () => post<RefreshToolAvailabilityResponse>('/api/tools/availability/refresh'),

  getSettings: () => get<SettingsResponse>('/api/settings'),
  patchSettings: (runtime: Partial<Settings['runtime']>) =>
    patch<PatchSettingsResponse>('/api/settings', { runtime }),
  patchWordlists: (wordlists: WordlistEntry[]) =>
    patch<PatchWordlistsResponse>('/api/settings/wordlists', { wordlists }),

  logStream: (lines = 100): EventSource => stream('/api/logs/stream', { lines }),

  runHistory: (limit?: number) =>
    get<RunHistoryResponse>(`/api/runs/history${limit ? `?limit=${limit}` : ''}`),
  clearRunHistory: () => post<{ success: boolean }>('/api/runs/clear'),
  runTool: (endpoint: string, params: Record<string, unknown>) =>
    postWithTimeout<ToolExecResponse>(endpoint, params, 86400),

  processDashboard: () => get<ProcessDashboardResponse>('/api/processes/dashboard'),
  processList: () => get<ProcessListResponse>('/api/processes/list'),
  processDashboardStream: (): EventSource => stream('/api/processes/dashboard/stream'),
  processPoolStats: () => get<PoolStatsResponse>('/api/process/pool-stats'),
  processPoolStatsStream: (): EventSource => stream('/api/process/pool-stats/stream'),
  terminateProcess: (pid: number) => post<ProcessActionResponse>(`/api/processes/terminate/${pid}`),
  pauseProcess: (pid: number) => post<ProcessActionResponse>(`/api/processes/pause/${pid}`),
  resumeProcess: (pid: number) => post<ProcessActionResponse>(`/api/processes/resume/${pid}`),

  cacheStats: () => get<CacheStatsResponse>('/api/cache/stats'),
  clearCache: () => post<{ success: boolean; message: string }>('/api/cache/clear'),

  sessions: () => get<SessionsResponse>('/api/sessions'),
  sessionsStream: (): EventSource => stream('/api/sessions/stream'),
  session: (sessionId: string) => get<SessionDetailResponse>(`/api/sessions/${sessionId}`),
  createSession: (payload: CreateSessionPayload) =>
    post<SessionMutationResponse>('/api/sessions', payload),
  createSessionFromTemplate: (payload: CreateSessionFromTemplatePayload) =>
    post<SessionMutationResponse>('/api/sessions/from-template', payload),
  updateSession: (sessionId: string, payload: UpdateSessionPayload) =>
    patch<SessionMutationResponse>(`/api/sessions/${sessionId}`, payload),
  deleteSession: (sessionId: string) => del<SessionDeleteResponse>(`/api/sessions/${sessionId}`),
  handoverSession: (sessionId: string, note = '') =>
    post<SessionHandoverResponse>(`/api/sessions/${sessionId}/handover`, { note }),

  sessionTemplates: () => get<SessionTemplatesResponse>('/api/sessions/templates'),
  sessionTemplatesCompat: () => get<SessionTemplatesResponse>('/api/session-templates'),
  createSessionTemplate: (payload: CreateSessionTemplatePayload) =>
    post<SessionTemplateMutationResponse>('/api/sessions/templates', payload),
  createSessionTemplateCompat: (payload: CreateSessionTemplatePayload) =>
    post<SessionTemplateMutationResponse>('/api/session-templates', payload),
  updateSessionTemplate: (templateId: string, payload: UpdateSessionTemplatePayload) =>
    patch<SessionTemplateMutationResponse>(`/api/sessions/templates/${templateId}`, payload),
  deleteSessionTemplate: (templateId: string) =>
    del<SessionTemplateDeleteResponse>(`/api/sessions/templates/${templateId}`),

  createAttackChain: (target: string, objective = 'comprehensive') =>
    post<CreateAttackChainResponse>('/api/intelligence/create-attack-chain', { target, objective }),
  previewAttackChain: (target: string, objective = 'comprehensive') =>
    post<CreateAttackChainResponse>('/api/intelligence/preview-attack-chain', { target, objective }),
  aiReconSession: (target: string) =>
    post<{ success: boolean; steps: AttackChainStep[]; session_name: string; error?: string }>(
      '/api/intelligence/ai-recon-session',
      { target },
    ),
  classifyTask: (description: string) =>
    post<ClassifyTaskResponse>('/api/intelligence/classify-task', { description }),
};
