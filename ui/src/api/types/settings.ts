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
    cache_size: number;
    cache_ttl: number;
    tool_availability_ttl: number;
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
