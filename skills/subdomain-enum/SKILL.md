---
name: subdomain-enum
description: Subdomain and DNS enumeration workflow using subfinder, amass, dnsenum, fierce, theharvester, gau, and waybackurls
---

# subdomain-enum

Subdomain and DNS reconnaissance workflow for NyxStrike. Use this skill when a user wants to enumerate subdomains, discover DNS records, find email addresses, or build a full attack surface map for a domain.

## Workflow

### 1. Passive subdomain discovery (subfinder)

Start passive — no direct DNS queries to the target, low noise:

```
run_tool(tool="subfinder", domain="<target.com>", silent=true, all_sources=true)
```

### 2. Active subdomain enumeration (amass)

Follow up with amass for active DNS brute-force and graph-based enumeration:

```
# Passive mode (intelligence gathering only)
run_tool(tool="amass", domain="<target.com>", mode="enum",
         additional_args="-passive")

# Active mode (DNS resolution, zone transfers)
run_tool(tool="amass", domain="<target.com>", mode="enum",
         additional_args="-active -brute")
```

### 3. DNS zone transfer and record enumeration (dnsenum)

Attempt zone transfers and enumerate MX, NS, A, CNAME records:

```
run_tool(tool="dnsenum", domain="<target.com>")
```

### 4. DNS reconnaissance (fierce)

Fierce does brute-force subdomain discovery and identifies nearby IP ranges:

```
run_tool(tool="fierce", domain="<target.com>")
```

### 5. Email, host, and URL harvesting (theharvester)

Collect emails, hosts, and IPs from public sources (Google, Bing, LinkedIn, etc.):

```
run_tool(tool="theharvester", domain="<target.com>")
```

### 6. Historical URL discovery (gau + waybackurls)

Pull archived URLs to find forgotten endpoints, old parameters, and legacy paths:

```
run_tool(tool="gau", domain="<target.com>")
run_tool(tool="waybackurls", domain="<target.com>")
```

Feed the results into `web-vuln` skill tools (nuclei, sqlmap) for vulnerability testing.

### 7. WHOIS lookup

Gather registration info, nameservers, and ASN data:

```
run_tool(tool="whois", target="<target.com>")
```

### 8. HTTP probe discovered subdomains (httpx)

After collecting subdomains, probe which ones are live:

```
run_tool(tool="httpx", target="<subdomains_file_or_list>",
         probe=true, title=true, status_code=true, tech_detect=true)
```

## Attack surface map — full pipeline

```
subfinder → amass → dnsenum/fierce → theharvester
                       ↓
                    httpx probe
                       ↓
              web-recon + web-vuln skills
```

## Tips

- Run subfinder and amass in parallel — they use different data sources.
- Always probe discovered subdomains with httpx before scanning — many will be dead.
- Historical URLs from gau/waybackurls often expose parameters that are still live but not linked from the main site.
- Zone transfers (dnsenum) are rare but high-value — always attempt them.

## NyxStrike Tool Reference

| Tool | Use case |
|---|---|
| `subfinder` | Passive subdomain discovery |
| `amass` | Active/passive subdomain + graph enumeration |
| `dnsenum` | DNS zone transfer + record enumeration |
| `fierce` | DNS brute-force + nearby IP ranges |
| `theharvester` | Email, host, IP OSINT from public sources |
| `gau` | Historical URL discovery (AlienVault/Wayback) |
| `waybackurls` | Wayback Machine URL archive |
| `whois` | Domain registration + ASN info |
| `httpx` | Probe live subdomains |
| `bbot` | Comprehensive OSINT + recon automation |
