import type { AttackChainStep, SessionSummary, Tool } from '../../api'

export function normalizeStepsFromSession(session: SessionSummary): AttackChainStep[] {
  if (Array.isArray(session.workflow_steps) && session.workflow_steps.length > 0) return session.workflow_steps
  return session.tools_executed.map(tool => ({ tool, parameters: {} }))
}

function normalizeToken(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, '')
}

export function resolveToolForStep(stepTool: string, tools: Tool[]): Tool | null {
  const step = stepTool.trim()
  if (!step) return null

  const directByName = tools.find(t => t.name === step)
  if (directByName) return directByName

  const directByEndpoint = tools.find(t => t.endpoint === step)
  if (directByEndpoint) return directByEndpoint

  const directByParent = tools.find(t => t.parent_tool === step)
  if (directByParent) return directByParent

  const normalizedStep = normalizeToken(step)
  let best: { tool: Tool; score: number } | null = null

  for (const tool of tools) {
    const name = normalizeToken(tool.name)
    const parent = normalizeToken(tool.parent_tool ?? '')
    const endpoint = normalizeToken(tool.endpoint)
    let score = 0

    if (name === normalizedStep) score = Math.max(score, 80)
    if (parent === normalizedStep) score = Math.max(score, 75)
    if (endpoint === normalizedStep) score = Math.max(score, 70)
    if (name.includes(normalizedStep)) score = Math.max(score, 62)
    if (endpoint.includes(normalizedStep)) score = Math.max(score, 58)
    if (parent && parent.includes(normalizedStep)) score = Math.max(score, 56)
    if (normalizedStep.includes(name)) score = Math.max(score, 52)
    if (score === 0) continue

    if (!best || score > best.score) best = { tool, score }
  }

  return best?.tool ?? null
}

export type StepState = 'idle' | 'success' | 'failed'

export type PersistedStepResult = {
  success: boolean
  return_code: number
  execution_time: number
  timestamp?: string
  stdout?: string
  stderr?: string
}
