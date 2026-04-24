import { useState, useEffect, useCallback } from 'react'
import { api } from '../../api'
import type { ChatSession } from '../../api'

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)

  const loadSessions = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.chat.listSessions()
      if (res.success) setSessions(res.sessions)
    } catch {
      // non-critical
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  async function createSession(): Promise<ChatSession | null> {
    try {
      const res = await api.chat.createSession()
      if (res.success) {
        setSessions(prev => [res.session, ...prev])
        return res.session
      }
    } catch { /* ignore */ }
    return null
  }

  async function deleteSession(id: string): Promise<void> {
    try {
      await api.chat.deleteSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
    } catch { /* ignore */ }
  }

  async function deleteAllSessions(): Promise<void> {
    // Delete sequentially; best-effort — remove from local state regardless
    const ids = sessions.map(s => s.id)
    await Promise.allSettled(ids.map(id => api.chat.deleteSession(id)))
    setSessions([])
  }

  function updateSessionName(id: string, name: string) {
    setSessions(prev => prev.map(s => s.id === id ? { ...s, name } : s))
  }

  async function renameSession(id: string, name: string): Promise<void> {
    try {
      await api.chat.renameSession(id, name)
      setSessions(prev => prev.map(s => s.id === id ? { ...s, name } : s))
    } catch { /* ignore */ }
  }

  return { sessions, loading, createSession, deleteSession, deleteAllSessions, updateSessionName, renameSession, reload: loadSessions }
}
