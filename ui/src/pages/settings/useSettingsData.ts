import { useEffect, useState } from 'react'
import { api, type Settings, type WordlistEntry } from '../../api'
import { useToast } from '../../components/ToastProvider'

const WORDLIST_TYPE_OPTIONS = ['password', 'directory', 'params', 'subdomain', 'username', 'general']
const SPEED_OPTIONS = ['fast', 'medium', 'slow']
const COVERAGE_OPTIONS = ['focused', 'broad', 'comprehensive']

function withCurrentOption(options: string[], current: string) {
  if (!current) return options
  return options.includes(current) ? options : [current, ...options]
}

export function useSettingsData() {
  const { pushToast } = useToast()

  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [wordlistsSaving, setWordlistsSaving] = useState(false)
  const [clearingCache, setClearingCache] = useState(false)

  const [timeout, setTimeout_] = useState('')
  const [cacheSize, setCacheSize] = useState('')
  const [cacheTtl, setCacheTtl] = useState('')
  const [toolTtl, setToolTtl] = useState('')
  const [wordlistsDraft, setWordlistsDraft] = useState<WordlistEntry[]>([])

  useEffect(() => {
    api.getSettings().then(response => {
      setSettings(response.settings)
      setTimeout_(String(response.settings.runtime.command_timeout))
      setCacheSize(String(response.settings.runtime.cache_size))
      setCacheTtl(String(response.settings.runtime.cache_ttl))
      setToolTtl(String(response.settings.runtime.tool_availability_ttl))
      setWordlistsDraft(response.settings.wordlists.map(w => ({ ...w })))
      setLoading(false)
    }).catch(e => {
      setError(String(e))
      setLoading(false)
    })
  }, [])

  function updateWordlist(index: number, field: keyof WordlistEntry, value: string) {
    setWordlistsDraft(prev => prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)))
  }

  function addWordlist() {
    setWordlistsDraft(prev => [
      ...prev,
      { name: '', path: '', type: 'directory', speed: 'medium', coverage: 'broad' },
    ])
  }

  function removeWordlist(index: number) {
    setWordlistsDraft(prev => prev.filter((_, i) => i !== index))
  }

  async function saveRuntime() {
    setSaving(true)
    try {
      const runtimeRes = await api.patchSettings({
        command_timeout: Number(timeout),
        cache_size: Number(cacheSize),
        cache_ttl: Number(cacheTtl),
        tool_availability_ttl: Number(toolTtl),
      })
      if (!runtimeRes.success) {
        pushToast('error', 'Failed to save runtime settings')
        return
      }
      pushToast('success', 'Runtime settings saved')
    } catch {
      pushToast('error', 'Failed to save runtime settings')
    } finally {
      setSaving(false)
    }
  }

  async function saveWordlists() {
    setWordlistsSaving(true)
    try {
      const wordlistsRes = await api.patchWordlists(wordlistsDraft)
      if (!wordlistsRes.success) {
        pushToast('error', 'Failed to save wordlists')
        return
      }

      const refreshed = await api.getSettings()
      setSettings(refreshed.settings)
      setWordlistsDraft(refreshed.settings.wordlists.map(w => ({ ...w })))
      pushToast('success', 'Wordlists saved')
    } catch {
      pushToast('error', 'Failed to save wordlists')
    } finally {
      setWordlistsSaving(false)
    }
  }

  async function clearCache() {
    setClearingCache(true)
    try {
      const res = await api.clearCache()
      if (res.success) {
        pushToast('success', 'Cache cleared')
      } else {
        pushToast('error', 'Failed to clear cache')
      }
    } catch {
      pushToast('error', 'Failed to clear cache')
    } finally {
      setClearingCache(false)
    }
  }

  return {
    settings,
    loading,
    error,
    saving,
    wordlistsSaving,
    clearingCache,
    timeout,
    cacheSize,
    cacheTtl,
    toolTtl,
    wordlistsDraft,
    setTimeout_,
    setCacheSize,
    setCacheTtl,
    setToolTtl,
    addWordlist,
    removeWordlist,
    updateWordlist,
    saveRuntime,
    saveWordlists,
    clearCache,
    withCurrentTypeOption: (current: string) => withCurrentOption(WORDLIST_TYPE_OPTIONS, current),
    withCurrentSpeedOption: (current: string) => withCurrentOption(SPEED_OPTIONS, current),
    withCurrentCoverageOption: (current: string) => withCurrentOption(COVERAGE_OPTIONS, current),
  }
}
