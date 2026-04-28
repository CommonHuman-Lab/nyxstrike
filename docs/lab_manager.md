# Lab Manager (`lab.sh`)

The NyxStrike Lab Manager is a Bash-based Docker lab launcher that spins up and tears
down intentionally vulnerable security environments for practice, research, and tool
testing. All labs run as named Docker containers with the `nyxstrike-` prefix, making
them easy to track and clean up independently of the main NyxStrike server.

---

## Requirements

- **Docker** — installed and daemon running (`docker info` must succeed)
- **Bash** 4.0+
- Internet access on first run (to pull Docker images)
- `nc` (netcat) — used internally to poll port readiness

---

## File Structure

```
scripts/
  lab.sh                        # Main entrypoint / interactive menu
  labs/
    _common.sh                  # Shared helpers sourced by every lab script
    juiceshop.sh                # OWASP Juice Shop
    dvwa.sh                     # Damn Vulnerable Web App
    metasploitable.sh           # Metasploitable2
    webgoat.sh                  # OWASP WebGoat
    htb_style.sh                # CTFd + Struts2 challenge
    kioptrix.sh                 # VulnHub Kioptrix Level 1
    vulnad.sh                   # Vulnerable Active Directory (Samba4)
    vulnad/
      Dockerfile                # Samba4 AD DC image definition
      entrypoint.sh             # Provisions AD domain on first boot
      populate_vulnad.py        # Seeds AD with realistic attack paths
```

---

## Usage

### Interactive menu (default)

```bash
./scripts/lab.sh
# or explicitly
./scripts/lab.sh menu
```

Drops into an interactive prompt:

```
  lab> start 1       # start Juice Shop
  lab> stop 1        # stop Juice Shop
  lab> status        # show all running lab containers
  lab> list          # list available labs
  lab> start all     # start every lab
  lab> stop all      # stop every lab
  lab> quit          # exit
```

### Non-interactive (scripting / CI)

All commands can be passed directly as arguments — no interactive prompt is opened:

```bash
./scripts/lab.sh list
./scripts/lab.sh status
./scripts/lab.sh start 1
./scripts/lab.sh stop 1
./scripts/lab.sh start all
./scripts/lab.sh stop all
./scripts/lab.sh help
```

---

## Available Labs

| ID | Name | Description | Default Port(s) |
|----|------|-------------|-----------------|
| 1 | **Juice Shop** | OWASP Juice Shop — OWASP Top 10 + 82 challenges | `3000` |
| 2 | **DVWA** | Damn Vulnerable Web App — PHP/MySQL classic | `8080` |
| 3 | **Metasploitable2** | Linux VM with intentionally vulnerable services | `8081`, `2222`, `445`, `3306`, `5900`, `6667` |
| 4 | **WebGoat** | OWASP WebGoat — lesson-based labs | `8888` |
| 5 | **HTB Style** | CTFd scoreboard + Struts2 CVE-2017-5638 challenge | `8000` (CTFd), `8090` (target) |
| 6 | **Kioptrix** | VulnHub Kioptrix Level 1 — classic boot2root | `8082`, `4445` |
| 7 | **VulnAD** | Vulnerable Active Directory via Samba4 | `389`, `88`, `4445` |

---

## Lab Details

### 1 — OWASP Juice Shop

A modern Node.js web application covering all OWASP Top 10 vulnerability categories
with an integrated challenge tracker.

| | |
|---|---|
| **Image** | `bkimminich/juice-shop:latest` |
| **URL** | `http://127.0.0.1:3000` |
| **Admin credentials** | `admin@juice-sh.op` / `admin123` |
| **Challenges** | 82 tasks — XSS, SQLi, IDOR, broken auth, insecure deserialization, and more |

```bash
./scripts/lab.sh start 1
```

---

### 2 — DVWA (Damn Vulnerable Web App)

Classic PHP/MySQL training platform. Vulnerability difficulty is adjustable between
Low, Medium, High, and Impossible inside the app.

| | |
|---|---|
| **Image** | `vulnerables/web-dvwa:latest` |
| **URL** | `http://127.0.0.1:8080` |
| **Credentials** | `admin` / `password` |
| **First run** | Visit `/setup.php` and click **Create / Reset Database** |
| **Coverage** | SQLi, XSS, CSRF, file inclusion, command injection, file upload |

```bash
./scripts/lab.sh start 2
```

---

### 3 — Metasploitable2

A Linux virtual machine image pre-loaded with intentionally vulnerable services — the
classic Metasploit practice target.

