import { useState, useEffect } from 'react'
import { RefreshCw, XCircle, Save, Plus, Trash2 } from 'lucide-react'
import { api, type Settings, type WordlistEntry } from '../api'
import { useToast } from '../components/ToastProvider'
import './SettingsPage.css'

function SettingsRow({ label, value, mono, accent }: {
  label: string
  value: string
  mono?: boolean
  accent?: string
}) {
  return (
    <div className="settings-row">
      <span className="settings-label">{label}</span>
      <span className={`settings-value ${mono ? 'mono' : ''}`} style={accent ? { color: accent } : {}}>
        {value}
      </span>
    </div>
  )
}

function SettingsField({ label, unit, hint, value, onChange }: {
  label: string
  unit: string
  hint: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="settings-field">
      <label className="settings-label">{label}</label>
      <div className="settings-input-row">
        <input
          className="settings-input mono"
          type="number"
          min={1}
          value={value}
          onChange={e => onChange(e.target.value)}
        />
        <span className="settings-unit">{unit}</span>
      </div>
      <span className="settings-hint-inline">{hint}</span>
    </div>
  )
}


export default function SettingsPage() {
  const wordlistTypeOptions = ['password', 'directory', 'params', 'subdomain', 'username', 'general']
  const speedOptions = ['fast', 'medium', 'slow']
  const coverageOptions = ['focused', 'broad', 'comprehensive']

  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [wordlistsSaving, setWordlistsSaving] = useState(false)
  const { pushToast } = useToast()

  const [timeout, setTimeout_] = useState('')
  const [cacheSize, setCacheSize] = useState('')
  const [cacheTtl, setCacheTtl] = useState('')
  const [toolTtl, setToolTtl] = useState('')
  const [wordlistsDraft, setWordlistsDraft] = useState<WordlistEntry[]>([])

  // --- Server Cache Stats ---
  const [clearingCache, setClearingCache] = useState(false)

  useEffect(() => {
    api.getSettings().then(r => {
      setSettings(r.settings)
      setTimeout_(String(r.settings.runtime.command_timeout))
      setCacheSize(String(r.settings.runtime.cache_size))
      setCacheTtl(String(r.settings.runtime.cache_ttl))
      setToolTtl(String(r.settings.runtime.tool_availability_ttl))
      setWordlistsDraft(r.settings.wordlists.map(w => ({ ...w })))
      setLoading(false)
    }).catch(e => {
      setError(String(e))
      setLoading(false)
    })
  }, [])

  function updateWordlist(index: number, field: keyof WordlistEntry, value: string) {
    setWordlistsDraft(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item))
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

  function withCurrentOption(options: string[], current: string) {
    if (!current) return options
    return options.includes(current) ? options : [current, ...options]
  }

  async function save() {
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
    } catch (e) {
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
    } catch (e) {
      pushToast('error', 'Failed to save wordlists')
    } finally {
      setWordlistsSaving(false)
    }
  }

  if (loading) return (
    <div className="loading-state">
      <RefreshCw size={20} className="spin" color="var(--green)" />
      <p>Loading settings…</p>
    </div>
  )
  if (error) return <div className="error-banner"><XCircle size={16} /> {error}</div>
  if (!settings) return null

  return (
    <div className="settings-page">
      {/* ── Server Environment ── */}
      <section className="section">
        <div className="section-header">
          <h3>Server Environment <span className="badge">read-only</span></h3>
        </div>
        <div className="settings-grid">
          <SettingsRow label="Host" value={settings.server.host} mono />
          <SettingsRow label="Port" value={String(settings.server.port)} mono />
          <SettingsRow
            label="Auth Enabled"
            value={settings.server.auth_enabled ? 'Yes (HEXSTRIKE_API_TOKEN set)' : 'No'}
            accent={settings.server.auth_enabled ? 'var(--green)' : 'var(--amber)'}
          />
          <SettingsRow
            label="Debug Mode"
            value={settings.server.debug_mode ? 'On' : 'Off'}
            accent={settings.server.debug_mode ? 'var(--amber)' : 'var(--text-dim)'}
          />
          <SettingsRow label="Data Directory" value={settings.server.data_dir} mono />
        </div>
        <p className="settings-hint">
          Change these by setting environment variables before starting the server:
          <code> HEXSTRIKE_HOST</code>, <code>HEXSTRIKE_PORT</code>, <code>HEXSTRIKE_API_TOKEN</code>,
          <code> DEBUG_MODE</code>, <code>HEXSTRIKE_DATA_DIR</code>.
        </p>
      </section>

      {/* ── Runtime Config ── */}
      <section className="section">
        <div className="section-header">
          <h3>Runtime Config</h3>
          <span className="section-meta">changes apply immediately, reset on server restart</span>
        </div>
        <div className="settings-grid">
          <SettingsField
            label="Command Timeout" unit="seconds"
            hint="Max time a tool process is allowed to run."
            value={timeout} onChange={setTimeout_}
          />
          <SettingsField
            label="Cache Size" unit="entries"
            hint="Maximum number of cached tool results."
            value={cacheSize} onChange={setCacheSize}
          />
          <SettingsField
            label="Cache TTL" unit="seconds"
            hint="How long a cache entry lives before expiry."
            value={cacheTtl} onChange={setCacheTtl}
          />
          <SettingsField
            label="Tool Availability TTL" unit="seconds"
            hint="How long the tool availability check is cached."
            value={toolTtl} onChange={setToolTtl}
          />
        </div>
        <div className="settings-actions">
          <button className="btn-primary" onClick={save} disabled={saving}>
            <Save size={14} /> {saving ? 'Saving…' : 'Save Runtime'}
          </button>
        </div>
      </section>

      {/* ── Server Controls ── */}
      <section className="section">
        <div className="section-header">
          <h3>Server Controls</h3>
        </div>
        <div className="settings-grid">
          <div className="settings-row" style={{alignItems:'flex-start'}}>
            <button
              className={"btn-primary"}
              style={{minWidth:120}}
              disabled={clearingCache}
              onClick={async () => {
                setClearingCache(true)
                try {
                  const res = await api.clearCache()
                  if(res.success){
                    pushToast('success', 'Cache cleared')
                  } else {
                    pushToast('error', 'Failed to clear cache')
                  }
                } catch(e:any){
                  pushToast('error', 'Failed to clear cache')
                }
                setClearingCache(false)
              }}
            >{clearingCache ? "Clearing…" : "Clear Cache"}</button>
          </div>
        </div>
      </section>

      {/* ── Wordlists ── */}
      <section className="section">
        <div className="section-header">
          <h3>Wordlists <span className="badge">{wordlistsDraft.length}</span></h3>
          <div className="settings-actions-inline">
            <button className="btn-secondary" onClick={addWordlist} disabled={wordlistsSaving}>
              <Plus size={14} /> Add Wordlist
            </button>
            <button className="btn-secondary" onClick={saveWordlists} disabled={wordlistsSaving}>
              <Save size={14} /> {wordlistsSaving ? 'Saving…' : 'Save Wordlists'}
            </button>
          </div>
        </div>
        <div className="wordlist-table">
          <div className="wordlist-head">
            <span>Name</span><span>Type</span><span>Speed</span><span>Coverage</span><span>Path</span><span>Actions</span>
          </div>
          {wordlistsDraft.map((w, idx) => (
            <div key={`wordlist-row-${idx}`} className="wordlist-row editable">
              <input
                className="settings-input mono wordlist-input"
                value={w.name}
                onChange={e => updateWordlist(idx, 'name', e.target.value)}
                placeholder="rockyou"
                disabled={!!w.is_default}
              />
              <select
                className="settings-input wordlist-input"
                value={w.type}
                onChange={e => updateWordlist(idx, 'type', e.target.value)}
              >
                {withCurrentOption(wordlistTypeOptions, w.type).map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
              <select
                className="settings-input wordlist-input"
                value={w.speed}
                onChange={e => updateWordlist(idx, 'speed', e.target.value)}
              >
                {withCurrentOption(speedOptions, w.speed).map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
              <select
                className="settings-input wordlist-input"
                value={w.coverage}
                onChange={e => updateWordlist(idx, 'coverage', e.target.value)}
              >
                {withCurrentOption(coverageOptions, w.coverage).map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
              <input
                className="settings-input mono wordlist-input"
                value={w.path}
                onChange={e => updateWordlist(idx, 'path', e.target.value)}
                placeholder="/usr/share/wordlists/rockyou.txt"
              />
              <button
                className="btn-danger-outline"
                onClick={() => removeWordlist(idx)}
                disabled={wordlistsSaving || !!w.is_default}
                title={w.is_default ? 'Default wordlists cannot be deleted' : 'Remove row'}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        <p className="settings-hint">
          Changes are stored in <code>wordlists.json</code>. Entries here override defaults from <code>config.py</code>.
        </p>
      </section>
    </div>
  )
}
