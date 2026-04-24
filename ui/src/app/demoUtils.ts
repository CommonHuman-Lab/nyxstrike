// ─── Demo mode activation helpers ─────────────────────────────────────────────
// Kept in a tiny separate module so App.tsx doesn't pull in the large DEMO_*
// data constants on every page load.

export function isDemoMode(): boolean {
  if (new URLSearchParams(window.location.search).get('demo') === '1') {
    sessionStorage.setItem('nyxstrike_demo', '1')
    return true
  }
  return sessionStorage.getItem('nyxstrike_demo') === '1'
}

export function exitDemo() {
  sessionStorage.removeItem('nyxstrike_demo')
}
