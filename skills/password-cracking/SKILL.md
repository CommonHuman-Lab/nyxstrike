---
name: password-cracking
description: Password hash identification, cracking, and credential brute-forcing using hashid, john, hashcat, hydra, medusa, and ophcrack
---

# password-cracking

Password cracking and credential brute-force workflow for NyxStrike. Use this skill when a user has captured hashes to crack, wants to brute-force a login service, or needs to identify an unknown hash format.

## Workflow

### Step 1 — Identify the hash type (hashid)

Always identify the hash format before cracking. Do not guess.

```
run_tool(tool="hashid", hash="<paste_hash_here>")
```

Common hash types and their hashcat mode numbers:

| Hash | hashcat mode |
|---|---|
| MD5 | 0 |
| SHA-1 | 100 |
| SHA-256 | 1400 |
| SHA-512 | 1700 |
| bcrypt | 3200 |
| NTLM | 1000 |
| Net-NTLMv2 | 5600 |
| WPA2 | 22000 |
| Kerberos 5 AS-REP | 18200 |
| Kerberos 5 TGS | 13100 |

### Step 2 — Dictionary attack (john or hashcat)

**John the Ripper** — best for automatic format detection and many exotic formats:

```
run_tool(tool="john", hash_file="/path/to/hashes.txt",
         wordlist="/usr/share/wordlists/rockyou.txt")

# Force a specific format
run_tool(tool="john", hash_file="/path/to/hashes.txt",
         wordlist="/usr/share/wordlists/rockyou.txt",
         format_type="NT")
```

**Hashcat** — best for speed, GPU acceleration, and rule-based attacks:

```
# Dictionary attack (mode 0)
run_tool(tool="hashcat", hash_file="/path/to/hashes.txt",
         hash_type="1000",
         attack_mode="0",
         wordlist="/usr/share/wordlists/rockyou.txt")

# Dictionary + rules (best64 rule)
run_tool(tool="hashcat", hash_file="/path/to/hashes.txt",
         hash_type="0",
         attack_mode="0",
         wordlist="/usr/share/wordlists/rockyou.txt",
         additional_args="-r /usr/share/hashcat/rules/best64.rule")
```

### Step 3 — Brute-force / mask attack (hashcat)

Use when dictionary attack fails and you know the password format:

```
# 8-character lowercase + digit (e.g. "summer23")
run_tool(tool="hashcat", hash_file="/path/to/hashes.txt",
         hash_type="0",
         attack_mode="3",
         mask="?l?l?l?l?l?l?d?d")
```

Mask charset reference:
- `?l` lowercase letters
- `?u` uppercase letters
- `?d` digits
- `?s` special characters
- `?a` all printable

### Step 4 — Windows NTLM / rainbow tables (ophcrack)

Use ophcrack for Windows NTLM hashes when you have rainbow tables available:

```
run_tool(tool="ophcrack", hash_file="/path/to/ntlm_hashes.txt",
         tables_dir="/path/to/tables")
```

### Step 5 — Network service brute-force (hydra or medusa)

Use after gaining credentials to test for password reuse, or when attacking login services directly.

**Hydra:**

```
# SSH brute-force
run_tool(tool="hydra", target="<target>", service="ssh",
         username="admin",
         password_file="/usr/share/wordlists/rockyou.txt")

# HTTP form brute-force
run_tool(tool="hydra", target="<target>", service="http-post-form",
         username_file="/usr/share/seclists/Usernames/top-usernames-shortlist.txt",
         password_file="/usr/share/wordlists/rockyou.txt",
         additional_args='"/login:username=^USER^&password=^PASS^:Invalid"')
```

**Medusa** (alternative to Hydra, stronger on some protocols):

```
run_tool(tool="medusa", target="<target>", module="ssh",
         username="root",
         password_file="/usr/share/wordlists/rockyou.txt")
```

## Service-to-tool selection guide

| Service | Tool |
|---|---|
| SSH | hydra, medusa |
| FTP | hydra, medusa |
| HTTP form POST | hydra |
| SMB | netexec (see `smb-enum` skill) |
| RDP | hydra |
| MySQL | hydra, medusa |
| NTLM hashes | hashcat (mode 1000), john |
| Net-NTLMv2 | hashcat (mode 5600) |
| bcrypt | john (slow), hashcat (mode 3200) |

## Tips

- Start with `rockyou.txt` + `best64.rule` — covers most real-world passwords.
- For corporate targets, build a custom wordlist from the company name, domain, and OSINT findings.
- GPU hashcat is orders of magnitude faster than CPU john for MD5/NTLM — use it when available.
- Never skip `hashid` — cracking the wrong format wastes significant time.

## NyxStrike Tool Reference

| Tool | Use case |
|---|---|
| `hashid` | Identify unknown hash type |
| `john` | Dictionary + format-aware cracking |
| `hashcat` | GPU-accelerated dictionary/mask/rule cracking |
| `hydra` | Network login brute-forcer |
| `medusa` | Alternative network login brute-forcer |
| `patator` | Multi-purpose brute-forcer |
| `ophcrack` | NTLM rainbow table cracker |
