export interface Plugin {
  name: string;
  version: string;
  description: string;
  category: string;
  endpoint: string;
  mcp_tool_name: string;
  effectiveness: number;
  enabled: boolean;
  plugin_type: string;
}

export interface ManifestPlugin extends Plugin {
  /** True when the plugin was successfully loaded at startup. */
  loaded: boolean;
  author: string;
  tags: string[];
  /** The plugin type key from plugins.yaml (e.g. "tools"). */
  type: string;
}

export interface PluginsListResponse {
  success: boolean;
  total: number;
  plugins: Plugin[];
}

export interface PluginsByCategoryResponse {
  success: boolean;
  categories: Record<string, Plugin[]>;
}

export interface PluginsManifestResponse {
  success: boolean;
  total: number;
  plugins: ManifestPlugin[];
}

export interface PluginToggleResponse {
  success: boolean;
  plugin: string;
  enabled: boolean;
  message: string;
  error?: string;
}

export interface ServerRestartResponse {
  success: boolean;
  message: string;
  error?: string;
}

