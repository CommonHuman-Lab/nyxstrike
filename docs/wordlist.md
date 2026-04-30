# Wordlist Manager (`wordlist.sh`)

Lists, searches, resolves, downloads, and registers wordlists used by NyxStrike tools.
Maintains a unified view of wordlists across system paths and the local NyxStrike data
directory — system paths always win, no duplicate files.

---

## Requirements

- **Bash** 4.0+
- **python3** — used for registry read/write and file size display
- **git** — required for `get seclists`
- **wget** or **curl** — required for `get rockyou` (download fallback only)

---

## Usage

```bash
./scripts/wordlist.sh                          # same as 'list'
./scripts/wordlist.sh list                     # all wordlists: name | exists | size | path
./scripts/wordlist.sh status                   # show only missing wordlists
./scripts/wordlist.sh search <keyword>         # filter by name or description
./scripts/wordlist.sh path <name>              # print resolved path (scriptable)
./scripts/wordlist.sh get rockyou              # decompress or download rockyou.txt
./scripts/wordlist.sh get seclists             # clone or update SecLists
./scripts/wordlist.sh add <name> <path> [desc] # register a custom wordlist
./scripts/wordlist.sh help                     # show usage
```

---

## Path Resolution

For every built-in wordlist, the script checks paths in this order:

1. **System path** (e.g. `/usr/share/wordlists/rockyou.txt`) — if found, this is used
2. **Local fallback** (`~/.nyxstrike_data/wordlists/<sub-path>`) — only if not on system

This ensures no double files: if a wordlist is already installed on the system it is
used directly and no local copy is created.

Custom wordlists registered with `add` use whatever path you specify.

---

## Built-in Wordlists

| Name | System Path | Description |
|------|-------------|-------------|
| `rockyou` | `/usr/share/wordlists/rockyou.txt` | Classic 14M password list |
| `john` | `/usr/share/wordlists/john.lst` | John the Ripper default list |
| `dirb-common` | `/usr/share/wordlists/dirb/common.txt` | Common web directories |
| `dirb-big` | `/usr/share/wordlists/dirb/big.txt` | Large web directory list |
| `dirb-small` | `/usr/share/wordlists/dirb/small.txt` | Small web directory list |
| `dirsearch-common` | `/usr/share/wordlists/dirsearch/common.txt` | Common paths for dirsearch |
| `seclists-web-common` | `/usr/share/seclists/Discovery/Web-Content/common.txt` | SecLists common web content |
| `seclists-web-big` | `/usr/share/seclists/Discovery/Web-Content/big.txt` | SecLists big web content |
| `seclists-web-raft-small` | `/usr/share/seclists/Discovery/Web-Content/raft-small-words.txt` | SecLists RAFT small words |
| `seclists-dns` | `/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt` | Top 5000 subdomains |
| `seclists-dns-big` | `/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt` | Top 110k subdomains |
| `seclists-usernames` | `/usr/share/seclists/Usernames/top-usernames-shortlist.txt` | Common usernames |
| `seclists-passwords` | `/usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt` | 10k most common passwords |
| `seclists-passwords-rockyou2021` | `/usr/share/seclists/Passwords/Leaked-Databases/rockyou2021.txt` | rockyou 2021 leak |

---

## Commands

### `list`

Shows all wordlists (built-in + custom registry) with their resolved status:

```
NAME                                EXISTS   SIZE     PATH / DESCRIPTION
─────────────────────────────────────────────────────────────────────────────────
rockyou                             yes      133.4M   /usr/share/wordlists/rockyou.txt [sys]
dirsearch-common                    no       —        Common paths for dirsearch
```

- `[sys]` — resolved from system path
- `[local]` — resolved from local fallback
- `[custom]` — registered via `add`

---

### `status`

Shows only wordlists that are missing from disk, with a hint on how to get them:

```bash
./scripts/wordlist.sh status
```

---

### `search <keyword>`

Filters the list by name or description — case-sensitive substring match:

```bash
./scripts/wordlist.sh search password
./scripts/wordlist.sh search seclists
./scripts/wordlist.sh search dns
```

---

### `path <name>`

Prints the resolved on-disk path for a named wordlist. Exits with code 1 if not found.
Designed for use in other scripts:

```bash
WORDLIST=$(./scripts/wordlist.sh path rockyou)
hydra -L users.txt -P "$WORDLIST" ssh://target
```

```bash
./scripts/wordlist.sh path seclists-web-common
# → /usr/share/seclists/Discovery/Web-Content/common.txt
```

---

### `get rockyou`

Ensures `rockyou.txt` is available. Tries the following in order:

1. Already present at `/usr/share/wordlists/rockyou.txt` — done
2. Already present at local fallback — done
3. Decompress `/usr/share/wordlists/rockyou.txt.gz` in place (needs write permission)
4. Decompress `.gz` to local fallback if system path is not writable
5. Download from GitHub releases to local fallback (uses `wget` or `curl`)

```bash
./scripts/wordlist.sh get rockyou
```

---

### `get seclists`

Ensures SecLists is available. Tries the following in order:

1. `/usr/share/seclists` already exists — print update hint, exit
2. Local `~/.nyxstrike_data/wordlists/seclists/.git` exists — `git pull`
3. `/usr/share/` is writable — clone to `/usr/share/seclists`
4. Fall back to local: clone to `~/.nyxstrike_data/wordlists/seclists`

```bash
./scripts/wordlist.sh get seclists
```

> **Note:** A shallow clone (`--depth 1`) is used to keep download size manageable.
> The full SecLists repo is ~1 GB uncompressed.

---

### `add <name> <path> [description]`

Registers a custom wordlist into the NyxStrike registry
(`.nyxstrike_data/wordlists/wordlists.json`). The file does not need to exist yet —
it will be shown as missing in `list` until the path is populated.

```bash
./scripts/wordlist.sh add my-api-words /opt/wordlists/api-endpoints.txt "Custom API endpoint list"
```

Constraints:
- Name must not conflict with any built-in name
- Path is resolved to absolute before saving
- `python3` or `jq` is required for registry writes

---

## Registry File

Custom wordlists are stored in:

```
.nyxstrike_data/wordlists/wordlists.json
```

Format:

```json
{
  "WORD_LISTS": {
    "my-api-words": {
      "path": "/opt/wordlists/api-endpoints.txt",
      "description": "Custom API endpoint list"
    }
  }
}
```

This file is also read by the NyxStrike server (`config.py`) when resolving wordlist
paths for tool execution.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NYXSTRIKE_DATA_DIR` | `<repo_root>/.nyxstrike_data` | Override the NyxStrike data directory |

---

## Examples

```bash
# Check what's installed
./scripts/wordlist.sh list

# Find everything password-related
./scripts/wordlist.sh search password

# Get the path to use in a tool command
hashcat -a 0 hash.txt "$(./scripts/wordlist.sh path rockyou)"

# Install SecLists if not present
./scripts/wordlist.sh get seclists

# Register a custom list
./scripts/wordlist.sh add company-users /home/user/recon/employees.txt "Harvested employee list"
```

---

## Related

- [`report.sh`](report.md) — generate Markdown reports from session findings
- [`install_tools.sh`](installation_and_flags.md) — installs the security tools that consume these wordlists
- [SecLists](https://github.com/danielmiessler/SecLists) — the upstream wordlist collection
