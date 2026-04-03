import { useState } from 'react'
import { IdeConfigSection, FlagsSection, AuthenticationSection, DemoModeSection } from './HelpSections'
import { IDE_CONFIGS } from './ideConfigs'
import './HelpPage.css'

export default function HelpPage() {
  const [activeIde, setActiveIde] = useState('claude')
  const [installPath, setInstallPath] = useState('/path/to/hexstrike-ai-community-edition')
  const ide = IDE_CONFIGS.find(i => i.id === activeIde) ?? IDE_CONFIGS[0]

  return (
    <div className="help-page">
      <IdeConfigSection
        installPath={installPath}
        setInstallPath={setInstallPath}
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
