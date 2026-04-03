const HTTP_ACCESS_RE = /\d+\.\d+\.\d+\.\d+.*"GET \/web-dashboard HTTP\/\d/

export function getVisibleLogLines(logLines: string[], showHttpAccess: boolean): string[] {
  if (showHttpAccess) return logLines
  return logLines.filter(line => !HTTP_ACCESS_RE.test(line))
}

export function getLogLevelClass(line: string): '' | 'error' | 'warn' | 'debug' {
  if (/\bERROR\b/.test(line)) return 'error'
  if (/\bWARN(ING)?\b/.test(line)) return 'warn'
  if (/\bDEBUG\b/.test(line)) return 'debug'
  return ''
}
