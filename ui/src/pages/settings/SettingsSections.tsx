import { Save, Plus, Trash2 } from 'lucide-react'
import type { Settings, WordlistEntry, PersonalityPreset } from '../../api'
import { ActionButton } from '../../components/ActionButton'
import { CollapsibleSection } from '../../components/CollapsibleSection'

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
          min={0}
          value={value}
          onChange={e => onChange(e.target.value)}
        />
        <span className="settings-unit">{unit}</span>
      </div>
      <span className="settings-hint-inline">{hint}</span>
    </div>
  )
}

export function SettingsTextarea({ label, hint, value, onChange, rows = 4 }: {
  label: string
  hint: string
  value: string
  onChange: (v: string) => void
  rows?: number
}) {
  return (
    <div className="settings-field">
      <label className="settings-label">{label}</label>
      <textarea
        className="settings-input settings-textarea mono"
        rows={rows}
        value={value}
        onChange={e => onChange(e.target.value)}
      />
      <span className="settings-hint-inline">{hint}</span>
    </div>
  )
}

export function ServerEnvironmentSection({ settings }: { settings: Settings }) {
  return (
    <CollapsibleSection
      title="Server Environment"
      badge={<span className="badge">read-only</span>}
    >
      <div className="settings-grid">
        <SettingsRow label="Host" value={settings.server.host} mono />
        <SettingsRow label="Port" value={String(settings.server.port)} mono />
        <SettingsRow
          label="Auth Enabled"
          value={settings.server.auth_enabled ? 'Yes (NYXSTRIKE_API_TOKEN set)' : 'No'}
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
        <code> NYXSTRIKE_HOST</code>, <code>NYXSTRIKE_PORT</code>, <code>NYXSTRIKE_API_TOKEN</code>,
        <code> DEBUG_MODE</code>, <code>NYXSTRIKE_DATA_DIR</code>.
      </p>
    </CollapsibleSection>
  )
}

export function RuntimeConfigSection({
  timeout,
  requestTimeout,
  inactivityTimeout,
  maxRuntime,
  cacheSize,
  cacheTtl,
  toolTtl,
  setTimeout_,
  setRequestTimeout,
  setInactivityTimeout,
  setMaxRuntime,
  setCacheSize,
  setCacheTtl,
  setToolTtl,
  saving,
  onSave,
}: {
  timeout: string
  requestTimeout: string
  inactivityTimeout: string
  maxRuntime: string
  cacheSize: string
  cacheTtl: string
  toolTtl: string
  setTimeout_: (v: string) => void
  setRequestTimeout: (v: string) => void
  setInactivityTimeout: (v: string) => void
  setMaxRuntime: (v: string) => void
  setCacheSize: (v: string) => void
  setCacheTtl: (v: string) => void
  setToolTtl: (v: string) => void
  saving: boolean
  onSave: () => Promise<void>
}) {
  return (
    <CollapsibleSection
      title="Runtime Config"
      badge={<span className="section-meta">changes apply immediately</span>}
      defaultOpen
    >
      <div className="settings-grid">
        <SettingsField
          label="Command Timeout" unit="seconds"
          hint="Per-run hard timeout. Use 0 only in API when you need no hard timeout."
          value={timeout} onChange={setTimeout_}
        />
        <SettingsField
          label="Request Timeout" unit="seconds"
          hint="How long clients wait for API responses (0 means no client-side request timeout)."
          value={requestTimeout} onChange={setRequestTimeout}
        />
        <SettingsField
          label="Inactivity Timeout" unit="seconds"
          hint="Stops commands that produce no output for too long."
          value={inactivityTimeout} onChange={setInactivityTimeout}
        />
        <SettingsField
          label="Max Runtime" unit="seconds"
          hint="Safety cap for any single tool execution."
          value={maxRuntime} onChange={setMaxRuntime}
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
        <ActionButton variant="success" onClick={onSave} disabled={saving}>
          <Save size={14} /> {saving ? 'Saving…' : 'Save Runtime'}
        </ActionButton>
      </div>
    </CollapsibleSection>
  )
}

export function ServerControlsSection({
  clearingCache,
  onClearCache,
}: {
  clearingCache: boolean
  onClearCache: () => Promise<void>
}) {
  return (
    <CollapsibleSection title="Server Controls">
      <div className="settings-grid">
        <div className="settings-row" style={{ alignItems: 'flex-start' }}>
          <ActionButton variant="danger" onClick={onClearCache} disabled={clearingCache}>
            <Trash2 size={14} /> {clearingCache ? 'Clearing Cache…' : 'Clear Cache'}
          </ActionButton>
          <p className="settings-hint-small">
            Clear all cached tool results. This can be useful if you want to free up memory or ensure that outdated results are not used.
          </p>
        </div>
      </div>
    </CollapsibleSection>
  )
}

