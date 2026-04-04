export interface Tool {
  name: string;
  desc: string;
  category: string;
  endpoint: string;
  method: string;
  params: Record<string, { required?: boolean }>;
  optional: Record<string, string | number | boolean>;
  effectiveness: number;
  parent_tool?: string | null;
}

export interface ToolsCatalogResponse {
  success: boolean;
  total: number;
  categories: string[];
  tools: Tool[];
}

export interface ToolCategoriesResponse {
  categories: Record<string, string[]>;
}
