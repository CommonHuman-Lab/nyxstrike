import { RefreshCw, XCircle } from 'lucide-react'
import { useSettingsData } from './settings/useSettingsData'
import {
  RuntimeConfigSection,
  ServerControlsSection,
  ServerEnvironmentSection,
  WordlistsSection,
} from './settings/SettingsSections'
import './SettingsPage.css'

export default function SettingsPage() {
  const {
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
    withCurrentTypeOption,
    withCurrentSpeedOption,
    withCurrentCoverageOption,
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
      <ServerEnvironmentSection settings={settings} />

      <RuntimeConfigSection
        timeout={timeout}
        cacheSize={cacheSize}
        cacheTtl={cacheTtl}
        toolTtl={toolTtl}
        setTimeout_={setTimeout_}
        setCacheSize={setCacheSize}
        setCacheTtl={setCacheTtl}
        setToolTtl={setToolTtl}
        saving={saving}
        onSave={saveRuntime}
      />

      <ServerControlsSection
        clearingCache={clearingCache}
        onClearCache={clearCache}
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
    </div>
  )
}
