#!/usr/bin/env bash
# =============================================================================
# NyxStrike Wordlist Manager
# List, search, download, and register wordlists used by NyxStrike tools
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${NYXSTRIKE_DATA_DIR:-${REPO_ROOT}/.nyxstrike_data}"
LOCAL_WL_DIR="${DATA_DIR}/wordlists"
REGISTRY_FILE="${LOCAL_WL_DIR}/wordlists.json"

# ---------------- colours / output helpers -----------------------------------
RED='\033[0;31m'
GREEN='\033[38;5;46m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
BOLD='\033[1m'
RESET='\033[0m'

good()   { echo -e "\t${GREEN}[+]${RESET} $*"; }
bad()    { echo -e "\t${RED}[-]${RESET} $*"; }
info()   { echo -e "\t${GRAY}[*]${RESET} $*"; }
warn()   { echo -e "\t${YELLOW}[!]${RESET} $*"; }
header() { echo -e "\n${GREEN}${BOLD}$*${RESET}"; }

# ---------------- banner -----------------------------------------------------
banner() {
  echo ""
  echo -e "${GREEN}${BOLD}"
  echo "  ███╗   ██╗██╗   ██╗██╗  ██╗███████╗████████╗██████╗ ██╗██╗  ██╗███████╗"
  echo "  ████╗  ██║╚██╗ ██╔╝╚██╗██╔╝██╔════╝╚══██╔══╝██╔══██╗██║██║ ██╔╝██╔════╝"
  echo "  ██╔██╗ ██║ ╚████╔╝  ╚███╔╝ ███████╗   ██║   ██████╔╝██║█████╔╝ █████╗  "
  echo "  ██║╚██╗██║  ╚██╔╝   ██╔██╗ ╚════██║   ██║   ██╔══██╗██║██╔═██╗ ██╔══╝  "
  echo "  ██║ ╚████║   ██║   ██╔╝ ██╗███████║   ██║   ██║  ██║██║██║  ██╗███████╗"
  echo "  ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝"
  echo -e "${RESET}"
  echo -e "  ${BOLD}Wordlist Manager${RESET} — List, search, download, and register wordlists"
  echo ""
}

# ---------------- built-in wordlist catalogue --------------------------------
# Format per entry: "name|system_path|local_subpath|description"
# system_path   — checked first; if it exists, wins
# local_subpath — path under LOCAL_WL_DIR used as fallback
declare -a BUILTIN_WORDLISTS=(
  "rockyou|/usr/share/wordlists/rockyou.txt|rockyou.txt|Classic password list — 14M entries"
  "john|/usr/share/wordlists/john.lst|john.lst|John the Ripper default wordlist"
  "dirb-common|/usr/share/wordlists/dirb/common.txt|dirb/common.txt|Common web directories (DIRB)"
  "dirb-big|/usr/share/wordlists/dirb/big.txt|dirb/big.txt|Large web directory list (DIRB)"
  "dirb-small|/usr/share/wordlists/dirb/small.txt|dirb/small.txt|Small web directory list (DIRB)"
  "dirsearch-common|/usr/share/wordlists/dirsearch/common.txt|dirsearch/common.txt|Common paths for dirsearch"
  "seclists-web-common|/usr/share/seclists/Discovery/Web-Content/common.txt|seclists/Discovery/Web-Content/common.txt|SecLists — common web content"
  "seclists-web-big|/usr/share/seclists/Discovery/Web-Content/big.txt|seclists/Discovery/Web-Content/big.txt|SecLists — big web content"
  "seclists-web-raft-small|/usr/share/seclists/Discovery/Web-Content/raft-small-words.txt|seclists/Discovery/Web-Content/raft-small-words.txt|SecLists — RAFT small words"
  "seclists-dns|/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt|seclists/Discovery/DNS/subdomains-top1million-5000.txt|SecLists — top 5000 subdomains"
  "seclists-dns-big|/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt|seclists/Discovery/DNS/subdomains-top1million-110000.txt|SecLists — top 110k subdomains"
  "seclists-usernames|/usr/share/seclists/Usernames/top-usernames-shortlist.txt|seclists/Usernames/top-usernames-shortlist.txt|SecLists — common usernames"
  "seclists-passwords|/usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt|seclists/Passwords/Common-Credentials/10k-most-common.txt|SecLists — 10k most common passwords"
  "seclists-passwords-rockyou2021|/usr/share/seclists/Passwords/Leaked-Databases/rockyou2021.txt|seclists/Passwords/Leaked-Databases/rockyou2021.txt|SecLists — rockyou 2021 leak"
)

