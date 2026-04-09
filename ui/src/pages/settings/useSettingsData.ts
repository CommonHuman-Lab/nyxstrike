import { useEffect, useState } from 'react'
import { api, type Settings, type WordlistEntry } from '../../api'
import { useToast } from '../../components/ToastProvider'

const WORDLIST_TYPE_OPTIONS = ['password', 'directory', 'params', 'subdomain', 'username', 'general']
const SPEED_OPTIONS = ['fast', 'medium', 'slow']
const COVERAGE_OPTIONS = ['focused', 'broad', 'comprehensive']

type SettingsCache = {
  settings: Settings
  timeout: string
  requestTimeout: string
  inactivityTimeout: string
  maxRuntime: string
  cacheSize: string
  cacheTtl: string
  toolTtl: string
  wordlistsDraft: WordlistEntry[]
}

let settingsCache: SettingsCache | null = null

function withCurrentOption(options: string[], current: string) {
  if (!current) return options
  return options.includes(current) ? options : [current, ...options]
}

export function useSettingsData() {
  const { pushToast } = useToast()
  const hasCache = settingsCache !== null

  const [settings, setSettings] = useState<Settings | null>(settingsCache?.settings ?? null)
  const [loading, setLoading] = useState(!hasCache)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [wordlistsSaving, setWordlistsSaving] = useState(false)
  const [clearingCache, setClearingCache] = useState(false)

  const [timeout, setTimeout_] = useState(settingsCache?.timeout ?? '')
  const [requestTimeout, setRequestTimeout] = useState(settingsCache?.requestTimeout ?? '')
  const [inactivityTimeout, setInactivityTimeout] = useState(settingsCache?.inactivityTimeout ?? '')
  const [maxRuntime, setMaxRuntime] = useState(settingsCache?.maxRuntime ?? '')
  const [cacheSize, setCacheSize] = useState(settingsCache?.cacheSize ?? '')
  const [cacheTtl, setCacheTtl] = useState(settingsCache?.cacheTtl ?? '')
  const [toolTtl, setToolTtl] = useState(settingsCache?.toolTtl ?? '')
  const [wordlistsDraft, setWordlistsDraft] = useState<WordlistEntry[]>(settingsCache?.wordlistsDraft ?? [])

  function applySettings(response: Settings) {
    const nextCache: SettingsCache = {
      settings: response,
      timeout: String(response.runtime.command_timeout),
      requestTimeout: String(response.runtime.request_timeout),
      inactivityTimeout: String(response.runtime.command_inactivity_timeout),
      maxRuntime: String(response.runtime.command_max_runtime),
      cacheSize: String(response.runtime.cache_size),
      cacheTtl: String(response.runtime.cache_ttl),
      toolTtl: String(response.runtime.tool_availability_ttl),
      wordlistsDraft: response.wordlists.map(w => ({ ...w })),
    }
    settingsCache = nextCache
    setSettings(nextCache.settings)
    setTimeout_(nextCache.timeout)
    setRequestTimeout(nextCache.requestTimeout)
    setInactivityTimeout(nextCache.inactivityTimeout)
    setMaxRuntime(nextCache.maxRuntime)
    setCacheSize(nextCache.cacheSize)
    setCacheTtl(nextCache.cacheTtl)
    setToolTtl(nextCache.toolTtl)
    setWordlistsDraft(nextCache.wordlistsDraft)
  }

  useEffect(() => {
    api.getSettings().then(response => {
      applySettings(response.settings)
      setLoading(false)
    }).catch(e => {
      if (!settingsCache) setError(String(e))
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
        request_timeout: Number(requestTimeout),
        command_inactivity_timeout: Number(inactivityTimeout),
        command_max_runtime: Number(maxRuntime),
        cache_size: Number(cacheSize),
        cache_ttl: Number(cacheTtl),
        tool_availability_ttl: Number(toolTtl),
      })
      if (!runtimeRes.success) {
        pushToast('error', 'Failed to save runtime settings')
        return
      }
      if (runtimeRes.settings) applySettings(runtimeRes.settings)
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
      applySettings(refreshed.settings)
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
    requestTimeout,
    inactivityTimeout,
    maxRuntime,
    cacheSize,
    cacheTtl,
    toolTtl,
    wordlistsDraft,
    setTimeout_,
    setRequestTimeout,
    setInactivityTimeout,
    setMaxRuntime,
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
