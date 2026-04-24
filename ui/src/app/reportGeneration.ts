/**
 * Module-level store for report generation state.
 * Lives outside React so it survives page/tab navigation.
 */

export type ReportGenState =
  | { status: 'idle' }
  | { status: 'generating'; label: string }
  | { status: 'done'; label: string; savedPath: string }
  | { status: 'error'; label: string; message: string }

type Listener = (state: ReportGenState) => void

let _state: ReportGenState = { status: 'idle' }
const _listeners = new Set<Listener>()

function _notify() {
  _listeners.forEach(fn => fn(_state))
}

export function getReportGenState(): ReportGenState {
  return _state
}

export function setReportGenState(next: ReportGenState) {
  _state = next
  _notify()
}

export function subscribeReportGen(fn: Listener): () => void {
  _listeners.add(fn)
  return () => _listeners.delete(fn)
}

// ── Convenience helpers ────────────────────────────────────────────────────────

export function reportGenStart(label: string) {
  setReportGenState({ status: 'generating', label })
}

export function reportGenDone(label: string, savedPath: string) {
  setReportGenState({ status: 'done', label, savedPath })
}

export function reportGenError(label: string, message: string) {
  setReportGenState({ status: 'error', label, message })
}

export function reportGenDismiss() {
  setReportGenState({ status: 'idle' })
}

// ── Navigation callback ────────────────────────────────────────────────────────
// SessionDetailPage registers this so the bubble can navigate to the saved note.

type NavigateCallback = (savedPath: string) => void
let _navigateFn: NavigateCallback | null = null

export function registerReportNavigation(fn: NavigateCallback): () => void {
  _navigateFn = fn
  return () => { if (_navigateFn === fn) _navigateFn = null }
}

export function reportGenNavigate(savedPath: string) {
  _navigateFn?.(savedPath)
}

export function isReportGenerating(): boolean {
  return _state.status === 'generating'
}

export function setReportGenerating(value: boolean) {
  // No-op shim — modal now calls reportGenStart/Done/Error directly.
  // Kept so existing imports don't break during transition.
  if (!value && _state.status === 'generating') {
    setReportGenState({ status: 'idle' })
  }
}
