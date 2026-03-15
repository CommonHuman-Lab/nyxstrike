---
name: smb-enum
description: SMB and Windows network enumeration workflow using nmap, smbmap, enum4linux, netexec, and nbtscan for share discovery, user enumeration, and lateral movement
---

# smb-enum

SMB and Windows network enumeration workflow for HexStrike AI. Use this skill when a user wants to enumerate SMB shares, discover Windows users and groups, test for null sessions, spray credentials, or assess Active Directory exposure.

## Workflow

### Step 1 — Identify SMB hosts and version (nmap)

Start by confirming SMB is open and check the version for known vulnerabilities:

```
run_tool(tool="nmap", target="<target>",
         ports="445,139",
         additional_args="-sV -sC --script smb-vuln-*,smb-security-mode,smb2-security-mode")
```

Key NSE scripts for SMB:

| Script | Purpose |
|---|---|
| `smb-vuln-ms17-010` | EternalBlue check |
| `smb-vuln-cve-2020-0796` | SMBGhost check |
| `smb-security-mode` | Null session, message signing |
| `smb2-security-mode` | SMBv2 signing status |
| `smb-enum-shares` | List accessible shares |
| `smb-enum-users` | Enumerate domain/local users |

### Step 2 — NetBIOS and host discovery (nbtscan)

For Windows networks, get NetBIOS names and identify domain controllers:

```
run_tool(tool="nbtscan", target="<subnet_cidr>")
```

### Step 3 — Share enumeration (smbmap)

List shares and permissions without credentials (null session), then with credentials:

```
# Null session
run_tool(tool="smbmap", target="<target>")

# With credentials
run_tool(tool="smbmap", target="<target>",
         additional_args="-u '<username>' -p '<password>' -d '<domain>'")

# Recursive listing of a share
run_tool(tool="smbmap", target="<target>",
         additional_args="-u '<username>' -p '<password>' -R <sharename>")
```

### Step 4 — Full SMB/RPC enumeration (enum4linux)

Enumerate users, groups, shares, password policy, and OS info in one pass:

```
# Full auto enumeration
run_tool(tool="enum4linux", target="<target>", additional_args="-a")

# Users only
run_tool(tool="enum4linux", target="<target>", additional_args="-U")

# Password policy
run_tool(tool="enum4linux", target="<target>", additional_args="-P")
```

### Step 5 — Credential testing and lateral movement (netexec)

Test credentials across hosts, run modules, and move laterally:

```
# Test credentials over SMB
run_tool(tool="netexec", target="<target>", protocol="smb",
         username="<user>", password="<pass>")

# Spray a password across a subnet
run_tool(tool="netexec", target="<cidr>", protocol="smb",
         username="administrator", password="Password123")

# Dump SAM database (requires admin)
run_tool(tool="netexec", target="<target>", protocol="smb",
         username="<user>", password="<pass>",
         module="--sam")

# Pass the hash (PTH)
run_tool(tool="netexec", target="<target>", protocol="smb",
         username="<user>",
         additional_args="-H <NTLM_hash>")

# WinRM access check
run_tool(tool="netexec", target="<target>", protocol="winrm",
         username="<user>", password="<pass>")

# LDAP enumeration (Active Directory)
run_tool(tool="netexec", target="<dc_ip>", protocol="ldap",
         username="<user>", password="<pass>",
         module="--users")
```

## Vulnerability quick-checks

| Vulnerability | Check |
|---|---|
| EternalBlue (MS17-010) | `nmap --script smb-vuln-ms17-010` |
| SMBGhost (CVE-2020-0796) | `nmap --script smb-vuln-cve-2020-0796` |
| Null session | `smbmap -H <target>` (no creds) |
| Anonymous RPC | `enum4linux -a <target>` |
| Weak password policy | `enum4linux -P <target>` |
| Pass-the-hash | `netexec smb -H <hash>` |

## Typical engagement flow

```
nbtscan → identify hosts + domain
    ↓
nmap smb-vuln-* → check for EternalBlue/SMBGhost
    ↓
enum4linux -a → users, groups, shares, policy
    ↓
smbmap → share permissions + content
    ↓
netexec smb → credential spray / PTH / SAM dump
    ↓
exploitation skill (if EternalBlue confirmed)
```

## Tips

- Null sessions are less common in modern Windows but always worth checking — they give free user enumeration.
- Signing disabled + local admin reuse → classic PTH attack path via netexec.
- `enum4linux -a` is noisy but comprehensive — use it after confirming the target is in scope.
- Password spraying: use a single password per round with a long delay to avoid account lockout — check lockout policy with `enum4linux -P` first.
- SMBv1 present → high likelihood of EternalBlue (MS17-010) — escalate to exploitation skill.

## HexStrike Tool Reference

| Tool | Use case |
|---|---|
| `nmap` | SMB version + NSE vuln scripts |
| `nbtscan` | NetBIOS name and domain discovery |
| `smbmap` | Share enumeration + file listing |
| `enum4linux` | Full SMB/RPC enumeration (users, groups, policy) |
| `netexec` | Credential testing, PTH, SAM dump, lateral movement |
