import type { Tool, AttackChainStep } from '../../api'

export function inferTargetValue(paramName: string, target: string, sessionId?: string): string | undefined {
  const k = paramName.toLowerCase()
  if (k === 'session_id' && sessionId) return sessionId
  if (k === 'target' || k === 'host' || k === 'query') return target
  if (k === 'url' || k === 'endpoint') {
    if (target.startsWith('http://') || target.startsWith('https://')) return target
    return `https://${target}`
  }
  if (k === 'domain') {
    return target.replace(/^https?:\/\//, '').replace(/\/.*/, '')
  }
  return undefined
}

export function buildInitialFieldValues(tool: Tool, step: AttackChainStep, target: string, sessionId?: string): Record<string, string> {
  const out: Record<string, string> = {}
  const stepParams = (step.parameters ?? {}) as Record<string, unknown>
  for (const k of Object.keys(tool.params)) {
    const existing = stepParams[k]
    if (existing !== undefined && existing !== null && String(existing).trim() !== '') {
      out[k] = String(existing)
      continue
    }
    out[k] = inferTargetValue(k, target, sessionId) ?? ''
  }
  for (const [k, v] of Object.entries(tool.optional)) {
    const existing = stepParams[k]
    out[k] = existing !== undefined && existing !== null ? String(existing) : String(v)
  }
  return out
}

export function buildRunPayload(tool: Tool, fieldValues: Record<string, string>): {
  payload: Record<string, unknown>
  missing: string[]
} {
  const required = Object.keys(tool.params)
  const missing = required.filter(k => !fieldValues[k]?.trim())
  const payload: Record<string, unknown> = {}
  if (missing.length > 0) return { payload, missing }

  for (const k of required) payload[k] = fieldValues[k].trim()
  for (const k of Object.keys(tool.optional)) {
    const v = fieldValues[k]
    if (v !== undefined && v !== '') payload[k] = v
  }
  return { payload, missing }
}