# ---------------- registry helpers -------------------------------------------
ensure_registry() {
  mkdir -p "$LOCAL_WL_DIR"
  if [[ ! -f "$REGISTRY_FILE" ]]; then
    echo '{"WORD_LISTS":{}}' > "$REGISTRY_FILE"
  fi
  # ensure WORD_LISTS key exists
  if ! grep -q '"WORD_LISTS"' "$REGISTRY_FILE" 2>/dev/null; then
    echo '{"WORD_LISTS":{}}' > "$REGISTRY_FILE"
  fi
}

# Read custom entries from registry — outputs "name|path|description" lines
registry_entries() {
  ensure_registry
  if command -v python3 &>/dev/null; then
    python3 - "$REGISTRY_FILE" <<'PYEOF' 2>/dev/null || true
import json, sys
data = json.load(open(sys.argv[1]))
for name, info in data.get("WORD_LISTS", {}).items():
    path = info.get("path", "")
    desc = info.get("description", "")
    print(f"{name}|{path}|{desc}")
PYEOF
  fi
}

# Write a new entry into the registry
registry_add() {
  local name="$1"
  local path="$2"
  local desc="$3"
  ensure_registry
  if command -v python3 &>/dev/null; then
    python3 - "$REGISTRY_FILE" "$name" "$path" "$desc" <<'PYEOF'
import json, sys
reg_file, name, path, desc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = json.load(open(reg_file))
data.setdefault("WORD_LISTS", {})[name] = {"path": path, "description": desc}
with open(reg_file, "w") as f:
    json.dump(data, f, indent=2)
print(f"Registered: {name}")
PYEOF
  elif command -v jq &>/dev/null; then
    local tmp
    tmp=$(mktemp)
    jq --arg n "$name" --arg p "$path" --arg d "$desc" \
      '.WORD_LISTS[$n] = {"path": $p, "description": $d}' \
      "$REGISTRY_FILE" > "$tmp" && mv "$tmp" "$REGISTRY_FILE"
    good "Registered: ${name}"
  else
    bad "python3 or jq is required to add wordlist entries."
    exit 1
  fi
}

# ---------------- path resolution --------------------------------------------
# Resolve a wordlist name to its actual on-disk path.
# Checks system path first, then local fallback.
# Returns "" if not found anywhere.
resolve_path() {
  local name="$1"

  # 1. Check built-ins
  for entry in "${BUILTIN_WORDLISTS[@]}"; do
    IFS='|' read -r bname sys_path local_sub _desc <<< "$entry"
    if [[ "$bname" == "$name" ]]; then
      if [[ -f "$sys_path" ]]; then
        echo "$sys_path"; return
      fi
      local local_path="${LOCAL_WL_DIR}/${local_sub}"
      if [[ -f "$local_path" ]]; then
        echo "$local_path"; return
      fi
      echo ""; return
    fi
  done

  # 2. Check custom registry
  while IFS='|' read -r rname rpath _rdesc; do
    if [[ "$rname" == "$name" ]]; then
      if [[ -f "$rpath" ]]; then
        echo "$rpath"; return
      fi
      echo ""; return
    fi
  done < <(registry_entries)

  echo ""
}

# ---------------- human-readable file size -----------------------------------
human_size() {
  local path="$1"
  if [[ ! -f "$path" ]]; then echo "—"; return; fi
  local bytes
  bytes=$(wc -c < "$path" 2>/dev/null || echo 0)
  if   [[ $bytes -ge 1073741824 ]]; then
    python3 -c "print(f'{$bytes/1073741824:.1f}G')" 2>/dev/null || echo "$((bytes/1073741824))G"
  elif [[ $bytes -ge 1048576 ]];    then
    python3 -c "print(f'{$bytes/1048576:.1f}M')" 2>/dev/null || echo "$((bytes/1048576))M"
  elif [[ $bytes -ge 1024 ]];       then
    python3 -c "print(f'{$bytes/1024:.1f}K')" 2>/dev/null || echo "$((bytes/1024))K"
  else echo "${bytes}B"
  fi
}