export function WordlistsSection({
  wordlistsDraft,
  wordlistsSaving,
  onAddWordlist,
  onSaveWordlists,
  onUpdateWordlist,
  onRemoveWordlist,
  withCurrentTypeOption,
  withCurrentSpeedOption,
  withCurrentCoverageOption,
}: {
  wordlistsDraft: WordlistEntry[]
  wordlistsSaving: boolean
  onAddWordlist: () => void
  onSaveWordlists: () => Promise<void>
  onUpdateWordlist: (index: number, field: keyof WordlistEntry, value: string) => void
  onRemoveWordlist: (index: number) => void
  withCurrentTypeOption: (current: string) => string[]
  withCurrentSpeedOption: (current: string) => string[]
  withCurrentCoverageOption: (current: string) => string[]
}) {
  return (
    <CollapsibleSection
      title="Wordlists"
      badge={<span className="badge">{wordlistsDraft.length}</span>}
      headerRight={(
        <div className="settings-actions-inline">
          <ActionButton variant="default" onClick={onAddWordlist} disabled={wordlistsSaving}>
            <Plus size={14} /> Add Wordlist
          </ActionButton>
          <ActionButton variant="default" onClick={onSaveWordlists} disabled={wordlistsSaving}>
            <Save size={14} /> {wordlistsSaving ? 'Saving…' : 'Save Wordlists'}
          </ActionButton>
        </div>
      )}
    >
      <div className="wordlist-table">
        <div className="wordlist-head">
          <span>Name</span><span>Type</span><span>Speed</span><span>Coverage</span><span>Path</span><span>Actions</span>
        </div>
        {wordlistsDraft.map((wordlist, index) => (
          <div key={`wordlist-row-${index}`} className="wordlist-row editable">
            <input
              className="settings-input mono wordlist-input"
              value={wordlist.name}
              onChange={e => onUpdateWordlist(index, 'name', e.target.value)}
              placeholder="rockyou"
              disabled={Boolean(wordlist.is_default)}
            />
            <select
              className="settings-input wordlist-input"
              value={wordlist.type}
              onChange={e => onUpdateWordlist(index, 'type', e.target.value)}
            >
              {withCurrentTypeOption(wordlist.type).map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            <select
              className="settings-input wordlist-input"
              value={wordlist.speed}
              onChange={e => onUpdateWordlist(index, 'speed', e.target.value)}
            >
              {withCurrentSpeedOption(wordlist.speed).map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            <select
              className="settings-input wordlist-input"
              value={wordlist.coverage}
              onChange={e => onUpdateWordlist(index, 'coverage', e.target.value)}
            >
              {withCurrentCoverageOption(wordlist.coverage).map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            <input
              className="settings-input mono wordlist-input"
              value={wordlist.path}
              onChange={e => onUpdateWordlist(index, 'path', e.target.value)}
              placeholder="/usr/share/wordlists/rockyou.txt"
            />
            <ActionButton
              variant={wordlist.is_default ? 'default' : 'danger'}
              onClick={() => onRemoveWordlist(index)}
              disabled={wordlistsSaving || Boolean(wordlist.is_default)}
              title={wordlist.is_default ? 'Default wordlists cannot be deleted' : 'Remove row'}
            >
              <Trash2 size={14} />
            </ActionButton>
          </div>
        ))}
      </div>
      <p className="settings-hint">
        Changes are stored in <code>wordlists.json</code>. Entries here override defaults from <code>config.py</code>.
      </p>
    </CollapsibleSection>
  )
}

export function ChatSettingsSection({
  chatPersonality,
  setChatPersonality,
  customPrompt,
  setCustomPrompt,
  personalityPresets,
  summarizationThreshold,
  setSummarizationThreshold,
  contextInjectionChars,
  setContextInjectionChars,
  saving,
  onSave,
}: {
  chatPersonality: string
  setChatPersonality: (v: string) => void
  customPrompt: string
  setCustomPrompt: (v: string) => void
  personalityPresets: PersonalityPreset[]
  summarizationThreshold: string
  setSummarizationThreshold: (v: string) => void
  contextInjectionChars: string
  setContextInjectionChars: (v: string) => void
  saving: boolean
  onSave: () => Promise<void>
}) {
  const options = [...personalityPresets.map(p => ({ id: p.id, label: p.label })), { id: 'custom', label: 'Custom' }]

  return (
    <CollapsibleSection
      title="Chat Widget"
      badge={<span className="section-meta">changes apply immediately</span>}
    >
      <div className="settings-grid">
        <div className="settings-field">
          <label className="settings-label">Personality</label>
          <select
            className="settings-input settings-select-full"
            value={chatPersonality}
            onChange={e => setChatPersonality(e.target.value)}
          >
            {options.map(p => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
          <span className="settings-hint-inline">The system persona sent to the LLM at the start of every chat.</span>
        </div>
        {chatPersonality === 'custom' && (
          <SettingsTextarea
            label="Custom Prompt"
            hint="Your custom system prompt. Saved independently and preserved when switching presets."
            value={customPrompt}
            onChange={setCustomPrompt}
            rows={5}
          />
        )}
        <SettingsField
          label="Summarization Threshold"
          unit="messages"
          hint="When non-summarized message count exceeds this, the oldest half are summarized."
          value={summarizationThreshold}
          onChange={setSummarizationThreshold}
        />
        <SettingsField
          label="Context Injection Chars"
          unit="chars"
          hint="Max characters of session context injected into the chat prompt."
          value={contextInjectionChars}
          onChange={setContextInjectionChars}
        />
      </div>
      <div className="settings-actions">
        <ActionButton variant="success" onClick={onSave} disabled={saving}>
          <Save size={14} /> {saving ? 'Saving…' : 'Save Chat Settings'}
        </ActionButton>
      </div>
    </CollapsibleSection>
  )
}