| | |
|---|---|
| **Image** | `tleemcjr/metasploitable2:latest` |
| **HTTP** | `http://127.0.0.1:8081` |
| **SSH** | `ssh msfadmin@127.0.0.1 -p 2222` (password: `msfadmin`) |
| **FTP** | `ftp 127.0.0.1 21` — anonymous login enabled |
| **MySQL** | `mysql -h 127.0.0.1 -u root` — no password |
| **SMB** | `smbclient -L //127.0.0.1` |
| **VNC** | `vncviewer 127.0.0.1:5900` — no password |

> **Warning:** This container is intentionally vulnerable. Do not expose it on a public network.

Notable CVEs present:
- `vsftpd 2.3.4` backdoor (port 21)
- `Samba usermap_script` (port 445) — CVE-2007-2447
- `UnrealIRCd` backdoor (port 6667)
- `distcc` RCE (port 3632)

```bash
./scripts/lab.sh start 3
```

---

### 4 — WebGoat

OWASP WebGoat is a deliberately insecure Java web application with structured,
lesson-based exercises — the closest open-source equivalent to PortSwigger Web Academy.

| | |
|---|---|
| **Image** | `webgoat/webgoat:latest` |
| **WebGoat URL** | `http://127.0.0.1:8888/WebGoat` |
| **WebWolf URL** | `http://127.0.0.1:8888/WebWolf` |
| **Credentials** | Register a new account on first visit |
| **Coverage** | SQLi, XSS, XXE, JWT attacks, IDOR, SSRF, path traversal, broken auth, crypto |

```bash
./scripts/lab.sh start 4
```

---

### 5 — HTB Style (CTFd + Vulnerable Challenge)

