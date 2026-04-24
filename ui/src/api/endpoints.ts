import { del, get, patch, post, postFormData, postWithTimeout, put, stream } from './client';
import type {
  AttackChainStep,
  AnalyzeSessionResponse,
  CacheStatsResponse,
  ChatSessionsResponse,
  ChatSessionResponse,
  ChatMessagesResponse,
  ClassifyTaskResponse,
  CreateAttackChainResponse,
  CreateFindingPayload,
  CreateSessionFromTemplatePayload,
  CreateSessionPayload,
  CreateSessionTemplatePayload,
  FollowUpSessionResponse,
  GenerateAiReportPayload,
  GenerateReportPayload,
  UpdateFindingPayload,
  UpdateSessionTemplatePayload,
  LlmSessionsResponse,
  LlmSessionDetailResponse,
  PatchSettingsResponse,
  PatchWordlistsResponse,
  PoolStatsResponse,
  ProcessDashboardResponse,
  ProcessListResponse,
  RunHistoryResponse,
  RunHistorySummaryResponse,
  SessionAiReportResponse,
  SessionDeleteResponse,
  SessionDetailResponse,
  SessionFindingDeleteResponse,
  SessionFindingMutationResponse,
  SessionFindingsResponse,
  SessionHandoverResponse,
  SessionMutationResponse,
  SessionNoteConflictResponse,
  SessionNoteContentResponse,
  SessionNoteFolderMutationResponse,
  SessionNoteFoldersResponse,
  SessionNoteMutationResponse,
  SessionNoteSearchResponse,
  SessionNotesResponse,
  SessionReportResponse,
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
  PluginsByCategoryResponse,
  PluginsListResponse,
} from './types';

type ProcessActionResponse = { success: boolean; message?: string; error?: string };

