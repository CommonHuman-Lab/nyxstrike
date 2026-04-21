export interface PersonalityPreset {
  id: string;
  label: string;
  prompt: string;
}

export interface WordlistEntry {
  name: string;
  path: string;
  type: string;
  speed: string;
  coverage: string;
  is_default?: boolean;
}

export interface Settings {
  server: {
    host: string;
    port: number;
    auth_enabled: boolean;
    debug_mode: boolean;
    working_dir: string;
    data_dir: string;
  };
  runtime: {
    command_timeout: number;
    request_timeout: number;
    command_inactivity_timeout: number;
    command_max_runtime: number;
    cache_size: number;
    cache_ttl: number;
    tool_availability_ttl: number;
  };
  chat: {
    personality: string;
    system_prompt: string;
    custom_prompt: string;
    summarization_threshold: number;
    context_injection_chars: number;
    personality_presets: PersonalityPreset[];
  };
  wordlists: WordlistEntry[];
}

export interface SettingsResponse {
  success: boolean;
  settings: Settings;
}

export interface PatchSettingsResponse {
  success: boolean;
  updated: Record<string, number>;
  settings?: Settings;
  errors?: Record<string, string>;
  error?: string;
}

export interface PatchWordlistsResponse {
  success: boolean;
  updated: Record<string, number>;
  wordlists?: WordlistEntry[];
  errors?: Record<string, string>;
  error?: string;
}