# ---------------- list -------------------------------------------------------
cmd_list() {
  local filter="${1:-}"

  header "Wordlist Registry"
  echo ""
  printf "  ${BOLD}%-35s %-8s %-8s %s${RESET}\n" "NAME" "EXISTS" "SIZE" "PATH / DESCRIPTION"
  echo "  ─────────────────────────────────────────────────────────────────────────────────"

  # Built-ins
  for entry in "${BUILTIN_WORDLISTS[@]}"; do
    IFS='|' read -r name sys_path local_sub desc <<< "$entry"
    [[ -n "$filter" ]] && [[ "$name$desc" != *"$filter"* ]] && continue

    local resolved="" source_label=""
    if [[ -f "$sys_path" ]]; then
      resolved="$sys_path"
      source_label="[sys]"
    else
      local local_path="${LOCAL_WL_DIR}/${local_sub}"
      if [[ -f "$local_path" ]]; then
        resolved="$local_path"
        source_label="[local]"
      fi
    fi

    local exists_flag size display_path
    if [[ -n "$resolved" ]]; then
      exists_flag="${GREEN}yes${RESET}"
      size=$(human_size "$resolved")
      display_path="${resolved} ${GRAY}${source_label}${RESET}"
    else
      exists_flag="${RED}no${RESET} "
      size="—"
      display_path="${GRAY}${desc}${RESET}"
    fi

    printf "  ${BOLD}%-35s${RESET} " "$name"
    echo -ne "${exists_flag}     "
    printf "%-8s" "$size"
    echo -e "${display_path}"
  done

  # Custom registry entries
  local custom_count=0
  while IFS='|' read -r rname rpath rdesc; do
    [[ -z "$rname" ]] && continue
    # skip if already in built-ins
    local is_builtin=0
    for entry in "${BUILTIN_WORDLISTS[@]}"; do
      IFS='|' read -r bname _ _ _ <<< "$entry"
      [[ "$bname" == "$rname" ]] && { is_builtin=1; break; }
    done
    [[ $is_builtin -eq 1 ]] && continue
    [[ -n "$filter" ]] && [[ "$rname$rdesc" != *"$filter"* ]] && continue

    custom_count=$((custom_count + 1))
    local exists_flag size display_path
    if [[ -f "$rpath" ]]; then
      exists_flag="${GREEN}yes${RESET}"
      size=$(human_size "$rpath")
      display_path="${rpath} ${GRAY}[custom]${RESET}"
    else
      exists_flag="${RED}no${RESET} "
      size="—"
      display_path="${GRAY}${rdesc}${RESET}"
    fi

    printf "  ${BOLD}%-35s${RESET} " "$rname"
    echo -ne "${exists_flag}     "
    printf "%-8s" "$size"
    echo -e "${display_path}"
  done < <(registry_entries)

  echo ""
  info "Registry: ${REGISTRY_FILE}"
  echo ""
}

# ---------------- status (missing only) --------------------------------------
cmd_status() {
  header "Missing Wordlists"
  echo ""
  local missing=0

  for entry in "${BUILTIN_WORDLISTS[@]}"; do
    IFS='|' read -r name sys_path local_sub desc <<< "$entry"
    if [[ ! -f "$sys_path" && ! -f "${LOCAL_WL_DIR}/${local_sub}" ]]; then
      printf "  ${RED}%-35s${RESET} %s\n" "$name" "$desc"
      missing=$((missing + 1))
    fi
  done

  while IFS='|' read -r rname rpath rdesc; do
    [[ -z "$rname" ]] && continue
    if [[ ! -f "$rpath" ]]; then
      printf "  ${RED}%-35s${RESET} %s\n" "$rname" "$rpath"
      missing=$((missing + 1))
    fi
  done < <(registry_entries)

  if [[ $missing -eq 0 ]]; then
    good "All registered wordlists are present on disk."
  else
    echo ""
    warn "${missing} wordlist(s) missing."
    echo ""
    echo -e "  Run ${GREEN}./wordlist.sh get rockyou${RESET}  to decompress rockyou"
    echo -e "  Run ${GREEN}./wordlist.sh get seclists${RESET} to clone SecLists"
  fi
  echo ""
}

# ---------------- search -----------------------------------------------------
cmd_search() {
  local keyword="${1:-}"
  if [[ -z "$keyword" ]]; then
    bad "Usage: wordlist.sh search <keyword>"
    exit 1
  fi
  header "Search results for: ${keyword}"
  echo ""
  cmd_list "$keyword"
}

# ---------------- path (scriptable) ------------------------------------------
cmd_path() {
  local name="${1:-}"
  if [[ -z "$name" ]]; then
    bad "Usage: wordlist.sh path <name>"
    exit 1
  fi
  local resolved
  resolved=$(resolve_path "$name")
  if [[ -z "$resolved" ]]; then
    bad "Wordlist '${name}' not found on disk."
    exit 1
  fi
  echo "$resolved"
}

# ---------------- get rockyou ------------------------------------------------
cmd_get_rockyou() {
  header "rockyou.txt"

  local sys_path="/usr/share/wordlists/rockyou.txt"
  local gz_path="/usr/share/wordlists/rockyou.txt.gz"
  local local_path="${LOCAL_WL_DIR}/rockyou.txt"

  # Already present on system
  if [[ -f "$sys_path" ]]; then
    good "Already present at system path: ${sys_path}"
    return
  fi

  # Already present locally
  if [[ -f "$local_path" ]]; then
    good "Already present at local path: ${local_path}"
    return
  fi

  # Decompress system gz
  if [[ -f "$gz_path" ]]; then
    info "Decompressing ${gz_path} → ${sys_path}"
    if gunzip -k "$gz_path" 2>/dev/null; then
      good "Decompressed to: ${sys_path}"
      return
    else
      warn "Permission denied on system path — decompressing to local fallback"
      mkdir -p "$LOCAL_WL_DIR"
      gunzip -c "$gz_path" > "$local_path"
      good "Decompressed to local: ${local_path}"
      return
    fi
  fi

  # Download to local
  warn "rockyou.txt.gz not found at system path. Downloading to local wordlists dir..."
  mkdir -p "$LOCAL_WL_DIR"
  local url="https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt"
  if command -v wget &>/dev/null; then
    wget -q --show-progress -O "$local_path" "$url"
  elif command -v curl &>/dev/null; then
    curl -L --progress-bar -o "$local_path" "$url"
  else
    bad "wget or curl is required to download rockyou.txt"
    exit 1
  fi
  good "Downloaded to: ${local_path}"
}

