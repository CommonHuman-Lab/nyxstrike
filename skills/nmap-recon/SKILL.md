---
name: nmap-recon
description: Network reconnaissance workflow using nmap, masscan, and rustscan via NyxStrike tools
---

# nmap-recon

Step-by-step network reconnaissance skill for NyxStrike. Use this skill when a user asks to scan a host, discover open ports, enumerate services, or perform OS detection.

## Workflow

### 1. Fast port discovery (rustscan or masscan)

Start with a fast sweep to identify open ports before running detailed scans.

- Prefer `rustscan` for speed on a single target.
- Prefer `masscan` for large CIDR ranges.

```
run_tool(tool="rustscan", target="<target>", ports="1-65535")
```

### 2. Service & version detection (nmap)

Run nmap against the open ports discovered in step 1 to enumerate services, versions, and scripts.

```
run_tool(tool="nmap", target="<target>", ports="<open_ports>", flags="-sV -sC -O")
```

Useful nmap flag combinations:

| Goal | Flags |
|---|---|
| Service + version detection | `-sV` |
| Default NSE scripts | `-sC` |
| OS detection | `-O` |
| Aggressive (all of the above + traceroute) | `-A` |
| UDP scan | `-sU` |
| Full port range | `-p-` |

### 3. Targeted NSE scripts (optional)

If specific services are found, run targeted NSE scripts for deeper enumeration.

| Service | Suggested scripts |
|---|---|
| SMB (445) | `--script smb-vuln-*,smb-enum-shares` |
| HTTP (80/443) | `--script http-title,http-headers,http-methods` |
| FTP (21) | `--script ftp-anon,ftp-bounce` |
| SSH (22) | `--script ssh-hostkey,ssh-auth-methods` |
| SNMP (161/udp) | `--script snmp-info,snmp-interfaces` |

```
run_tool(tool="nmap_advanced", target="<target>", ports="<port>", scripts="<script_list>")
```

### 4. ARP scan (local network only)

For targets on the same subnet, use arp_scan to identify live hosts before deeper scanning.

```
run_tool(tool="arp_scan", target="<subnet_cidr>")
```

## Tips

- Always confirm scope before scanning. Only scan targets you are authorized to test.
- Start with `-T3` (default timing) and increase to `-T4` only on reliable networks.
- Save output with `-oN`, `-oX`, or `-oG` flags for later analysis; pass via the `output_file` parameter where supported.
- Chain results: feed open ports from rustscan/masscan directly into nmap to avoid redundant full-port scans.

## NyxStrike Tool Reference

| Tool | Use case |
|---|---|
| `nmap` | Service/version/script scanning |
| `nmap_advanced` | NSE script targeting |
| `masscan` | High-speed large-range port sweep |
| `rustscan` | Fast single-target port discovery |
| `arp_scan` | Local subnet host discovery |
