export const RUN_FAVORITES_KEY = 'nyxstrike_run_favorites'
export const RUN_RECENT_TARGETS_KEY = 'nyxstrike_run_recent_targets'

export function deriveTargetFromParams(params: Record<string, unknown>): string | null {
  const candidateKeys = ['target', 'url', 'domain', 'host', 'ip', 'rhost', 'hostname']
  for (const key of candidateKeys) {
    const value = params[key]
    if (value == null) continue
    const trimmed = String(value).trim()
    if (trimmed.length > 0) return trimmed
  }
  return null
}
