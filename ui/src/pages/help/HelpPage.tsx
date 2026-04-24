import { useEffect, useState } from 'react'
import { IdeConfigSection, FlagsSection, AuthenticationSection, DemoModeSection } from './HelpSections'
import { IDE_CONFIGS } from './ideConfigs'
import { api } from '../../api'
import './HelpPage.css'

export default function HelpPage() {
  const [activeIde, setActiveIde] = useState('claude')
  const [installPath, setInstallPath] = useState('/path/to/nyxstrike')
  const [pathDetected, setPathDetected] = useState(false)
  const ide = IDE_CONFIGS.find(i => i.id === activeIde) ?? IDE_CONFIGS[0]

  useEffect(() => {
    let mounted = true

    api.getSettings().then(response => {
      const detectedPath = response.settings.server.working_dir?.trim()
      if (!mounted || !detectedPath) {
        return
      }
      setInstallPath(detectedPath)
      setPathDetected(true)
    }).catch(() => {
      if (mounted) {
        setPathDetected(false)
      }
    })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="help-page">
      <IdeConfigSection
        installPath={installPath}
        setInstallPath={setInstallPath}
        pathDetected={pathDetected}
        activeIde={activeIde}
        setActiveIde={setActiveIde}
        ideConfigs={IDE_CONFIGS}
        selectedIde={ide}
      />
      <FlagsSection />
      <AuthenticationSection />
      <DemoModeSection />
    </div>
  )
}