export const api = {
  dashboard: () => get<WebDashboardResponse>('/web-dashboard'),
  dashboardStream: (): EventSource => stream('/web-dashboard/stream'),
  /** Dedicated resource-only SSE stream — connect only on pages that display System Resources. */
  resourcesStream: (): EventSource => stream('/api/system/resources/stream'),

  tools: () => get<ToolsCatalogResponse>('/api/tools'),
  getToolCategories: () => get<ToolCategoriesResponse>('/api/tools/categories'),
  refreshToolAvailability: () => post<RefreshToolAvailabilityResponse>('/api/tools/availability/refresh'),

  pluginList: () => get<PluginsListResponse>('/api/plugins/list'),
  pluginsByCategory: () => get<PluginsByCategoryResponse>('/api/plugins/by-category'),

  getSettings: () => get<SettingsResponse>('/api/settings'),
  patchSettings: (runtime: Partial<Settings['runtime']>, chat?: Partial<Settings['chat']>) =>
    patch<PatchSettingsResponse>('/api/settings', { runtime, ...(chat ? { chat } : {}) }),
  patchWordlists: (wordlists: WordlistEntry[]) =>
    patch<PatchWordlistsResponse>('/api/settings/wordlists', { wordlists }),

  logStream: (lines = 100): EventSource => stream('/api/logs/stream', { lines }),

  runHistory: (limit?: number) =>
    get<RunHistoryResponse>(`/api/runs/history${limit ? `?limit=${limit}` : ''}`),
  /** Lightweight fetch — id, tool, timestamp, success, execution_time only (no stdout/stderr/params). */
  runHistorySummary: (limit?: number) =>
    get<RunHistorySummaryResponse>(`/api/runs/history/summary${limit ? `?limit=${limit}` : ''}`),
  clearRunHistory: () => post<{ success: boolean }>('/api/runs/clear'),
  runTool: (endpoint: string, params: Record<string, unknown>) =>
    postWithTimeout<ToolExecResponse>(endpoint, params, 86400),

  processDashboard: () => get<ProcessDashboardResponse>('/api/processes/dashboard'),
  processList: () => get<ProcessListResponse>('/api/processes/list'),
  processDashboardStream: (): EventSource => stream('/api/processes/dashboard/stream'),
  processPoolStats: () => get<PoolStatsResponse>('/api/process/pool-stats'),
  processPoolStatsStream: (): EventSource => stream('/api/process/pool-stats/stream'),
  /** Unified SSE stream: process list + pool stats + system load in one connection. */
  processesStream: (): EventSource => stream('/api/processes/stream'),
  terminateProcess: (pid: number) => post<ProcessActionResponse>(`/api/processes/terminate/${pid}`),
  pauseProcess: (pid: number) => post<ProcessActionResponse>(`/api/processes/pause/${pid}`),
  resumeProcess: (pid: number) => post<ProcessActionResponse>(`/api/processes/resume/${pid}`),
  cancelAiTask: (taskId: string) => post<ProcessActionResponse>(`/api/processes/cancel-ai-task/${taskId}`),

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

  // ── Session Notes ────────────────────────────────────────────────────────
  sessionNotes: (sessionId: string) =>
    get<SessionNotesResponse>(`/api/sessions/${sessionId}/notes`),
  sessionNote: (sessionId: string, name: string, folder = '') =>
    get<SessionNoteContentResponse>(
      `/api/sessions/${sessionId}/notes/${name}${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`
    ),
  createSessionNote: (sessionId: string, filename: string, content: string, folder = '') =>
    post<SessionNoteMutationResponse>(`/api/sessions/${sessionId}/notes`, { filename, content, folder }),
  updateSessionNote: (sessionId: string, name: string, content: string, folder = '') =>
    put<SessionNoteMutationResponse>(
      `/api/sessions/${sessionId}/notes/${name}${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`,
      { content }
    ),
  deleteSessionNote: (sessionId: string, name: string, folder = '') =>
    del<SessionNoteMutationResponse>(
      `/api/sessions/${sessionId}/notes/${name}${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`
    ),
  uploadSessionNote: (sessionId: string, name: string, file: File, overwrite = false, folder = '') => {
    const form = new FormData();
    form.append('file', file);
    const params = new URLSearchParams();
    if (overwrite) params.set('overwrite', '1');
    if (folder) params.set('folder', folder);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return postFormData<SessionNoteMutationResponse | SessionNoteConflictResponse>(
      `/api/sessions/${sessionId}/notes/${name}/upload${qs}`,
      form,
    );
  },

  // ── Session Note Folders ─────────────────────────────────────────────────
  sessionNoteFolders: (sessionId: string) =>
    get<SessionNoteFoldersResponse>(`/api/sessions/${sessionId}/notes/folders`),
  createSessionNoteFolder: (sessionId: string, name: string) =>
    post<SessionNoteFolderMutationResponse>(`/api/sessions/${sessionId}/notes/folders`, { name }),
  deleteSessionNoteFolder: (sessionId: string, folder: string) =>
    del<SessionNoteFolderMutationResponse>(`/api/sessions/${sessionId}/notes/folders/${encodeURIComponent(folder)}`),
  renameSessionNoteFolder: (sessionId: string, folder: string, newName: string) =>
    patch<SessionNoteFolderMutationResponse>(`/api/sessions/${sessionId}/notes/folders/${encodeURIComponent(folder)}`, { new_name: newName }),
  searchSessionNotes: (sessionId: string, q: string) =>
    get<SessionNoteSearchResponse>(`/api/sessions/${sessionId}/notes/search?q=${encodeURIComponent(q)}`),

  createAttackChain: (target: string, objective = 'comprehensive') =>
    post<CreateAttackChainResponse>('/api/intelligence/create-attack-chain', { target, objective }),
  previewAttackChain: (target: string, objective = 'comprehensive') =>
    post<CreateAttackChainResponse>('/api/intelligence/preview-attack-chain', { target, objective }),
  aiReconSession: (target: string) =>
    post<{ success: boolean; steps: AttackChainStep[]; session_name: string; error?: string }>(
      '/api/intelligence/ai-recon-session',
      { target },
    ),
  aiProfilingSession: (target: string) =>
    post<{ success: boolean; steps: AttackChainStep[]; session_name: string; target_type: string; error?: string }>(
      '/api/intelligence/ai-profiling-session',
      { target },
    ),
  aiVulnSession: (target: string) =>
    post<{ success: boolean; steps: AttackChainStep[]; session_name: string; error?: string }>(
      '/api/intelligence/ai-vuln-session',
      { target },
    ),
  aiOsintSession: (target: string) =>
    post<{ success: boolean; steps: AttackChainStep[]; session_name: string; error?: string }>(
      '/api/intelligence/ai-osint-session',
      { target },
    ),
  classifyTask: (description: string) =>
    post<ClassifyTaskResponse>('/api/intelligence/classify-task', { description }),
  llmSessions: (limit = 50) =>
    get<LlmSessionsResponse>(`/api/intelligence/llm-agent-sessions?limit=${limit}`),
  llmSessionDetail: (llmSessionId: string) =>
    get<LlmSessionDetailResponse>(`/api/intelligence/llm-agent-scan/${llmSessionId}`),
  analyzeSession: (sessionId: string) =>
    post<AnalyzeSessionResponse>('/api/intelligence/analyze-session', {
      session_id: sessionId,
      save_to_notes: true,
    }),
  followUpSession: (sessionId: string) =>
    post<FollowUpSessionResponse>('/api/intelligence/follow-up-session', {
      session_id: sessionId,
      save_to_notes: true,
    }),

  // ── Session Findings ─────────────────────────────────────────────────────
  sessionFindings: (sessionId: string) =>
    get<SessionFindingsResponse>(`/api/sessions/${sessionId}/findings`),
  addSessionFinding: (sessionId: string, payload: CreateFindingPayload) =>
    post<SessionFindingMutationResponse>(`/api/sessions/${sessionId}/findings`, payload),
  updateSessionFinding: (sessionId: string, findingId: string, payload: UpdateFindingPayload) =>
    patch<SessionFindingMutationResponse>(`/api/sessions/${sessionId}/findings/${findingId}`, payload),
  deleteSessionFinding: (sessionId: string, findingId: string) =>
    del<SessionFindingDeleteResponse>(`/api/sessions/${sessionId}/findings/${findingId}`),

  // ── Session Reports ──────────────────────────────────────────────────────
  generateSessionReport: (sessionId: string, options: GenerateReportPayload = {}) =>
    post<SessionReportResponse>(`/api/sessions/${sessionId}/report`, options),
  generateSessionAiReport: (sessionId: string, options: GenerateAiReportPayload = {}) =>
    post<SessionAiReportResponse>(`/api/sessions/${sessionId}/report/ai`, options),
  /** Returns the URL to trigger a notes zip download in the browser */
  exportSessionNotesUrl: (sessionId: string) => `/api/sessions/${sessionId}/notes/export`,

  // ── Chat Widget ──────────────────────────────────────────────────────────
  chat: {
    listSessions: () => get<ChatSessionsResponse>('/api/chat/sessions'),
    createSession: () => post<ChatSessionResponse>('/api/chat/sessions'),
    deleteSession: (chatSessionId: string) => del<{ success: boolean }>(`/api/chat/sessions/${chatSessionId}`),
    renameSession: (chatSessionId: string, name: string) => patch<{ success: boolean }>(`/api/chat/sessions/${chatSessionId}`, { name }),
    getMessages: (chatSessionId: string) => get<ChatMessagesResponse>(`/api/chat/sessions/${chatSessionId}/messages`),
  },
};
