import { useEffect, useState } from 'react'
import { api, hasToken, type WebDashboardResponse } from '../api'

interface UseAuthOptions {
  demo: boolean
  onProbeSuccess: (health: WebDashboardResponse) => void
  onLoadingDone: () => void
}

export function useAuth({ demo, onProbeSuccess, onLoadingDone }: UseAuthOptions) {
  const [authed, setAuthed] = useState(demo || hasToken())
  const [needsAuth, setNeedsAuth] = useState(false)

  // Try without token first (skipped in demo)
  useEffect(() => {
    if (demo || hasToken()) return
    api.dashboard().then(h => {
      onProbeSuccess(h)
      setAuthed(true)
    }).catch(e => {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        setNeedsAuth(true)
      } else {
        setAuthed(true)
      }
      onLoadingDone()
    })
  }, [])

  return { authed, needsAuth, setAuthed, setNeedsAuth }
}
