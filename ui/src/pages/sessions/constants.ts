export interface StartMode {
  key: 'intelligence' | 'comprehensive' | 'reconnaissance' | 'vulnerability_hunting' | 'OSINT' | 'api_security' | 'internal_network_ad' | 'manual' | 'from_template'
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
    title: 'Intelligent Profiling',
    description: 'Automated target profiling and attack chain generation.',
    details: 'Best for quick, comprehensive insights on a target.',
    modalDescription: 'Leverages AI to analyze the target and generate a customized attack chain. This mode is ideal when you want a smart, efficient workflow that adapts to the target’s unique characteristics, providing actionable insights with minimal setup.',
    tools: ['analyze-target', 'smart-scan', 'technology-detection', 'create-attack-chain', 'vulnx', 'httpx'],
    placeholder: 'Domain or org target (target.tld)',
  },
  {
    key: 'comprehensive',
    title: 'Comprehensive Assessment',
    description: 'Balanced full-chain workflow from recon to vulnerability checks.',
    details: 'Best default for unknown targets.',
    modalDescription: 'Builds a broad, practical workflow that starts with target profiling and surface mapping, then moves into prioritized vulnerability validation. This is designed for cases where you want full context and a structured path from discovery to actionable findings.',
    tools: ['nmap', 'httpx', 'katana', 'nuclei', 'nikto', 'ffuf', 'testssl', 'arjun'],
    placeholder: 'Target URL/domain/IP (example.com)',
  },
  {
    key: 'reconnaissance',
    title: 'Reconnaissance',
    description: 'Discovery-first workflow for assets, endpoints, and technologies.',
    details: 'Use when mapping attack surface.',
    modalDescription: 'Focuses on enumeration and intelligence gathering with minimal intrusive testing. It maps hosts, services, paths, and technologies so you can decide where deeper testing should happen next.',
    tools: ['subfinder', 'amass', 'httpx', 'katana', 'waybackurls', 'gau', 'arjun', 'whatweb', 'paramspider', 'wafw00f'],
    placeholder: 'Scope target (example.com or 10.0.0.0/24)',
  },
  {
    key: 'vulnerability_hunting',
    title: 'Vulnerability Hunting',
    description: 'Vulnerability-focused chain prioritizing exploitable findings.',
    details: 'Use when recon is already known.',
    modalDescription: 'Runs targeted security checks against known attack surface to quickly identify high-value weaknesses. This mode biases toward validating likely vulnerabilities and producing results you can triage and act on fast.',
    tools: ['nuclei', 'sqlmap', 'dalfox', 'jaeles', 'nikto', 'wpscan', 'arjun', 'jwt-analyzer', 'graphql-scanner', 'zaproxy'],
    placeholder: 'Web/API target (https://target.tld)',
  },
  {
    key: 'OSINT',
    title: 'OSINT Collection',
    description: 'Intelligence and external footprint gathering for a target.',
    details: 'Useful before active probing.',
    modalDescription: 'Collects passive intelligence from public sources to understand exposure before active scanning. This includes historical URLs, publicly indexed assets, and reconnaissance artifacts useful for planning follow-up testing.',
    tools: ['theHarvester', 'subfinder', 'amass', 'waymore', 'waybackurls', 'whois', 'gau', 'dnsenum'],
    placeholder: 'Domain or org target (target.tld)',
  },
  {
    key: 'api_security',
    title: 'API Security',
    description: 'API-focused workflow for endpoint, auth, and parameter weakness detection.',
    details: 'Best for REST/GraphQL services and modern API stacks.',
    modalDescription: 'Targets API attack surfaces end-to-end: endpoint discovery, hidden parameter mining, schema analysis, auth/token checks, and vulnerability validation. Use this when APIs are primary scope or where mobile/backend services expose extensive routes.',
    tools: ['httpx', 'katana', 'arjun', 'x8', 'paramspider', 'api-schema-analyzer', 'graphql-scanner', 'jwt-analyzer', 'nuclei', 'sqlmap', 'ffuf'],
    placeholder: 'API base URL (https://api.target.tld)',
  },
  {
    key: 'internal_network_ad',
    title: 'Internal Network + AD',
    description: 'Internal host discovery with SMB/AD enumeration and lateral movement checks.',
    details: 'Best for enterprise network and Active Directory testing.',
    modalDescription: 'Builds an internal assessment chain focused on host/service discovery, SMB/NetBIOS/RPC enumeration, domain intel extraction, and AD-aware access checks. Use for corp ranges, domain-joined segments, and post-foothold validation.',
    tools: ['nmap_advanced', 'autorecon', 'enum4linux-ng', 'smbmap', 'rpcclient', 'nxc', 'ldapdomaindump', 'impacket-ad-enum', 'responder', 'evil-winrm'],
    placeholder: 'Internal target (10.0.0.15 or 10.0.0.0/24)',
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
