import type { AttackChainStep, SessionSummary, Tool, ToolExecResponse } from '../../api'

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

export type StepState = 'idle' | 'running' | 'success' | 'failed'

export type PersistedStepResult = {
  success: boolean
  return_code: number
  execution_time: number
  timestamp?: string
  stdout?: string
  stderr?: string
}

export type StepArtifacts = {
  urls: string[]
  domains: string[]
  subdomains: string[]
  ips: string[]
  live_hosts: string[]
  endpoints: string[]
  open_ports: string[]
}

export type ChainSuggestionField = {
  param: string
  value: string
  sourceArtifact: keyof StepArtifacts | 'params'
  sourceTool: string
  confidence: number
  reason: string
}

export type ChainSuggestion = {
  sourceTool: string
  summary: string
  confidence: number
  fields: ChainSuggestionField[]
}

export type ChainMappingPreference = {
  targetTool: string
  param: string
  sourceTool?: string
  sourceArtifact: keyof StepArtifacts | 'params'
}

const URL_RE = /https?:\/\/[^\s"'<>]+/gi
const IPV4_RE = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g
const DOMAIN_RE = /\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b/gi
const HOST_PORT_RE = /\b(?:[a-z0-9.-]+|(?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})\b/gi

function emptyArtifacts(): StepArtifacts {
  return {
    urls: [],
    domains: [],
    subdomains: [],
    ips: [],
    live_hosts: [],
    endpoints: [],
    open_ports: [],
  }
}

function pushUnique(arr: string[], value: string): void {
  const clean = value.trim()
  if (!clean) return
  if (!arr.includes(clean)) arr.push(clean)
}

function isLikelyIp(value: string): boolean {
  const parts = value.split('.')
  if (parts.length !== 4) return false
  return parts.every(p => {
    if (!/^\d+$/.test(p)) return false
    const n = Number(p)
    return n >= 0 && n <= 255
  })
}

function hostFromUrl(url: string): string | null {
  try {
    return new URL(url).hostname.toLowerCase()
  } catch {
    return null
  }
}

function rootDomain(hostname: string): string {
  const parts = hostname.toLowerCase().split('.').filter(Boolean)
  if (parts.length <= 2) return hostname.toLowerCase()
  const tail = parts.slice(-3).join('.')
  if (tail.endsWith('.co.uk') || tail.endsWith('.com.au')) return parts.slice(-3).join('.')
  return parts.slice(-2).join('.')
}

function collectStrings(node: unknown, out: string[], depth = 0): void {
  if (depth > 4) return
  if (typeof node === 'string') {
    out.push(node)
    return
  }
  if (Array.isArray(node)) {
    for (const value of node.slice(0, 400)) collectStrings(value, out, depth + 1)
    return
  }
  if (node && typeof node === 'object') {
    for (const value of Object.values(node as Record<string, unknown>)) collectStrings(value, out, depth + 1)
  }
}

function normalizeTargetHost(target: string): string | null {
  const t = target.trim()
  if (!t) return null
  if (t.startsWith('http://') || t.startsWith('https://')) {
    try {
      return new URL(t).hostname.toLowerCase()
    } catch {
      return null
    }
  }
  return t.replace(/^\.+/, '').toLowerCase()
}

function firstParam(params: Record<string, unknown>, keys: string[]): string | undefined {
  for (const key of keys) {
    const v = params[key]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return undefined
}

function targetToUrl(value: string): string {
  const clean = value.trim()
  if (clean.startsWith('http://') || clean.startsWith('https://')) return clean
  return `https://${clean}`
}

export function extractStepArtifacts({
  step,
  result,
  target,
}: {
  step: AttackChainStep
  result: ToolExecResponse
  target: string
}): StepArtifacts {
  const artifacts = emptyArtifacts()
  const params = (step.parameters ?? {}) as Record<string, unknown>
  const text = result.stdout ?? ''
  const parsedStrings: string[] = []

  try {
    const parsed = JSON.parse(text)
    collectStrings(parsed, parsedStrings)
  } catch {
    // ignore non-JSON output
  }

  const corpus = [text, ...parsedStrings].join('\n')

  for (const m of corpus.match(URL_RE) ?? []) {
    pushUnique(artifacts.urls, m)
    const host = hostFromUrl(m)
    if (host) {
      pushUnique(artifacts.domains, host)
      pushUnique(artifacts.live_hosts, host)
      pushUnique(artifacts.endpoints, m)
    }
  }

  for (const m of corpus.match(DOMAIN_RE) ?? []) {
    const d = m.toLowerCase()
    if (!isLikelyIp(d)) {
      pushUnique(artifacts.domains, d)
      pushUnique(artifacts.live_hosts, d)
    }
  }

  for (const m of corpus.match(IPV4_RE) ?? []) {
    if (isLikelyIp(m)) {
      pushUnique(artifacts.ips, m)
      pushUnique(artifacts.live_hosts, m)
    }
  }

  const targetHost = normalizeTargetHost(target)
  const root = targetHost ? rootDomain(targetHost) : null
  if (root) {
    for (const domain of artifacts.domains) {
      if (domain.endsWith(`.${root}`) && domain !== root) pushUnique(artifacts.subdomains, domain)
    }
  }

  const explicitDomain = firstParam(params, ['domain'])
  if (explicitDomain) pushUnique(artifacts.domains, explicitDomain.toLowerCase())
  const explicitUrl = firstParam(params, ['url', 'endpoint'])
  if (explicitUrl) pushUnique(artifacts.urls, explicitUrl)
  const explicitTarget = firstParam(params, ['target', 'host', 'query'])
  if (explicitTarget) {
    if (isLikelyIp(explicitTarget)) pushUnique(artifacts.ips, explicitTarget)
    else pushUnique(artifacts.domains, explicitTarget.toLowerCase())
  }

  for (const m of corpus.match(HOST_PORT_RE) ?? []) {
    const port = m.split(':').pop()
    if (port) pushUnique(artifacts.open_ports, port)
  }

  return artifacts
}

type PriorStepContext = {
  index: number
  step: AttackChainStep
  artifacts: StepArtifacts
  params: Record<string, unknown>
}

function preferredSourceOrder(toolName: string, param: string): Array<keyof StepArtifacts | 'params'> {
  const t = toolName.toLowerCase()
  const p = param.toLowerCase()

  if (p === 'list_file') return ['subdomains', 'domains', 'live_hosts', 'urls']
  if (['domain', 'dns_name'].includes(p)) return ['subdomains', 'domains', 'params']
  if (['url', 'endpoint'].includes(p)) return ['endpoints', 'urls', 'domains', 'params']
  if (['target', 'host', 'query', 'hostname'].includes(p)) return ['live_hosts', 'domains', 'ips', 'urls', 'params']

  if (t.includes('httpx') || t.includes('gospider') || t.includes('hakrawler')) {
    return ['live_hosts', 'urls', 'domains', 'params']
  }
  if (t.includes('shuffledns') || t.includes('dns')) {
    return ['subdomains', 'domains', 'params']
  }
  return ['live_hosts', 'domains', 'urls', 'ips', 'params']
}

function candidateValueFor(source: keyof StepArtifacts | 'params', ctx: PriorStepContext, param: string, fallbackTarget: string): string | null {
  const p = param.toLowerCase()
  if (source === 'params') {
    return firstParam(ctx.params, [p, 'target', 'host', 'url', 'domain']) ?? null
  }
  const values = ctx.artifacts[source]
  if (!values || values.length === 0) return null

  if (p === 'domain') {
    const picked = values.find(v => !isLikelyIp(v)) ?? values[0]
    return picked ? rootDomain(picked) : null
  }
  if (['url', 'endpoint'].includes(p)) {
    const picked = values.find(v => v.startsWith('http://') || v.startsWith('https://'))
      ?? values.find(v => !isLikelyIp(v))
      ?? values[0]
    if (!picked) return null
    if (picked.startsWith('http://') || picked.startsWith('https://')) return picked
    return targetToUrl(picked)
  }
  if (['target', 'host', 'query', 'hostname'].includes(p)) {
    const picked = values[0] ?? fallbackTarget
    return picked || null
  }
  return values[0] ?? null
}

function confidenceFor({
  source,
  age,
  tool,
  param,
}: {
  source: keyof StepArtifacts | 'params'
  age: number
  tool: string
  param: string
}): number {
  let score = 0.45
  if (source === 'params') score += 0.08
  if (['subdomains', 'endpoints', 'live_hosts'].includes(source)) score += 0.2
  if (age <= 1) score += 0.2
  else if (age <= 3) score += 0.1

  const t = tool.toLowerCase()
  const p = param.toLowerCase()
  if ((t.includes('shuffledns') || t.includes('dns')) && p === 'domain') score += 0.08
  if ((t.includes('httpx') || t.includes('gospider')) && (p === 'url' || p === 'target')) score += 0.08

  return Math.max(0.1, Math.min(0.99, score))
}

export function buildStepChainSuggestion({
  steps,
  selectedStepIndex,
  selectedTool,
  sessionId,
  target,
  stepResults,
  stepArtifacts,
  currentValues,
  preferences,
}: {
  steps: AttackChainStep[]
  selectedStepIndex: number
  selectedTool: Tool
  sessionId: string
  target: string
  stepResults: Record<string, { result?: ToolExecResponse; error?: string }>
  stepArtifacts: Record<string, StepArtifacts>
  currentValues: Record<string, string>
  preferences?: ChainMappingPreference[]
}): ChainSuggestion | null {
  const paramNames = [...Object.keys(selectedTool.params), ...Object.keys(selectedTool.optional)]
  const missingParams = paramNames.filter(name => !currentValues[name]?.trim())
  if (missingParams.length === 0) return null

  const prior: PriorStepContext[] = []
  for (let i = selectedStepIndex - 1; i >= 0; i -= 1) {
    const step = steps[i]
    const key = `${sessionId}:${i}`
    const result = stepResults[key]?.result
    if (!result?.success) continue
    const artifacts = stepArtifacts[key] ?? extractStepArtifacts({ step, result, target })
    prior.push({
      index: i,
      step,
      artifacts,
      params: (step.parameters ?? {}) as Record<string, unknown>,
    })
  }
  if (prior.length === 0) return null

  const fields: ChainSuggestionField[] = []
  const prefs = preferences ?? []

  for (const param of missingParams) {
    const sources = preferredSourceOrder(selectedTool.name, param)
    let chosen: ChainSuggestionField | null = null

    for (const source of sources) {
      for (const ctx of prior) {
        const candidate = candidateValueFor(source, ctx, param, target)
        if (!candidate) continue
        const age = selectedStepIndex - ctx.index
        let confidence = confidenceFor({ source, age, tool: selectedTool.name, param })
        const pref = prefs.find(p =>
          p.targetTool === selectedTool.name
          && p.param === param
          && p.sourceArtifact === source
          && (!p.sourceTool || p.sourceTool === ctx.step.tool)
        )
        if (pref) confidence = Math.min(0.99, confidence + 0.22)
        const field: ChainSuggestionField = {
          param,
          value: candidate,
          sourceArtifact: source,
          sourceTool: ctx.step.tool,
          confidence,
          reason: `From ${ctx.step.tool} (${source})`,
        }
        if (!chosen || field.confidence > chosen.confidence) chosen = field
      }
    }

    if (chosen) fields.push(chosen)
  }

  if (fields.length === 0) return null

  const top = prior[0]
  const confidence = fields.reduce((sum, f) => sum + f.confidence, 0) / fields.length
  return {
    sourceTool: top.step.tool,
    summary: `Prepared ${fields.length} mapped value${fields.length === 1 ? '' : 's'} from previous successful tool outputs.`,
    confidence,
    fields,
  }
}
