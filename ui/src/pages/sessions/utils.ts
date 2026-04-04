import type { SessionSummary } from '../../api'

export function sessionName(session: SessionSummary): string {
  const meta = (session.metadata ?? {}) as Record<string, unknown>
  const explicitName = meta.session_name
  if (typeof explicitName === 'string' && explicitName.trim()) {
    const value = explicitName.trim()
    return value.charAt(0).toUpperCase() + value.slice(1)
  }

  const mode = (typeof session.objective === 'string' && session.objective)
    || (typeof meta.mode === 'string' ? meta.mode : '')
  if (mode) {
    const value = mode.replace(/_/g, ' ').trim()
    return value.charAt(0).toUpperCase() + value.slice(1)
  }

  return 'Session'
}