Runs a full [CTFd](https://ctfd.io) scoreboard alongside a vulnerable application,
replicating the HackTheBox experience locally.

| | |
|---|---|
| **CTFd (scoreboard)** | `http://127.0.0.1:8000` — complete the setup wizard on first visit |
| **Challenge target** | `http://127.0.0.1:8090` |
| **Vulnerability** | Apache Struts2 CVE-2017-5638 — unauthenticated RCE via Content-Type header |
| **CVSSv3** | 10.0 Critical |

Suggested workflow:
1. Get RCE on the challenge container
2. Read a flag file (create one yourself at `/root/flag.txt`)
3. Submit the flag through the CTFd interface

```bash
./scripts/lab.sh start 5
```

---

### 6 — Kioptrix Level 1

The classic VulnHub beginner boot2root machine. Attack paths mirror real-world
late-90s / early-2000s vulnerabilities still encountered in legacy environments.

| | |
|---|---|
| **HTTP** | `http://127.0.0.1:8082` |
| **SMB** | `smbclient -L //127.0.0.1 -p 4445 -N` |
| **Apache CVE** | CVE-2002-0082 — OpenFuck / mod_ssl overflow |
| **Samba CVE** | CVE-2003-0201 — trans2open buffer overflow |

> **Note:** If the community Docker image is unavailable, the script falls back to a
> Samba container that exposes the same SMB attack surface. For full fidelity, import
> the original OVA into VirtualBox from
> [VulnHub](https://www.vulnhub.com/entry/kioptrix-level-1,22/).

```bash
./scripts/lab.sh start 6
```

---

### 7 — VulnAD (Vulnerable Active Directory)

A Samba4 Active Directory Domain Controller pre-seeded with the same attack paths
as the original [VulnAD](https://github.com/WazeHell/vulnerable-AD) PowerShell script
by [@wazehell](https://github.com/WazeHell). Runs entirely on Linux — no Windows
license required.

| | |
|---|---|
| **Domain** | `vulnad.local` |
| **DC hostname** | `dc1.vulnad.local` |
| **Administrator** | `Administrator` / `P@ssw0rd123!` |
| **LDAP** | `ldap://127.0.0.1:389` |
| **Kerberos** | `127.0.0.1:88` |
| **SMB** | `127.0.0.1:4445` |

#### Attack paths seeded

| Path | Detail |
|------|--------|
| **Kerberoasting** | `mssql_svc` / `http_svc` / `exchange_svc` with SPNs registered; one has a weak password from the common password list |
| **AS-REP Roasting** | 4 random users with `DONT_REQUIRE_PREAUTH` set and weak passwords |
| **DCSync** | 3 users granted `Replicating Directory Changes` ACEs on the domain root |
| **Password in description** | 4 users with cleartext passwords stored in the AD `description` field |
| **Password spraying** | 8 users sharing the password `ncc1701` |
| **Default password** | 3 users with `Changeme123!` and `ChangePasswordAtLogon` set |
| **DnsAdmins abuse** | 3 users + 1 nested group added to `DnsAdmins` |
| **Bad ACLs** | `GenericAll`, `GenericWrite`, `WriteDACL`, `WriteOwner` across Normal → Mid → High group chain |

#### Quick-start attack examples

```bash
# Kerberoasting
GetUserSPNs.py vulnad.local/Administrator:'P@ssw0rd123!' -dc-ip 127.0.0.1 -request

# AS-REP Roasting
GetNPUsers.py vulnad.local/ -usersfile users.txt -dc-ip 127.0.0.1 -no-pass

# DCSync
secretsdump.py vulnad.local/dcsync_user@127.0.0.1

# BloodHound collection
bloodhound-python -u Administrator -p 'P@ssw0rd123!' -d vulnad.local -ns 127.0.0.1 -c All
```

```bash
./scripts/lab.sh start 7
```

---

## Starting All Labs

```bash
./scripts/lab.sh start all
```

Starts every lab in sequence. Failures are non-fatal — the script reports a warning and
continues to the next lab. Useful for standing up a full practice environment in one
command.

---

## Checking Status

```bash
./scripts/lab.sh status
```

Lists all running `nyxstrike-*` containers with their current state and exposed ports,
using `docker ps` under the hood.

---

## Stopping Labs

```bash
./scripts/lab.sh stop 1        # stop a specific lab
./scripts/lab.sh stop all      # stop and remove all lab containers
```

Each `stop` action removes the container entirely (`docker rm -f`). No data is persisted
between runs — each `start` is a clean slate.

---

## Adding a New Lab

1. Create `scripts/labs/mylab.sh` — source `_common.sh` at the top and implement
   `start`, `stop`, and `status` cases.
2. Register it in the `LABS` array in `scripts/lab.sh`:

```bash
LABS=(
  ...
  "8|My Lab|mylab.sh|Short description of what it covers"
)
```

3. Make the script executable:

```bash
chmod +x scripts/labs/mylab.sh
```

Each lab script follows the same pattern:

```bash
#!/usr/bin/env bash
LAB_NAME="My Lab"
CONTAINER_NAME="nyxstrike-mylab"
HOST_PORT=9000

source "$(dirname "$0")/_common.sh"
require_action "${1:-}"

case "$1" in
  start)
    ensure_container_gone "$CONTAINER_NAME"
    docker pull myimage:latest
    docker run -d --name "$CONTAINER_NAME" -p "${HOST_PORT}:80" myimage:latest
    wait_for_port 127.0.0.1 "$HOST_PORT" 60
    INFO_LINES=("URL|http://127.0.0.1:${HOST_PORT}" "Stop|./mylab.sh stop")
    access_card INFO_LINES
    good "My Lab is up!"
    ;;
  stop)
    docker rm -f "$CONTAINER_NAME" &>/dev/null && good "Stopped." || warn "Not running."
    ;;
  status)
    container_status "$CONTAINER_NAME"
    ;;
esac
```

---

## Shared Helper Reference (`_common.sh`)

All lab scripts source `_common.sh` which provides:

| Function | Description |
|----------|-------------|
| `good <msg>` | Print `[+] msg` in green |
| `bad <msg>` | Print `[-] msg` in red |
| `info <msg>` | Print `[*] msg` in gray |
| `warn <msg>` | Print `[!] msg` in yellow |
| `header <msg>` | Print a bold green section header prefixed with the lab name |
| `access_card <array>` | Print a formatted access-info box after lab start |
| `wait_for_port <host> <port> [timeout]` | Poll until a port is open (default 60s timeout) |
| `ensure_container_gone <name>` | Remove a container if it exists (running or stopped) |
| `container_status <name>` | Report current state of a named container |
| `require_action <arg>` | Exit with usage message if arg is not `start`/`stop`/`status` |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Docker daemon is not running` | Run `sudo systemctl start docker` (Linux) or start Docker Desktop |
| Port already in use | Another process is using the default port — edit `HOST_PORT` at the top of the lab script |
| Image pull fails | Check internet connectivity; some images (Kioptrix) have community-maintained sources that may go offline |
| VulnAD LDAP bind fails | Samba4 provisioning can take 15–30s — wait and retry; check `docker logs nyxstrike-vulnad` |
| `nc: command not found` | Install netcat: `apt install netcat-openbsd` / `brew install netcat` |

---

## Related

- [`install_tools.sh`](installation_and_flags.md) — installs the 185+ security tools NyxStrike orchestrates
- [`skills/`](../skills/) — AI agent workflow guides that can be used against these lab targets
- [VulnAD (original)](https://github.com/WazeHell/vulnerable-AD) — the PowerShell project this AD lab is based on
