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

export interface PluginsListResponse {
  success: boolean;
  total: number;
  plugins: Plugin[];
}

export interface PluginsByCategoryResponse {
  success: boolean;
  categories: Record<string, Plugin[]>;
}
