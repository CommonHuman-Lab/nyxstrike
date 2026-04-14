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

export function normalizePersistedResults(raw: unknown): PersistedStepResult[] {
  if (Array.isArray(raw)) return raw.filter(v => v && typeof v === 'object') as PersistedStepResult[]
  if (raw && typeof raw === 'object') return [raw as PersistedStepResult]
  return []
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
const PORT_PROTO_RE = /\b(\d{1,5})\/(?:tcp|udp)\b/gi
const NMAP_REPORT_RE = /Nmap\s+scan\s+report\s+for\s+(.+)$/gim

const IGNORE_CHAIN_HOSTS = new Set([
  'nmap.org',
  'github.com',
  'raw.githubusercontent.com',
  'localhost',
  'localdomain',
])

const FILELIKE_TLDS = new Set([
  'toml',
  'json',
  'yaml',
  'yml',
  'ini',
  'conf',
  'cfg',
  'txt',
  'log',
  'md',
  'xml',
  'csv',
])

const NEVER_CHAIN_PARAMS = new Set([
  'additional_args',
  'args',
  'flags',
  'flag',
  'password',
  'pass',
  'passwd',
  'pwd',
  'token',
  'api_key',
  'apikey',
  'secret',
  'auth',
  'authorization',
  'cookie',
  'headers',
  'header',
  'body',
  'data',
])

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

function parseValidPort(raw: string): string | null {
  const value = raw.trim()
  if (!/^\d{1,5}$/.test(value)) return null
  if (value.length > 1 && value.startsWith('0')) return null
  const n = Number(value)
  if (!Number.isInteger(n) || n < 1 || n > 65535) return null
  return String(n)
}

function shouldIgnoreHostForChaining(host: string): boolean {
  const clean = host.trim().toLowerCase()
  if (!clean) return true
  if (IGNORE_CHAIN_HOSTS.has(clean)) return true
  if (clean.endsWith('.localdomain')) return true
  const parts = clean.split('.').filter(Boolean)
  if (parts.length >= 2) {
    const tld = parts[parts.length - 1]
    if (FILELIKE_TLDS.has(tld)) return true
  }
  return false
}

function isLikelyHostToken(value: string): boolean {
  const v = value.trim().toLowerCase()
  if (!v) return false
  if (v.includes(' ')) return false
  if (v.includes('[') || v.includes(']') || v.includes('(') || v.includes(')')) return false
  if (isLikelyIp(v)) return true
  if (!/^[a-z0-9.-]+$/.test(v)) return false
  if (!v.includes('.')) return false
  return true
}

function cleanPotentialHostToken(value: string): string {
  const trimmed = value.trim().toLowerCase()
  return trimmed.replace(/^['"\[\(]+/, '').replace(/[\]'"\),;:]+$/, '')
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

function looksLikeCredentialParam(param: string): boolean {
  const p = param.toLowerCase()
  return (
    p.includes('password')
    || p.includes('passwd')
    || p.includes('token')
    || p.includes('secret')
    || p.includes('apikey')
    || p.includes('api_key')
    || p.includes('auth')
    || p === 'username'
    || p === 'user'
  )
}

function isPortParam(param: string): boolean {
  const p = param.toLowerCase()
  return p === 'port' || p === 'ports' || p.endsWith('_port') || p.endsWith('_ports')
}

function isDomainParam(param: string): boolean {
  const p = param.toLowerCase()
  return p === 'domain' || p === 'dns_name' || p === 'root_domain'
}

function isUrlParam(param: string): boolean {
  const p = param.toLowerCase()
  return p === 'url' || p === 'endpoint' || p.endsWith('_url') || p.endsWith('_endpoint')
}

function isHostParam(param: string): boolean {
  const p = param.toLowerCase()
  return p === 'target' || p === 'host' || p === 'hostname' || p === 'query' || p === 'rhost' || p === 'lhost'
}

function shouldSuggestParam(param: string): boolean {
  const p = param.toLowerCase()
  if (NEVER_CHAIN_PARAMS.has(p)) return false
  if (looksLikeCredentialParam(p)) return false
  return isDomainParam(p) || isUrlParam(p) || isHostParam(p) || isPortParam(p) || p === 'list_file'
}

function normalizeComparableValue(param: string, value: string): string {
  const p = param.toLowerCase()
  const v = value.trim()
  if (!v) return ''
  if (isHostParam(p) || isDomainParam(p)) return v.toLowerCase()
  if (isUrlParam(p)) return v.replace(/\/+$/, '').toLowerCase()
  if (isPortParam(p)) return v.replace(/\s+/g, '')
  return v
}

function isSameFieldValue(param: string, a: string, b: string): boolean {
  return normalizeComparableValue(param, a) === normalizeComparableValue(param, b)
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
      if (shouldIgnoreHostForChaining(host)) continue
      pushUnique(artifacts.domains, host)
      pushUnique(artifacts.live_hosts, host)
      pushUnique(artifacts.endpoints, m)
    }
  }

  for (const m of corpus.match(DOMAIN_RE) ?? []) {
    const d = cleanPotentialHostToken(m)
    if (!isLikelyHostToken(d) || shouldIgnoreHostForChaining(d)) continue
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

  // Prefer explicit scan target evidence from Nmap output.
  for (const line of corpus.match(NMAP_REPORT_RE) ?? []) {
    const report = line.replace(/^Nmap\s+scan\s+report\s+for\s+/i, '').trim()
    const ipInParens = report.match(/\((\d{1,3}(?:\.\d{1,3}){3})\)/)
    if (ipInParens?.[1] && isLikelyIp(ipInParens[1])) {
      pushUnique(artifacts.ips, ipInParens[1])
      pushUnique(artifacts.live_hosts, ipInParens[1])
    }

    // Handle both forms:
    // - Nmap scan report for host.name (1.2.3.4)
    // - Nmap scan report for 1.2.3.4 [host down, ...]
    const firstToken = report.match(/^([^\s\[(]+)/)?.[1]?.trim().toLowerCase() ?? ''
    if (isLikelyIp(firstToken)) {
      pushUnique(artifacts.ips, firstToken)
      pushUnique(artifacts.live_hosts, firstToken)
      continue
    }

    if (isLikelyHostToken(firstToken) && !shouldIgnoreHostForChaining(firstToken)) {
      pushUnique(artifacts.domains, firstToken)
      pushUnique(artifacts.live_hosts, firstToken)
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
    const parts = m.split(':')
    if (parts.length < 2) continue
    const hostPart = parts.slice(0, -1).join(':').trim()
    const portPart = parts[parts.length - 1]?.trim() ?? ''

    // Guard against timestamps like 12:09 or 2026-04-06T12:09
    if (/^\d+$/.test(hostPart)) continue

    const port = parseValidPort(portPart)
    if (port) pushUnique(artifacts.open_ports, port)
  }

  for (const match of corpus.match(PORT_PROTO_RE) ?? []) {
    const rawPort = match.split('/')[0]
    const port = parseValidPort(rawPort)
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

  if (p === 'list_file') return ['subdomains', 'domains', 'live_hosts', 'ips', 'urls']
  if (isPortParam(p)) return ['open_ports', 'params']
  if (['domain', 'dns_name'].includes(p)) return ['subdomains', 'domains', 'params']
  if (['url', 'endpoint'].includes(p)) return ['endpoints', 'urls', 'domains', 'params']

  if (['target', 'host', 'query', 'hostname', 'rhost', 'lhost'].includes(p) && (t.includes('nmap') || t.includes('enum4linux') || t.includes('netexec') || t.includes('smb') || t.includes('rpc'))) {
    return ['ips', 'live_hosts', 'domains', 'params']
  }
  if (['target', 'host', 'query', 'hostname'].includes(p)) return ['live_hosts', 'domains', 'ips', 'urls', 'params']

  if (t.includes('httpx') || t.includes('gospider') || t.includes('hakrawler')) {
    return ['live_hosts', 'urls', 'domains', 'params']
  }
  if (t.includes('shuffledns') || t.includes('dns')) {
    return ['subdomains', 'domains', 'params']
  }
  return ['params']
}

function candidateValueFor(source: keyof StepArtifacts | 'params', ctx: PriorStepContext, param: string, fallbackTarget: string): string | null {
  const p = param.toLowerCase()

  if (!shouldSuggestParam(p)) return null

  if (source === 'params') {
    if (isPortParam(p)) {
      const raw = firstParam(ctx.params, [p, 'ports', 'port'])
      if (!raw) return null
      const tokens = raw.split(',').map(v => parseValidPort(v)).filter((v): v is string => !!v)
      if (tokens.length === 0) return null
      return p === 'port' ? tokens[0] : tokens.slice(0, 10).join(',')
    }
    if (isDomainParam(p)) {
      const raw = firstParam(ctx.params, ['domain', 'dns_name', 'target', 'host'])
      if (!raw || isLikelyIp(raw)) return null
      return rootDomain(raw)
    }
    if (isUrlParam(p)) {
      const raw = firstParam(ctx.params, ['url', 'endpoint', 'target'])
      if (!raw) return null
      if (raw.startsWith('http://') || raw.startsWith('https://')) return raw
      if (isLikelyIp(raw)) return null
      return targetToUrl(raw)
    }
    if (isHostParam(p)) {
      const raw = firstParam(ctx.params, [p, 'target', 'host', 'domain'])
      if (!raw) return null
      return raw
    }
    return null
  }

  const values = ctx.artifacts[source]
  if (!values || values.length === 0) return null

  if (isPortParam(p)) {
    const numeric = values.map(v => parseValidPort(v)).filter((v): v is string => !!v)
    if (numeric.length === 0) return null
    return p === 'port' ? numeric[0] : numeric.slice(0, 10).join(',')
  }

  if (isDomainParam(p)) {
    const picked = values.find(v => !isLikelyIp(v)) ?? values[0]
    if (!picked || isLikelyIp(picked)) return null
    if (!isLikelyHostToken(cleanPotentialHostToken(picked))) return null
    return rootDomain(picked)
  }
  if (isUrlParam(p)) {
    const picked = values.find(v => v.startsWith('http://') || v.startsWith('https://'))
      ?? values.find(v => !isLikelyIp(v))
      ?? values[0]
    if (!picked) return null
    if (isLikelyIp(picked)) return null
    if (picked.startsWith('http://') || picked.startsWith('https://')) return picked
    return targetToUrl(picked)
  }
  if (isHostParam(p)) {
    const picked = values[0] ?? fallbackTarget
    return picked || null
  }
  return null
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
  baselineValues,
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
  baselineValues?: Record<string, string>
  preferences?: ChainMappingPreference[]
}): ChainSuggestion | null {
  const paramNames = [...Object.keys(selectedTool.params), ...Object.keys(selectedTool.optional)]
  const baseline = baselineValues ?? {}
  const missingParams = paramNames
    .filter(name => {
      const current = currentValues[name]?.trim() ?? ''
      if (!current) return true
      const defaultValue = baseline[name]?.trim() ?? ''
      // Keep chain hints visible when the field only has a generic auto-filled value.
      return !!defaultValue && current === defaultValue
    })
    .filter(name => shouldSuggestParam(name))
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

    if (chosen) {
      const current = currentValues[param]?.trim() ?? ''
      if (current && isSameFieldValue(param, current, chosen.value)) continue
      fields.push(chosen)
    }
  }

  if (fields.length === 0) return null

  const bestField = fields.reduce((best, field) => (field.confidence > best.confidence ? field : best), fields[0])
  const uniqueSources = new Set(fields.map(field => field.sourceTool))
  const confidence = fields.reduce((sum, f) => sum + f.confidence, 0) / fields.length
  return {
    sourceTool: bestField.sourceTool,
    summary: uniqueSources.size > 1
      ? `Prepared ${fields.length} mapped value${fields.length === 1 ? '' : 's'} from ${uniqueSources.size} prior tools.`
      : `Prepared ${fields.length} mapped value${fields.length === 1 ? '' : 's'} from ${bestField.sourceTool} output.`,
    confidence,
    fields,
  }
}
