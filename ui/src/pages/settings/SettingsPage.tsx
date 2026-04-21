import { Palette, RefreshCw, Trash2, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { InformationModal } from '../../components/InformationModal'
import { THEME_OPTIONS, type ThemeId } from '../../app/themes'
import { useSettingsData } from './useSettingsData'
import {
  ChatSettingsSection,
  RuntimeConfigSection,
  ServerEnvironmentSection,
  WordlistsSection,
} from './SettingsSections'
import './SettingsPage.css'

export default function SettingsPage({
  themeId,
  setThemeId,
  reduceTextureEffects,
  setReduceTextureEffects,
}: {
  themeId: ThemeId
  setThemeId: (theme: ThemeId) => void
  reduceTextureEffects: boolean
  setReduceTextureEffects: (value: boolean) => void
}) {
  const [themeModalOpen, setThemeModalOpen] = useState(false)
  const [themePreviewId, setThemePreviewId] = useState<ThemeId>(themeId)
  const [themeSelectionId, setThemeSelectionId] = useState<ThemeId>(themeId)

  useEffect(() => {
    if (!themeModalOpen) {
      setThemePreviewId(themeId)
      setThemeSelectionId(themeId)
      return
    }
    document.documentElement.setAttribute('data-theme', themePreviewId)
  }, [themeModalOpen, themePreviewId, themeId])

  function closeThemeModal() {
    document.documentElement.setAttribute('data-theme', themeId)
    setThemePreviewId(themeId)
    setThemeSelectionId(themeId)
    setThemeModalOpen(false)
  }

  function applyThemeSelection() {
    setThemeId(themeSelectionId)
    setThemeModalOpen(false)
  }

  const {
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
    saveChatSettings,
    clearCache,
    withCurrentTypeOption,
    withCurrentSpeedOption,
    withCurrentCoverageOption,
    chatPersonality,
    customPrompt,
    personalityPresets,
    summarizationThreshold,
    contextInjectionChars,
    setChatPersonality,
    setCustomPrompt,
    setSummarizationThreshold,
    setContextInjectionChars,
  } = useSettingsData()

  if (loading) {
    return (
      <div className="loading-state">
        <RefreshCw size={20} className="spin" color="var(--green)" />
        <p>Loading settings…</p>
      </div>
    )
  }

  if (error) {
    return <div className="error-banner"><XCircle size={16} /> {error}</div>
  }

  if (!settings) return null

  return (
    <div className="settings-page">
      <InformationModal
        isOpen={themeModalOpen}
        title="Choose Theme"
        description="Preview themes live, then apply your selection."
        className="theme-picker-modal"
        primaryLabel="Apply Theme"
        primaryVariant="success"
        secondaryLabel="Cancel"
        onPrimary={applyThemeSelection}
        onSecondary={closeThemeModal}
        onClose={closeThemeModal}
      >
        <label className="theme-picker-toggle-row">
          <input
            type="checkbox"
            checked={reduceTextureEffects}
            onChange={e => setReduceTextureEffects(e.target.checked)}
          />
          <span className="theme-picker-toggle-text">Reduce background texture effects</span>
        </label>
        <div className="theme-picker-grid">
          {THEME_OPTIONS.map(option => (
            <button
              key={option.id}
              className={`theme-picker-card${themeSelectionId === option.id ? ' active' : ''}`}
              onClick={() => {
                setThemeSelectionId(option.id)
                setThemePreviewId(option.id)
              }}
              type="button"
            >
              <span className="theme-picker-card-label">{option.label}</span>
              <span className="theme-picker-card-hint">{option.hint}</span>
            </button>
          ))}
        </div>
      </InformationModal>

      <div className="kpi-row settings-appearance-row">
        <div
          className="stat-card settings-appearance-card settings-appearance-card--action settings-appearance-card--clickable"
          role="button"
          tabIndex={0}
          onClick={() => setThemeModalOpen(true)}
          onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              setThemeModalOpen(true)
            }
          }}
          title="Open theme picker"
        >
          <div className="stat-icon" style={{ color: 'var(--accent)' }}><Palette size={20} /></div>
          <div className="stat-body settings-appearance-body">
            <div className="stat-label">Appearance</div>
            <div className="stat-value settings-appearance-value">{THEME_OPTIONS.find(t => t.id === themeId)?.label ?? themeId}</div>
            <div className="stat-sub">Preview and apply a theme instantly</div>
            <div className="settings-appearance-tap-hint mono">Click card to open picker</div>
          </div>
        </div>

        <div className="stat-card settings-appearance-card settings-maintenance-card">
          <div className="stat-icon" style={{ color: 'var(--warning)' }}><Trash2 size={20} /></div>
          <div className="stat-body settings-appearance-body">
            <div className="stat-label">Maintenance</div>
            <div className="stat-value settings-appearance-value">Cache</div>
            <div className="stat-sub">Clear cached tool results and force fresh data</div>
            <div className="settings-appearance-actions">
              <button className="btn-secondary settings-appearance-btn" onClick={clearCache} disabled={clearingCache}>
                {clearingCache ? 'Clearing…' : 'Clear Cache'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <ServerEnvironmentSection settings={settings} />

      <RuntimeConfigSection
        timeout={timeout}
        requestTimeout={requestTimeout}
        inactivityTimeout={inactivityTimeout}
        maxRuntime={maxRuntime}
        cacheSize={cacheSize}
        cacheTtl={cacheTtl}
        toolTtl={toolTtl}
        setTimeout_={setTimeout_}
        setRequestTimeout={setRequestTimeout}
        setInactivityTimeout={setInactivityTimeout}
        setMaxRuntime={setMaxRuntime}
        setCacheSize={setCacheSize}
        setCacheTtl={setCacheTtl}
        setToolTtl={setToolTtl}
        saving={saving}
        onSave={saveRuntime}
      />

      <WordlistsSection
        wordlistsDraft={wordlistsDraft}
        wordlistsSaving={wordlistsSaving}
        onAddWordlist={addWordlist}
        onSaveWordlists={saveWordlists}
        onUpdateWordlist={updateWordlist}
        onRemoveWordlist={removeWordlist}
        withCurrentTypeOption={withCurrentTypeOption}
        withCurrentSpeedOption={withCurrentSpeedOption}
        withCurrentCoverageOption={withCurrentCoverageOption}
      />

      <ChatSettingsSection
        chatPersonality={chatPersonality}
        setChatPersonality={setChatPersonality}
        customPrompt={customPrompt}
        setCustomPrompt={setCustomPrompt}
        personalityPresets={personalityPresets}
        summarizationThreshold={summarizationThreshold}
        setSummarizationThreshold={setSummarizationThreshold}
        contextInjectionChars={contextInjectionChars}
        setContextInjectionChars={setContextInjectionChars}
        saving={saving}
        onSave={saveChatSettings}
      />
    </div>
  )
}
