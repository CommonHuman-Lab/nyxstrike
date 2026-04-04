import type { Tool } from '../api';

export function getToolsStatusWithParents(
  tools: Tool[],
  toolsStatus: Record<string, boolean>
): Record<string, boolean> {
  const result = { ...toolsStatus };

  for (const tool of tools) {
    if (tool.parent_tool && toolsStatus[tool.parent_tool] && !(tool.name in result)) {
      result[tool.name] = true;
    }
  }

  return result;
}
