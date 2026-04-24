import type { RunHistoryEntry } from './types'

export function safeFixed(n: number | undefined | null, dec = 1, fallback = '—'): string {
  return typeof n === 'number' && isFinite(n) ? n.toFixed(dec) : fallback
}

export function fmt(n: number | undefined | null, dec = 1): string {
  return safeFixed(n, dec, '—')
}

export function fmtTs(ts: number): string {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString('en-GB')
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = parseFloat((bytes / Math.pow(k, i)).toFixed(2))
  return `${value} ${sizes[i]}`
}

export function getSuccessAccent(ok: number, total: number): string {
  if (ok === total) return 'var(--success)'
  if (ok === 0) return 'var(--danger)'
  return 'var(--warning)'
}

export function uptimeStr(secs: number): string {
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.floor(secs % 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

export function exportEntry(entry: RunHistoryEntry, format: 'txt' | 'json') {
  const r = entry.result
  const ts = entry.ts.toISOString().replace(/[:.]/g, '-')
  const filename = `${entry.tool}_${ts}.${format}`

  let content: string
  if (format === 'json') {
    content = JSON.stringify({
      tool: entry.tool,
      timestamp: entry.ts.toISOString(),
      params: entry.params,
      success: r.success,
      return_code: r.return_code,
      execution_time: r.execution_time,
      timed_out: r.timed_out,
      partial_results: r.partial_results,
      stdout: r.stdout,
      stderr: r.stderr,
    }, null, 2)
  } else {
    const paramStr = Object.entries(entry.params).map(([k, v]) => `  ${k}=${v}`).join('\n')
    content = [
      `Tool:       ${entry.tool}`,
      `Timestamp:  ${entry.ts.toISOString()}`,
      `Success:    ${r.success}`,
      `Exit code:  ${r.return_code}`,
      `Time:       ${safeFixed(r.execution_time, 2)}s`,
      r.timed_out ? `Timed out:  yes` : '',
      r.partial_results ? `Partial:    yes` : '',
      paramStr ? `\nParams:\n${paramStr}` : '',
      `\n--- stdout ---\n${r.stdout || '(empty)'}`,
      r.stderr ? `\n--- stderr ---\n${r.stderr}` : '',
    ].filter(Boolean).join('\n')
  }

  const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
