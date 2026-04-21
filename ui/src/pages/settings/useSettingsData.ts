import { useEffect, useState } from 'react'
import { api, type Settings, type WordlistEntry, type PersonalityPreset } from '../../api'
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
  chatPersonality: string
  customPrompt: string
  personalityPresets: PersonalityPreset[]
  summarizationThreshold: string
  contextInjectionChars: string
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
  const [chatPersonality, setChatPersonality] = useState(settingsCache?.chatPersonality ?? 'nyxstrike')
  const [customPrompt, setCustomPrompt] = useState(settingsCache?.customPrompt ?? '')
  const [personalityPresets, setPersonalityPresets] = useState<PersonalityPreset[]>(settingsCache?.personalityPresets ?? [])
  const [summarizationThreshold, setSummarizationThreshold] = useState(settingsCache?.summarizationThreshold ?? '')
  const [contextInjectionChars, setContextInjectionChars] = useState(settingsCache?.contextInjectionChars ?? '')

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
      chatPersonality: response.chat?.personality ?? 'nyxstrike',
      customPrompt: response.chat?.custom_prompt ?? '',
      personalityPresets: response.chat?.personality_presets ?? [],
      summarizationThreshold: String(response.chat?.summarization_threshold ?? 20),
      contextInjectionChars: String(response.chat?.context_injection_chars ?? 4000),
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
    setChatPersonality(nextCache.chatPersonality)
    setCustomPrompt(nextCache.customPrompt)
    setPersonalityPresets(nextCache.personalityPresets)
    setSummarizationThreshold(nextCache.summarizationThreshold)
    setContextInjectionChars(nextCache.contextInjectionChars)
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

  async function saveChatSettings() {
    setSaving(true)
    try {
      // Resolve the active system_prompt from the selected personality
      const resolvedPrompt =
        chatPersonality === 'custom'
          ? customPrompt
          : personalityPresets.find(p => p.id === chatPersonality)?.prompt ?? customPrompt

      const res = await api.patchSettings({}, {
        personality: chatPersonality,
        system_prompt: resolvedPrompt,
        custom_prompt: customPrompt,
        summarization_threshold: Number(summarizationThreshold),
        context_injection_chars: Number(contextInjectionChars),
      })
      if (!res.success) {
        pushToast('error', 'Failed to save chat settings')
        return
      }
      if (res.settings) applySettings(res.settings)
      pushToast('success', 'Chat settings saved')
    } catch {
      pushToast('error', 'Failed to save chat settings')
    } finally {
      setSaving(false)
    }
  }

  async function clearCache() {    setClearingCache(true)
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
    chatPersonality,
    customPrompt,
    personalityPresets,
    summarizationThreshold,
    contextInjectionChars,
    setTimeout_,
    setRequestTimeout,
    setInactivityTimeout,
    setMaxRuntime,
    setCacheSize,
    setCacheTtl,
    setToolTtl,
    setChatPersonality,
    setCustomPrompt,
    setSummarizationThreshold,
    setContextInjectionChars,
    addWordlist,
    removeWordlist,
    updateWordlist,
    saveRuntime,
    saveWordlists,
    saveChatSettings,
    clearCache,
    withCurrentTypeOption: (current: string) => withCurrentOption(WORDLIST_TYPE_OPTIONS, current),
    withCurrentSpeedOption: (current: string) => withCurrentOption(SPEED_OPTIONS, current),
    withCurrentCoverageOption: (current: string) => withCurrentOption(COVERAGE_OPTIONS, current),
  }
}

