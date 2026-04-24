export interface StartMode {
  key: 'intelligence' | 'manual' | 'from_template' | 'ai_recon' | 'ai_profiling' | 'ai_vuln' | 'ai_osint'
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
  {
    key: 'ai_profiling',
    title: 'AI Profiling',
    description: 'Target-aware profiling pipeline that adapts tools to the target type.',
    details: 'Adds subfinder and theharvester for domains; skips DNS tools for bare IPs.',
    modalDescription: 'Classifies your target (IP, URL, or domain) and builds an adaptive pipeline: nmap, whois, whatweb, http-headers, dig, subfinder, theharvester, gobuster, nikto, and AI analysis.',
    tools: ['nmap', 'whois', 'whatweb', 'http-headers', 'dig', 'subfinder', 'theharvester', 'gobuster', 'nikto'],
    placeholder: 'Domain, URL, or IP (example.com / 10.0.0.1)',
  },
  {
    key: 'ai_vuln',
    title: 'AI Vuln Scan',
    description: 'Vulnerability scanning pipeline: nuclei, sqlmap, dalfox, and nikto.',
    details: 'Checks for CVEs, SQL injection, XSS, and common web misconfigurations.',
    modalDescription: 'Runs a focused vulnerability scan: nuclei (CVE templates), sqlmap (SQLi), dalfox (XSS), and nikto (misconfiguration) — followed by AI analysis of all findings.',
    tools: ['nuclei', 'sqlmap', 'dalfox', 'nikto'],
    placeholder: 'Target URL or domain (https://example.com)',
  },
  {
    key: 'ai_osint',
    title: 'AI OSINT',
    description: 'Passive OSINT pipeline: subfinder, theharvester, gau, and waybackurls.',
    details: 'Domain targets only — no active scanning, no bare IPs.',
    modalDescription: 'Purely passive intelligence gathering: subfinder (subdomains), theharvester (emails & hosts), gau (archived URLs), and waybackurls — followed by AI attack-surface analysis.',
    tools: ['subfinder', 'theharvester', 'gau', 'waybackurls'],
    placeholder: 'Domain only (example.com)',
  },
]
