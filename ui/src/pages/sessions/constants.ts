export interface StartMode {
  key: 'comprehensive' | 'reconnaissance' | 'vulnerability_hunting' | 'osint' | 'manual' | 'from_template'
  title: string
  description: string
  details: string
  modalDescription: string
  tools: string[]
  placeholder: string
}

export const START_MODES: StartMode[] = [
  {
    key: 'comprehensive',
    title: 'Comprehensive Assessment',
    description: 'Balanced full-chain workflow from recon to vulnerability checks.',
    details: 'Best default for unknown targets.',
    modalDescription: 'Builds a broad, practical workflow that starts with target profiling and surface mapping, then moves into prioritized vulnerability validation. This is designed for cases where you want full context and a structured path from discovery to actionable findings.',
    tools: ['nmap', 'httpx', 'katana', 'nuclei', 'nikto', 'ffuf'],
    placeholder: 'Target URL/domain/IP (example.com)',
  },
  {
    key: 'reconnaissance',
    title: 'Reconnaissance',
    description: 'Discovery-first workflow for assets, endpoints, and technologies.',
    details: 'Use when mapping attack surface.',
    modalDescription: 'Focuses on enumeration and intelligence gathering with minimal intrusive testing. It maps hosts, services, paths, and technologies so you can decide where deeper testing should happen next.',
    tools: ['subfinder', 'amass', 'httpx', 'katana', 'waybackurls', 'gau'],
    placeholder: 'Scope target (example.com or 10.0.0.0/24)',
  },
  {
    key: 'vulnerability_hunting',
    title: 'Vulnerability Hunting',
    description: 'Vulnerability-focused chain prioritizing exploitable findings.',
    details: 'Use when recon is already known.',
    modalDescription: 'Runs targeted security checks against known attack surface to quickly identify high-value weaknesses. This mode biases toward validating likely vulnerabilities and producing results you can triage and act on fast.',
    tools: ['nuclei', 'sqlmap', 'dalfox', 'jaeles', 'nikto', 'wpscan'],
    placeholder: 'Web/API target (https://target.tld)',
  },
  {
    key: 'osint',
    title: 'OSINT Collection',
    description: 'Intelligence and external footprint gathering for a target.',
    details: 'Useful before active probing.',
    modalDescription: 'Collects passive intelligence from public sources to understand exposure before active scanning. This includes historical URLs, publicly indexed assets, and reconnaissance artifacts useful for planning follow-up testing.',
    tools: ['theharvester', 'subfinder', 'amass', 'gau', 'waybackurls'],
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
]