# ---------------- get seclists -----------------------------------------------
cmd_get_seclists() {
  header "SecLists"

  local sys_path="/usr/share/seclists"
  local local_path="${LOCAL_WL_DIR}/seclists"

  # Already present on system — no double files
  if [[ -d "$sys_path" ]]; then
    good "SecLists already present at system path: ${sys_path}"
    info "To update: sudo git -C ${sys_path} pull"
    return
  fi

  # Already present locally — update instead
  if [[ -d "${local_path}/.git" ]]; then
    info "SecLists already cloned locally — pulling latest changes..."
    git -C "$local_path" pull --ff-only
    good "SecLists updated at: ${local_path}"
    return
  fi

  # Try system path first (if writable)
  if [[ -w "$(dirname "$sys_path")" ]]; then
    info "Cloning SecLists to system path: ${sys_path}"
    git clone --depth 1 "https://github.com/danielmiessler/SecLists.git" "$sys_path"
    good "SecLists cloned to: ${sys_path}"
    return
  fi

  # Fall back to local
  warn "System path ${sys_path} not writable — cloning to local fallback"
  mkdir -p "$(dirname "$local_path")"
  info "Cloning SecLists to: ${local_path} (this may take a few minutes)"
  git clone --depth 1 "https://github.com/danielmiessler/SecLists.git" "$local_path"
  good "SecLists cloned to: ${local_path}"
}

# ---------------- add (custom registration) ----------------------------------
cmd_add() {
  local name="${1:-}"
  local path="${2:-}"
  local desc="${3:-Custom wordlist}"

  if [[ -z "$name" || -z "$path" ]]; then
    bad "Usage: wordlist.sh add <name> <path> [description]"
    echo "  Example: ./wordlist.sh add my-list /opt/lists/custom.txt 'My custom wordlist'"
    exit 1
  fi

  # Resolve to absolute path
  path="$(realpath "$path" 2>/dev/null || echo "$path")"

  if [[ ! -f "$path" ]]; then
    warn "File does not exist at path: ${path}"
    warn "Registering anyway — it can be populated later."
  fi

  # Check for name collision with built-ins
  for entry in "${BUILTIN_WORDLISTS[@]}"; do
    IFS='|' read -r bname _ _ _ <<< "$entry"
    if [[ "$bname" == "$name" ]]; then
      bad "Name '${name}' is reserved for a built-in wordlist. Choose a different name."
      exit 1
    fi
  done

  registry_add "$name" "$path" "$desc"
  good "Registered: ${name} → ${path}"
}

# ---------------- main -------------------------------------------------------
banner

cmd="${1:-list}"
shift || true

case "$cmd" in
  list)        cmd_list ;;
  status)      cmd_status ;;
  search)      cmd_search "${1:-}" ;;
  path)        cmd_path "${1:-}" ;;
  get)
    target="${1:-}"
    case "$target" in
      rockyou)   cmd_get_rockyou ;;
      seclists)  cmd_get_seclists ;;
      "")
        bad "Usage: wordlist.sh get <rockyou|seclists>"
        exit 1 ;;
      *)
        bad "Unknown target: ${target}. Supported: rockyou, seclists"
        exit 1 ;;
    esac ;;
  add)         cmd_add "${1:-}" "${2:-}" "${3:-}" ;;
  help|-h|--help)
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "  list                         List all wordlists with status and path"
    echo "  status                       Show only missing wordlists"
    echo "  search <keyword>             Filter wordlists by name or description"
    echo "  path <name>                  Print resolved path for a wordlist (scriptable)"
    echo "  get rockyou                  Decompress or download rockyou.txt"
    echo "  get seclists                 Clone or update SecLists"
    echo "  add <name> <path> [desc]     Register a custom wordlist"
    echo "  help                         Show this help"
    echo ""
    echo "  Local wordlist dir:  ${LOCAL_WL_DIR}"
    echo "  Registry file:       ${REGISTRY_FILE}"
    echo "" ;;
  *)
    bad "Unknown command: ${cmd}"
    echo "Run '$0 help' for usage."
    exit 1 ;;
esac
