export interface ChatSession {
  id: string;
  name: string;
  summary: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionsResponse {
  success: boolean;
  sessions: ChatSession[];
}

export interface ChatSessionResponse {
  success: boolean;
  session: ChatSession;
}

export interface ChatMessageItem {
  id: number;
  chat_session_id: string;
  role: 'user' | 'assistant';
  content: string;
  stats?: string | null;
  is_summarized: boolean;
  created_at: string;
}

export interface ChatMessagesResponse {
  success: boolean;
  messages: ChatMessageItem[];
  session: ChatSession;
}

export interface ToolConfirmRequest {
  approved: boolean;
}

export interface ToolCallPending {
  tool_name: string;
  arguments: Record<string, unknown>;
  description: string;
}
