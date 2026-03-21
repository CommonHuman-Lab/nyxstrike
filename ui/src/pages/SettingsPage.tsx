import { useState, useEffect } from 'react'
import { RefreshCw, XCircle, Save } from 'lucide-react'
import { api, type Settings } from '../api'
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
  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  const [timeout, setTimeout_] = useState('')
  const [cacheSize, setCacheSize] = useState('')
  const [cacheTtl, setCacheTtl] = useState('')
  const [toolTtl, setToolTtl] = useState('')

  // --- Server Cache Stats ---
  const [cacheMsg, setCacheMsg] = useState<string|null>(null)
  const [clearingCache, setClearingCache] = useState(false)

  useEffect(() => {
    api.getSettings().then(r => {
      setSettings(r.settings)
      setTimeout_(String(r.settings.runtime.command_timeout))
      setCacheSize(String(r.settings.runtime.cache_size))
      setCacheTtl(String(r.settings.runtime.cache_ttl))
      setToolTtl(String(r.settings.runtime.tool_availability_ttl))
      setLoading(false)
    }).catch(e => {
      setError(String(e))
      setLoading(false)
    })
  }, [])

  async function save() {
    setSaving(true)
    setSaveMsg(null)
    try {
      const res = await api.patchSettings({
        command_timeout: Number(timeout),
        cache_size: Number(cacheSize),
        cache_ttl: Number(cacheTtl),
        tool_availability_ttl: Number(toolTtl),
      })
      if (res.success && res.settings) {
        setSettings(res.settings)
        setSaveMsg('Saved')
      } else {
        setSaveMsg('Error: ' + JSON.stringify(res.errors || res.error))
      }
    } catch (e) {
      setSaveMsg('Error: ' + String(e))
    } finally {
      setSaving(false)
      setTimeout(() => setSaveMsg(null), 3000)
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
            <Save size={14} /> {saving ? 'Saving…' : 'Save Changes'}
          </button>
          {saveMsg && (
            <span className={`save-msg ${saveMsg.startsWith('Error') ? 'err' : 'ok'}`}>{saveMsg}</span>
          )}
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
                setCacheMsg(null)
                try {
                  const res = await api.clearCache()
                  if(res.success){
                    setCacheMsg("Cache cleared!")
                  } else {
                    setCacheMsg("Cache clear failed: "+(res.message||'unknown error'))
                  }
                } catch(e:any){
                  setCacheMsg("Cache clear error: "+String(e))
                }
                setTimeout(()=>setCacheMsg(null),2000)
                setClearingCache(false)
              }}
            >{clearingCache ? "Clearing…" : "Clear Cache"}</button>
            {cacheMsg && <span style={{marginLeft:10, fontSize:'12px', color: cacheMsg.startsWith('Cache cleared')?'var(--green)':'var(--red)'}}>{cacheMsg}</span>}
          </div>
        </div>
      </section>

      {/* ── Wordlists ── */}
      <section className="section">
        <div className="section-header">
          <h3>Wordlists <span className="badge">{settings.wordlists.length}</span></h3>
        </div>
        <div className="wordlist-table">
          <div className="wordlist-head">
            <span>Name</span><span>Type</span><span>Speed</span><span>Coverage</span><span>Path</span>
          </div>
          {settings.wordlists.map(w => (
            <div key={w.name} className="wordlist-row">
              <span className="mono">{w.name}</span>
              <span className="badge-small">{w.type}</span>
              <span>{w.speed}</span>
              <span>{w.coverage}</span>
              <span className="mono wl-path">{w.path}</span>
            </div>
          ))}
        </div>
        <p className="settings-hint">
          Edit wordlists via <code>GET/POST /api/wordlists</code> or modify <code>config.py</code> and restart.
        </p>
      </section>
    </div>
  )
}
