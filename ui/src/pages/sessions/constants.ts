export interface StartMode {
  key: 'intelligence' | 'manual' | 'from_template' | 'ai_recon'
  title: string
  description: string
  details: string
  modalDescription: string
  tools: string[]
  placeholder: string
}

export const START_MODES: StartMode[] = [
  {
    key: 'intelligence',
    title: 'Intelligent Attack-Chain',
    description: 'Automated target profiling and attack chain generation.',
    details: 'Best for quick, AI-driven assessments.',
    modalDescription: 'Leverages AI to analyze the target and generate a customized attack chain.',
    tools: [],
    placeholder: 'Domain or org target (target.tld)',
  },
  {
    key: 'manual',
    title: 'Manual Session',
    description: 'Start an empty session and add tools yourself.',
    details: 'Best when you want full manual control.',
    modalDescription: 'Creates a clean session with only target context. No predefined workflow is added, so you can build your own tool chain step-by-step from the session detail page.',
    tools: [],
    placeholder: 'Target URL/domain/IP (example.com)',
  },
  {
    key: 'from_template',
    title: 'From Template',
    description: 'Start from a saved tool template.',
    details: 'Reuse your recurring workflows.',
    modalDescription: 'Creates a session from an existing template. You only set target and choose the saved template; all template tools are copied into the new session.',
    tools: [],
    placeholder: 'Target URL/domain/IP (example.com)',
  },
  {
    key: 'ai_recon',
    title: 'AI Recon',
    description: 'Recon session pre-loaded with the recon pipeline, ready to run.',
    details: 'Builds a session with nmap, whois, dig, http-headers, and whatweb.',
    modalDescription: 'Pre-loaded with the recon pipeline: nmap, whois, dig, http-headers, and whatweb — configured for your target.',
    tools: ['nmap', 'whois', 'dig', 'http-headers', 'whatweb'],
    placeholder: 'Domain or IP (example.com / 10.0.0.1)',
  },
]
