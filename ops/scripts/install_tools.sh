#!/usr/bin/env bash
# =============================================================================
#  nyxstrike — Security Tools Installer
#  Version: 1.0.0
#  Compatibility: Linux (Debian/Ubuntu, Arch, Fedora/RHEL) | macOS (Homebrew)
#
#  Author : Anmol Singh Yadav [@IamLucif3r]
#  GitHub : https://github.com/IamLucif3r
# =============================================================================
#
#  USAGE:
#    ./ops/scripts/install_tools.sh [OPTIONS]
#
#  OPTIONS:
#    --only <category>   Install only a specific category
#                        Categories: network, web, auth, binary, cloud, ctf, osint, browser
#    --dry-run           Preview what would be installed, without making changes
#    --show-log          Display full install log at the end
#    --list              List all categories and their tools, then exit
#    --help, -h          Show this help message and exit
#
#  EXAMPLES:
#    ./ops/scripts/install_tools.sh                   # Install everything
#    ./ops/scripts/install_tools.sh --only network    # Install only network tools
#    ./ops/scripts/install_tools.sh --dry-run         # Preview all installs
#    ./ops/scripts/install_tools.sh --only web --dry-run
#
#  NOTES:
#    - Python deps (pyproject.toml) are handled separately: uv sync --extra tools --extra big
#    - GUI tools (Ghidra, Maltego, Binary Ninja, IDA) are skipped with guidance
#    - All pip installs use --user flag (no root required)
#    - Go packages install to ~/go/bin (add to PATH if not already set)
#    - Cargo packages install to ~/.cargo/bin (add to PATH if not already set)
#    - Gem installs use --user-install flag (no root required)
#    - apt/dnf/pacman installs still require sudo (no user-level equivalent)
# =============================================================================

set -uo pipefail

# ─── Colours ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[38;5;46m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ─── Globals ─────────────────────────────────────────────────────────────────
DRY_RUN=false
SHOW_LOG=false
ONLY_CATEGORY=""
FAIL_HINT=""
LOG_FILE="$(pwd)/install_log.txt"

COUNT_INSTALLED=0
COUNT_SKIPPED=0
COUNT_ALREADY=0
COUNT_FAILED=0
COUNT_MANUAL=0

declare -a FAILED_TOOLS=()
declare -a MANUAL_TOOLS=()
# Keep reasons indexed like FAILED_TOOLS for macOS's bundled Bash 3.2.
declare -a FAILED_REASONS=()

# ─── Detected OS/Package-Manager ─────────────────────────────────────────────
OS=""          # linux | macos
PKG_MGR=""     # apt | dnf | pacman | brew | unknown
DISTRO=""      # ubuntu | debian | arch | fedora | rhel | unknown
BREW_PREFIX=""

# ─── Sudo Wrapper ─────────────────────────────────────────────────────────────
# Empty when already running as root (e.g. Docker containers). Using an empty
# variable avoids 'sudo: command not found' errors in minimal environments.
SUDO="sudo"
[[ "$(id -u)" == "0" ]] && SUDO=""

# ─── Logging ─────────────────────────────────────────────────────────────────
log() {
  local timestamp
  # Guard against I/O errors (e.g. disk full in Docker) — never crash on logging
  timestamp="$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo '----')"
  echo "[$timestamp] $*" >> "$LOG_FILE" 2>/dev/null || true
}

info()    { echo -e "${CYAN}[i]${RESET} $*";                    log "[INFO]    $*"; }
success() { echo -e "${GREEN}[✔]${RESET} $*";                   log "[SUCCESS] $*"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $*";                  log "[WARN]    $*"; }
error()   { echo -e "${RED}[✘]${RESET} $*" >&2;                log "[ERROR]   $*"; }
skip()    { echo -e "${DIM}[~]${RESET} ${DIM}$*${RESET}";      log "[SKIP]    $*"; }
manual()  { echo -e "${MAGENTA}[⊕]${RESET} $*";                log "[MANUAL]  $*"; }
dry()     { echo -e "${BLUE}[•]${RESET} ${BLUE}[DRY-RUN]${RESET} would install: ${BOLD}$*${RESET}"; log "[DRY-RUN] $*"; }
section() { echo ""; echo -e "${BOLD}${YELLOW}━━━ $* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"; }

# ─── Help ─────────────────────────────────────────────────────────────────────
print_help() {
  echo -e "${BOLD}USAGE${RESET}"
  echo "  ./ops/scripts/install_tools.sh [OPTIONS]"
  echo ""
  echo -e "${BOLD}OPTIONS${RESET}"
  echo "  --only <category>   Install only a specific category of tools"
  echo "  --dry-run           Preview what would be installed without making changes"
  echo "  --show-log          Display full install log at the end"
  echo "  --list              List all categories and tools, then exit"
  echo "  --help, -h          Show this help message"
  echo ""
  echo -e "${BOLD}CATEGORIES${RESET}"
  echo "  network   Network reconnaissance & scanning tools (25+)"
  echo "  web       Web application security testing tools (40+)"
  echo "  auth      Authentication & password cracking tools (12+)"
  echo "  binary    Binary analysis & reverse engineering tools (25+)"
  echo "  cloud     Cloud & container security tools (20+)"
  echo "  ctf       CTF & digital forensics tools (20+)"
  echo "  osint     OSINT & intelligence gathering tools (20+)"
  echo "  browser   Browser agent dependencies (Chromium + ChromeDriver)"
  echo ""
  echo -e "${BOLD}EXAMPLES${RESET}"
  echo "  ./ops/scripts/install_tools.sh                    Install all tools"
  echo "  ./ops/scripts/install_tools.sh --only web         Install only web tools"
  echo "  ./ops/scripts/install_tools.sh --dry-run          Preview all installs"
  echo "  ./ops/scripts/install_tools.sh --only cloud --dry-run"
  echo ""
  echo -e "${BOLD}NOTES${RESET}"
  echo "  • Python deps: handle separately with  uv sync --extra tools --extra big"
  echo "  • Logs are written to: $LOG_FILE"
  echo "  • Go tools are installed to ~/go/bin — ensure it is in your PATH"
  echo "  • Rust/Cargo tools are installed to ~/.cargo/bin — ensure it is in your PATH"
  echo "  • Gem tools use --user-install — ensure ~/.gem/ruby/*/bin is in your PATH"
  echo "  • pip tools use --user — ~/.local/bin should be in your PATH"
}

# ─── Tool List ────────────────────────────────────────────────────────────────
print_list() {
  echo -e "${BOLD}nyxstrike — Managed Tool Inventory${RESET}"
  echo ""
  echo -e "${CYAN}🔍 NETWORK / RECON (25+)${RESET}"
  echo "   nmap, masscan, rustscan, autorecon, amass, subfinder, sublist3r, nuclei,"
  echo "   fierce, dnsenum, theharvester, responder, netexec, enum4linux,"
  echo "   enum4linux-ng, arp-scan, nbtscan, smbmap"
  echo ""
  echo -e "${CYAN}🌐 WEB APPLICATION SECURITY (40+)${RESET}"
  echo "   gobuster, ffuf, feroxbuster, dirsearch, dirb, httpx, katana,"
  echo "   hakrawler, gau, waybackurls, nikto, sqlmap, wpscan, arjun,"
  echo "   paramspider, dalfox, wafw00f, whatweb, wfuzz, commix"
  echo ""
  echo -e "${CYAN}🔐 AUTH / PASSWORD (12+)${RESET}"
  echo "   hydra, john, hashcat, medusa, patator, evil-winrm, hash-identifier"
  echo ""
  echo -e "${CYAN}🔬 BINARY / REVERSE ENGINEERING (25+)${RESET}"
  echo "   gdb, radare2, binwalk, ropgadget, checksec, exiftool, volatility3,"
  echo "   strings/objdump/readelf (binutils)"
  echo ""
  echo -e "${MAGENTA}   ⊕ MANUAL INSTALL REQUIRED: ghidra, ida-free, binary-ninja${RESET}"
  echo ""
  echo -e "${CYAN}☁️  CLOUD / CONTAINER (20+)${RESET}"
  echo "   trivy, kube-hunter, kube-bench, checkov, aws-cli,"
  echo "   kubectl, helm, docker-bench-security"
  echo ""
  echo -e "${CYAN}🏆 CTF / FORENSICS (20+)${RESET}"
  echo "   volatility3, foremost, steghide, exiftool, binwalk, scalpel,"
  echo "   testdisk, photorec, zsteg, stegsolve, outguess, bulk-extractor"
  echo ""
  echo -e "${CYAN}🕵️  OSINT / INTELLIGENCE (20+)${RESET}"
  echo "   sherlock, recon-ng, spiderfoot, theharvester"
  echo ""
  echo -e "${MAGENTA}   ⊕ MANUAL INSTALL REQUIRED: maltego, shodan-cli (API key needed)${RESET}"
  echo ""
  echo -e "${CYAN}🌍 BROWSER AGENT${RESET}"
  echo "   chromium, chromedriver"
}

# ─── OS Detection ─────────────────────────────────────────────────────────────
detect_os() {
  section "Detecting Operating System"

  if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    PKG_MGR="brew"
    DISTRO="macos"
    info "Detected: ${BOLD}macOS${RESET}"
    case "$(uname -m)" in
      arm64) BREW_PREFIX="/opt/homebrew" ;;
      x86_64) BREW_PREFIX="/usr/local" ;;
      *) error "Unsupported macOS architecture: $(uname -m)"; exit 1 ;;
    esac
    if [[ -x "$BREW_PREFIX/bin/brew" ]]; then
      export PATH="$BREW_PREFIX/bin:$BREW_PREFIX/sbin:$PATH"
    fi
    if ! command -v brew &>/dev/null; then
      if [[ "$DRY_RUN" == true ]]; then
        warn "Homebrew is missing; showing the installation plan only."
        return
      fi
      error "Homebrew is not installed. Install it first: https://brew.sh"
      error "Run: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
      exit 1
    fi
    BREW_PREFIX="$(brew --prefix)"
    export PATH="$BREW_PREFIX/opt/binutils/bin:$PATH"
    [[ -n "${VIRTUAL_ENV:-}" ]] && export PATH="$VIRTUAL_ENV/bin:$PATH"
    info "Homebrew found: $(brew --version | head -1)"

  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if [[ -f /etc/os-release ]]; then
      # shellcheck source=/dev/null
      source /etc/os-release
      DISTRO="${ID:-unknown}"
    fi

    case "$DISTRO" in
      ubuntu|debian|kali|parrot|pop|mint|linuxmint)
        PKG_MGR="apt"
        # Suppress ALL interactive prompts from apt/dpkg (crucial for Docker/CI)
        export DEBIAN_FRONTEND=noninteractive
        export DEBCONF_NONINTERACTIVE_SEEN=true
        info "Detected: ${BOLD}${DISTRO} Linux${RESET} (apt)"
        ;;
      arch|manjaro|endeavouros|garuda)
        PKG_MGR="pacman"
        info "Detected: ${BOLD}${DISTRO} Linux${RESET} (pacman)"
        ;;
      fedora|rhel|centos|rocky|alma)
        PKG_MGR="dnf"
        info "Detected: ${BOLD}${DISTRO} Linux${RESET} (dnf)"
        ;;
      *)
        PKG_MGR="unknown"
        warn "Unknown Linux distro: ${DISTRO}. System package installs will be skipped."
        warn "Go, pip, cargo, and gem installs will still proceed."
        ;;
    esac
  else
    error "Unsupported OS: $OSTYPE"
    exit 1
  fi

  log "OS=$OS DISTRO=$DISTRO PKG_MGR=$PKG_MGR"
}

# ─── PATH Guidance ────────────────────────────────────────────────────────────
check_paths() {
  section "Checking User PATH"
  local missing_paths=()

  local managed_bin="$HOME/.local/share/nyxstrike-tools/bin"
  if [[ -d "$managed_bin" && ":$PATH:" != *":$managed_bin:"* ]]; then
    missing_paths+=("$managed_bin  (isolated NyxStrike tools)")
  fi

  # Go
  if command -v go &>/dev/null; then
    local gopath
    gopath="$(go env GOPATH 2>/dev/null || echo "$HOME/go")"
    if [[ ":$PATH:" != *":${gopath}/bin:"* ]]; then
      missing_paths+=("${gopath}/bin  (Go binaries)")
    fi
  fi

  # Cargo / Rust
  if [[ -d "$HOME/.cargo/bin" && ":$PATH:" != *":$HOME/.cargo/bin:"* ]]; then
    missing_paths+=("$HOME/.cargo/bin  (Rust/Cargo binaries)")
  fi

  # pip --user
  local pip_bin
  pip_bin="$(python3 -m site --user-base 2>/dev/null)/bin"
  if [[ -d "$pip_bin" && ":$PATH:" != *":${pip_bin}:"* ]]; then
    missing_paths+=("${pip_bin}  (pip --user binaries)")
  fi

  # Gem user install
  if command -v ruby &>/dev/null; then
    local gem_bin
    gem_bin="$(ruby -e 'puts Gem.user_dir' 2>/dev/null)/bin"
    if [[ -d "$gem_bin" && ":$PATH:" != *":${gem_bin}:"* ]]; then
      missing_paths+=("${gem_bin}  (gem --user-install binaries)")
    fi
  fi

  if [[ ${#missing_paths[@]} -gt 0 ]]; then
    warn "The following directories are NOT in your PATH. Add them to ~/.bashrc or ~/.zshrc:"
    for p in "${missing_paths[@]}"; do
      warn "  export PATH=\"\$PATH:${p%%  *}\""
    done
    echo ""
  else
    success "All known user bin directories are in PATH"
  fi
}

# ─── Prereq Installers ────────────────────────────────────────────────────────

# Install python3 + pip3
_install_python() {
  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}python3 & pip3${RESET} ... "
  local ok=false
  case "$PKG_MGR" in
    apt)
      $SUDO apt-get install -y \
        -o Dpkg::Options::="--force-confdef" \
        -o Dpkg::Options::="--force-confold" \
        python3 python3-pip python3-dev &>/dev/null && ok=true ;;
    dnf)
      $SUDO dnf install -y python3 python3-pip &>/dev/null && ok=true ;;
    pacman)
      $SUDO pacman -S --noconfirm python python-pip &>/dev/null && ok=true ;;
    brew)
      brew install python3 &>/dev/null && ok=true ;;
  esac
  if $ok && command -v python3 &>/dev/null; then
    echo -e "${GREEN}done${RESET}"
    log "[SUCCESS] python3 & pip3 installed"
  else
    echo -e "${RED}failed${RESET}"
    error "Could not install python3 — please install it manually."
    exit 1
  fi
}

# Install git
_install_git() {
  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}git${RESET} ... "
  local ok=false
  case "$PKG_MGR" in
    apt)    $SUDO apt-get install -y \
              -o Dpkg::Options::="--force-confdef" \
              -o Dpkg::Options::="--force-confold" \
              git &>/dev/null && ok=true ;;
    dnf)    $SUDO dnf install -y git &>/dev/null && ok=true ;;
    pacman) $SUDO pacman -S --noconfirm git &>/dev/null && ok=true ;;
    brew)   brew install git &>/dev/null && ok=true ;;
  esac
  if $ok && command -v git &>/dev/null; then
    echo -e "${GREEN}done${RESET}"
    log "[SUCCESS] git installed"
  else
    echo -e "${RED}failed${RESET}"
    error "Could not install git — please install it manually."
    exit 1
  fi
}

# Install Go — prefer package manager; fall back to official binary on Linux
_install_go() {
  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}Go${RESET} ... "

  if [[ "$OS" == "macos" ]]; then
    brew install go &>/dev/null
    if command -v go &>/dev/null; then
      echo -e "${GREEN}done (brew)${RESET}"
      log "[SUCCESS] go installed via brew"
      return
    fi
  else
    # Try package manager first
    local pkg_ok=false
    case "$PKG_MGR" in
      apt)    $SUDO apt-get install -y \
                -o Dpkg::Options::="--force-confdef" \
                -o Dpkg::Options::="--force-confold" \
                golang-go &>/dev/null && pkg_ok=true ;;
      dnf)    $SUDO dnf install -y golang &>/dev/null && pkg_ok=true ;;
      pacman) $SUDO pacman -S --noconfirm go &>/dev/null && pkg_ok=true ;;
    esac

    if $pkg_ok && command -v go &>/dev/null; then
      echo -e "${GREEN}done (pkg)${RESET}"
      log "[SUCCESS] go installed via package manager"
      return
    fi

    # Fall back: download official binary to ~/.local/go
    echo -e "${YELLOW}pkg failed — downloading official binary...${RESET}"
    echo -ne "  ${CYAN}↳${RESET} Fetching latest Go release ... "
    local go_ver
    go_ver=$(curl -sL "https://go.dev/VERSION?m=text" | head -1)
    local arch
    arch=$(uname -m); [[ "$arch" == "x86_64" ]] && arch="amd64" || arch="arm64"
    local go_url="https://go.dev/dl/${go_ver}.linux-${arch}.tar.gz"

    mkdir -p "$HOME/.local"
    if curl -sL "$go_url" | tar -C "$HOME/.local" -xz 2>/dev/null; then
      # Symlink binaries into ~/.local/bin
      mkdir -p "$HOME/.local/bin"
      ln -sf "$HOME/.local/go/bin/go"   "$HOME/.local/bin/go"
      ln -sf "$HOME/.local/go/bin/gofmt" "$HOME/.local/bin/gofmt"
      # Make available in current shell immediately
      export PATH="$HOME/.local/bin:$PATH"
      if command -v go &>/dev/null; then
        echo -e "${GREEN}done (${go_ver} → ~/.local/go)${RESET}"
        log "[SUCCESS] go ${go_ver} installed to ~/.local/go"
        return
      fi
    fi
  fi

  echo -e "${RED}failed${RESET}"
  warn "Could not install Go — Go-based tools will be skipped."
  log "[WARN] go install failed"
}

# Install Rust + Cargo via rustup (user-level, no root)
_install_rust() {
  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}Rust & Cargo${RESET} via rustup ... "
  if curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
      | sh -s -- -y --no-modify-path &>/dev/null; then
    # Source cargo env so cargo is available immediately in this session
    # shellcheck source=/dev/null
    [[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
    export PATH="$HOME/.cargo/bin:$PATH"
    if command -v cargo &>/dev/null; then
      echo -e "${GREEN}done ($(cargo --version))${RESET}"
      log "[SUCCESS] rust & cargo installed via rustup"
      return
    fi
  fi
  echo -e "${RED}failed${RESET}"
  warn "Could not install Rust — Cargo-based tools will be skipped."
  log "[WARN] rustup install failed"
}

# Install Ruby
_install_ruby() {
  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}Ruby${RESET} ... "
  local ok=false
  case "$PKG_MGR" in
    apt)    $SUDO apt-get install -y \
              -o Dpkg::Options::="--force-confdef" \
              -o Dpkg::Options::="--force-confold" \
              ruby ruby-dev ruby-rubygems &>/dev/null && ok=true ;;
    dnf)    $SUDO dnf install -y ruby ruby-devel &>/dev/null && ok=true ;;
    pacman) $SUDO pacman -S --noconfirm ruby &>/dev/null && ok=true ;;
    brew)   brew install ruby &>/dev/null && ok=true ;;
  esac
  if $ok && command -v ruby &>/dev/null; then
    echo -e "${GREEN}done ($(ruby --version | awk '{print $2}'))${RESET}"
    log "[SUCCESS] ruby installed"
  else
    echo -e "${RED}failed${RESET}"
    warn "Could not install Ruby — gem-based tools will be skipped."
    log "[WARN] ruby install failed"
  fi
}

# ─── Bootstrap Essential Tools ────────────────────────────────────────────────
# Installs curl, ca-certificates, gnupg, lsb-release BEFORE any other step.
# These are needed by Go/Rust/Trivy downloaders and repo setup.
# Uses apt/brew directly (no curl required for this step).
bootstrap_essentials() {
  if [[ "$DRY_RUN" == true ]]; then
    return
  fi

  local need=()
  command -v curl        &>/dev/null || need+=("curl")
  command -v gpg         &>/dev/null || need+=("gpg")

  if [[ ${#need[@]} -eq 0 ]]; then
    return  # Nothing to bootstrap
  fi

  section "Bootstrapping Essential Tools"
  info "Installing: ${need[*]} (required for downloaders and repo setup)"

  case "$PKG_MGR" in
    apt)
      echo -ne "  ${CYAN}↳${RESET} Running apt-get update (bootstrap) ... "
      $SUDO apt-get update -qq &>/dev/null \
        && echo -e "${GREEN}done${RESET}" \
        || echo -e "${YELLOW}skipped${RESET}"
      echo -ne "  ${CYAN}↳${RESET} Installing curl, ca-certificates, gnupg, lsb-release ... "
      if $SUDO apt-get install -y \
          -o Dpkg::Options::="--force-confdef" \
          -o Dpkg::Options::="--force-confold" \
          curl ca-certificates gnupg lsb-release &>/dev/null; then
        echo -e "${GREEN}done${RESET}"
        log "[SUCCESS] bootstrap essentials installed"
      else
        echo -e "${RED}failed${RESET}"
        warn "Could not install bootstrap tools — some installers may fail"
      fi
      ;;
    dnf)
      echo -ne "  ${CYAN}↳${RESET} Installing curl, ca-certificates, gnupg ... "
      if $SUDO dnf install -y curl ca-certificates gnupg &>/dev/null; then
        echo -e "${GREEN}done${RESET}"
      else
        echo -e "${RED}failed${RESET}"
      fi
      ;;
    pacman)
      echo -ne "  ${CYAN}↳${RESET} Installing curl, ca-certificates, gnupg ... "
      if $SUDO pacman -S --noconfirm curl ca-certificates gnupg &>/dev/null; then
        echo -e "${GREEN}done${RESET}"
      else
        echo -e "${RED}failed${RESET}"
      fi
      ;;
    brew)
      brew install curl ca-certificates gnupg &>/dev/null || \
        warn "Could not install bootstrap tools — some installers may fail"
      ;;
  esac
}

# ─── Prereq Checks & Auto-Install ─────────────────────────────────────────────
check_prerequisites() {
  section "Checking & Installing Prerequisites"
  if [[ "$DRY_RUN" == true ]]; then
    dry "missing prerequisites: Python, git, Go, Rust/Cargo and Ruby"
    return
  fi

  # ── python3 + pip3 (hard required) ──
  if ! command -v python3 &>/dev/null; then
    _install_python
  elif ! python3 -m pip --version &>/dev/null && \
       { [[ -z "${VIRTUAL_ENV:-}" ]] || ! command -v uv &>/dev/null; }; then
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
      python3 -m ensurepip --upgrade || { error "Cannot prepare pip in the active environment"; exit 1; }
    else
      _install_python
    fi
  else
    success "python3 $(python3 --version 2>&1 | awk '{print $2}') — already installed"
  fi

  # ── git (hard required) ──
  if ! command -v git &>/dev/null; then
    _install_git
  else
    success "git $(git --version | awk '{print $3}') — already installed"
  fi

  # ── Go (optional — needed for many tools) ──
  if ! command -v go &>/dev/null; then
    _install_go
  else
    success "go $(go version | awk '{print $3}') — already installed"
  fi

  # ── Rust / Cargo (optional — rustscan, feroxbuster) ──
  if ! command -v cargo &>/dev/null; then
    # Source cargo env in case rustup was already run but PATH not updated
    [[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env" 2>/dev/null || true
    if ! command -v cargo &>/dev/null; then
      _install_rust
    else
      success "cargo $(cargo --version) — already installed"
    fi
  else
    success "cargo $(cargo --version) — already installed"
  fi

  # ── Ruby (optional — wpscan, evil-winrm, zsteg) ──
  if ! command -v ruby &>/dev/null; then
    _install_ruby
  else
    success "ruby $(ruby --version | awk '{print $2}') — already installed"
  fi
}

# ─── Setup PATH ───────────────────────────────────────────────────────────────
# Ensure Go, pip, cargo, gem bin directories are in PATH so tool_exists finds
# binaries immediately after installation.
setup_paths() {
  mkdir -p "$HOME/.local/bin" 2>/dev/null || true
  export PATH="$HOME/.local/bin:$PATH"

  if command -v go &>/dev/null; then
    local gobin
    gobin="$(go env GOPATH 2>/dev/null || echo "$HOME/go")/bin"
    mkdir -p "$gobin" 2>/dev/null || true
    export PATH="$gobin:$PATH"
  fi

  if [[ -d "$HOME/.cargo/bin" ]]; then
    export PATH="$HOME/.cargo/bin:$PATH"
  fi

  if command -v ruby &>/dev/null; then
    local gembin
    gembin="$(ruby -e 'puts Gem.user_dir' 2>/dev/null)/bin"
    mkdir -p "$gembin" 2>/dev/null || true
    export PATH="$gembin:$PATH"
  fi
  [[ -n "${VIRTUAL_ENV:-}" ]] && export PATH="$VIRTUAL_ENV/bin:$PATH"
  if [[ "$OS" == "macos" ]]; then
    export PATH="$HOME/.local/share/nyxstrike-tools/bin:$PATH"
  fi
}

# ─── Install Helpers ──────────────────────────────────────────────────────────

# Check if a tool is already installed
tool_exists() {
  local cmd="$1"
  command -v "$cmd" &>/dev/null
}

# Keep complete build diagnostics without flooding the terminal.
_run_install_logged() {
  local description="$1" output status=0
  shift
  output="$(mktemp "${TMPDIR:-/tmp}/nyxstrike-install.XXXXXX")" || return 1
  log "[ATTEMPT] $description"
  "$@" > "$output" 2>&1 || status=$?
  if ! cat "$output" >> "$LOG_FILE" 2>/dev/null; then
    warn "Cannot append to $LOG_FILE; full output retained at $output"
    tail -n 15 "$output" >&2
  else
    if [[ "$status" -ne 0 ]]; then
      printf '\n%s failed (exit %s). Last output; full details in %s:\n' \
        "$description" "$status" "$LOG_FILE" >&2
      tail -n 15 "$output" >&2
    fi
    rm -f "$output"
  fi
  log "[RESULT] $description exit=$status"
  return "$status"
}

# Package manager install (apt/dnf/pacman/brew)
# apt calls use -o Dpkg::Options to suppress config-file prompts in Docker/CI.
_pkg_install() {
  local pkg="$1"
  case "$PKG_MGR" in
    apt)    _run_install_logged "apt: $pkg" $SUDO apt-get install -y \
              -o Dpkg::Options::="--force-confdef" \
              -o Dpkg::Options::="--force-confold" \
              "$pkg" ;;
    dnf)    _run_install_logged "dnf: $pkg" $SUDO dnf install -y "$pkg" ;;
    pacman) _run_install_logged "pacman: $pkg" $SUDO pacman -S --noconfirm "$pkg" ;;
    brew)
      [[ "$pkg" != "bulk-extractor" ]] || pkg="bulk_extractor"
      _run_install_logged "brew: $pkg" brew install "$pkg"
      ;;
    *)      return 1 ;;
  esac
}

# Protect installed project dependencies when adding external tools.
# A subshell keeps temporary-file cleanup traps local to this installation.
_pip_install() (
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    local constraints filtered
    constraints="$(mktemp "${TMPDIR:-/tmp}/nyxstrike-pip-constraints.XXXXXX")" || return 1
    filtered="$(mktemp "${TMPDIR:-/tmp}/nyxstrike-pip-filtered.XXXXXX")" || {
      rm -f "$constraints"
      return 1
    }
    trap 'rm -f "$constraints" "$filtered"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    if command -v uv &>/dev/null; then
      if ! uv pip freeze --python "$VIRTUAL_ENV/bin/python" > "$constraints"; then
        error "Cannot protect existing Python dependencies; skipping tool installation"
        return 1
      fi
    else
      if ! "$VIRTUAL_ENV/bin/python" -m pip freeze --all > "$constraints"; then
        error "Cannot protect existing Python dependencies; skipping tool installation"
        return 1
      fi
    fi
    # Keep the server environment pinned while allowing the explicitly
    # requested top-level package to be repaired or upgraded.
    python3 - "$constraints" "$filtered" "$@" <<'PY' || return 1
import re
import sys

source, destination, *arguments = sys.argv[1:]

def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()

requested = set()
for argument in arguments:
    if argument.startswith("-"):
        continue
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[|\s*@|[<>=!~]|$)", argument)
    if match:
        requested.add(normalized(match.group(1)))

with open(source, encoding="utf-8") as input_file, open(destination, "w", encoding="utf-8") as output_file:
    for line in input_file:
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:==|\s*@)", line)
        if match and normalized(match.group(1)) in requested:
            continue
        output_file.write(line)
PY
    mv -f "$filtered" "$constraints" || return 1
    if command -v uv &>/dev/null; then
      _run_install_logged "Python package: $*" uv pip install --python "$VIRTUAL_ENV/bin/python" --quiet --constraint "$constraints" "$@"
    else
      _run_install_logged "Python package: $*" "$VIRTUAL_ENV/bin/python" -m pip install --quiet --constraint "$constraints" "$@"
    fi
  else
    # PEP 668 fallback applies only to user installs outside a project environment.
    _run_install_logged "Python user package: $*" python3 -m pip install --user --quiet "$@" || \
      _run_install_logged "Python user package fallback: $*" python3 -m pip install --user --quiet --break-system-packages "$@"
  fi
)

# go install
# Always cleans build cache + module cache after each install to prevent
# disk exhaustion in space-constrained environments (Docker, CI, VMs).
# The installed binary in $GOPATH/bin is preserved; only caches are removed.
_go_install() {
  command -v go &>/dev/null || return 1
  local ret=0
  _run_install_logged "Go package: $1" go install "$1" || ret=$?
  # Free Go disk usage immediately — binary is already placed in GOPATH/bin
  go clean -cache -modcache 2>/dev/null || true
  return $ret
}

# cargo install
_cargo_install() {
  command -v cargo &>/dev/null || return 1
  _run_install_logged "Cargo package: $1" cargo install --quiet "$1"
}

# gem --user-install
_gem_install() {
  command -v gem &>/dev/null || return 1
  _run_install_logged "Ruby gem: $1" gem install --user-install --no-document --quiet "$1"
}

# Install Python tools from official sources without changing the server environment.
_install_macos_source_tool() (
  local package="$1" binary="$2" source="$3"
  local bin_dir="${4:-$HOME/.local/bin}"
  local base="$HOME/.local/share/nyxstrike-tools"
  local staging="" wrapper="" published=false samba_path="" dependency
  command -v uv &>/dev/null || {
    echo "uv is required; run the NyxStrike launcher first." >&2
    return 1
  }
  if [[ "$package" == "enum4linux-ng" ]]; then
    for dependency in nmblookup net rpcclient smbclient; do
      if ! tool_exists "$dependency"; then
        _pkg_install samba || return 1
        samba_path="$(brew --prefix samba)" || return 1
        samba_path="$samba_path/bin:$samba_path/sbin"
        export PATH="$samba_path:$PATH"
        break
      fi
    done
    for dependency in nmblookup net rpcclient smbclient; do
      tool_exists "$dependency" || {
        echo "enum4linux-ng requires Samba command: $dependency" >&2
        return 1
      }
    done
  fi
  mkdir -p "$base" "$bin_dir" || return 1
  staging="$(mktemp -d "$base/$package.XXXXXX")" || return 1
  trap '[[ -z "$wrapper" ]] || rm -f "$wrapper"; if [[ "$published" != true ]]; then rm -rf "$staging"; fi' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  unset VIRTUAL_ENV PYTHONHOME PYTHONPATH UV_PROJECT_ENVIRONMENT UV_PYTHON
  export PYTHONNOUSERSITE=1 UV_TOOL_DIR="$staging/tools" UV_TOOL_BIN_DIR="$staging/bin"
  _run_install_logged "$package isolated installation" uv tool install --no-config \
    --python 3.12 --managed-python --from "$source" "$package" || return 1
  [[ -x "$UV_TOOL_BIN_DIR/$binary" ]] || return 1
  wrapper="$(mktemp "$bin_dir/.$binary.XXXXXX")" || return 1
  printf '#!/usr/bin/env bash\nunset PYTHONHOME PYTHONPATH\nexport PYTHONNOUSERSITE=1\n' > "$wrapper" || return 1
  if [[ -n "$samba_path" ]]; then
    printf 'export PATH=%q:"$PATH"\n' "$samba_path" >> "$wrapper" || return 1
  fi
  printf 'exec %q "$@"\n' "$UV_TOOL_BIN_DIR/$binary" >> "$wrapper" || return 1
  chmod +x "$wrapper" || return 1
  _run_install_logged "$package startup check" "$wrapper" --help || return 1
  [[ ! -d "$bin_dir/$binary" ]] || return 1
  mv -f "$wrapper" "$bin_dir/$binary" || return 1
  published=true
)

_install_macos_wafw00f() {
  _install_macos_source_tool wafw00f wafw00f \
    "git+https://github.com/EnableSecurity/wafw00f.git@69fbe3956bba47a172cf87e40e9037535d32a130" \
    "$HOME/.local/share/nyxstrike-tools/bin"
}

# Sublist3r's legacy wheel metadata breaks uv tool installation. Keep its source
# tree (including subbrute data) and install only requirements into a private venv.
_install_macos_sublist3r() (
  local base="$HOME/.local/share/nyxstrike-tools"
  local staging="" wrapper="" published=false
  local revision="729d649ec5370730172bf6f5314aafd68c874124"
  command -v uv &>/dev/null && command -v git &>/dev/null || return 1
  mkdir -p "$base/bin" || return 1
  staging="$(mktemp -d "$base/sublist3r.XXXXXX")" || return 1
  trap '[[ -z "$wrapper" ]] || rm -f "$wrapper"; if [[ "$published" != true ]]; then rm -rf "$staging"; fi' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  unset VIRTUAL_ENV PYTHONHOME PYTHONPATH UV_PROJECT_ENVIRONMENT UV_PYTHON
  export PYTHONNOUSERSITE=1
  _run_install_logged "Sublist3r source directory" git init --quiet "$staging/source" || return 1
  _run_install_logged "Sublist3r official remote" git -C "$staging/source" remote add origin \
    https://github.com/aboul3la/Sublist3r.git || return 1
  _run_install_logged "Sublist3r source download" git -C "$staging/source" fetch --depth 1 origin "$revision" || return 1
  _run_install_logged "Sublist3r source checkout" git -C "$staging/source" checkout --detach FETCH_HEAD || return 1
  [[ "$(git -C "$staging/source" rev-parse HEAD)" == "$revision" ]] || return 1
  _run_install_logged "Sublist3r isolated Python" uv venv --no-config --python 3.12 \
    --managed-python "$staging/venv" || return 1
  _run_install_logged "Sublist3r dependencies" uv pip install --no-config \
    --python "$staging/venv/bin/python" -r "$staging/source/requirements.txt" || return 1
  wrapper="$(mktemp "$base/bin/.sublist3r.XXXXXX")" || return 1
  printf '#!/usr/bin/env bash\nunset PYTHONHOME PYTHONPATH\nexport PYTHONNOUSERSITE=1\nexec %q %q "$@"\n' \
    "$staging/venv/bin/python" "$staging/source/sublist3r.py" > "$wrapper" || return 1
  chmod +x "$wrapper" || return 1
  _run_install_logged "Sublist3r startup check" "$wrapper" --help || return 1
  [[ ! -d "$base/bin/sublist3r" ]] || return 1
  mv -f "$wrapper" "$base/bin/sublist3r" || return 1
  published=true
)

# Install the same stable WPScan release in a private Homebrew Ruby when its
# formula cannot build on an older macOS host. Direct RubyGems installation can
# use Nokogiri's signed platform gem instead of forcing a local libxml2 build.
_install_macos_wpscan_gem() (
  local base="$HOME/.local/share/nyxstrike-tools" stage="" ruby_prefix default_gems
  local published=false
  brew install ruby@3.4 || return 1
  ruby_prefix="$(brew --prefix ruby@3.4)" || return 1
  [[ -x "$ruby_prefix/bin/ruby" && -x "$ruby_prefix/bin/gem" ]] || return 1
  mkdir -p "$base" || return 1
  stage="$(mktemp -d "$base/wpscan-gems.XXXXXX")" || return 1
  trap '[[ "$published" == true ]] || rm -rf -- "$stage"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  unset GEM_HOME GEM_PATH RUBYOPT RUBYLIB RUBYGEMS_GEMDEPS
  default_gems="$("$ruby_prefix/bin/ruby" -e 'puts Gem.default_dir')" || return 1
  export GEM_HOME="$stage/gems" GEM_PATH="$stage/gems:$default_gems"
  export PATH="$ruby_prefix/bin:$PATH"
  mkdir -p "$stage/bin" || return 1
  _run_install_logged "WPScan 4.1.0 RubyGems fallback" \
    "$ruby_prefix/bin/gem" install --no-document --install-dir "$GEM_HOME" \
    --bindir "$stage/bin" --version 4.1.0 wpscan || return 1
  [[ -x "$stage/bin/wpscan" ]] || return 1
  _macos_probe /usr/bin/env "GEM_HOME=$GEM_HOME" "GEM_PATH=$GEM_PATH" \
    "$ruby_prefix/bin/ruby" "$stage/bin/wpscan" --version || return 1
  _macos_publish wpscan /usr/bin/env "GEM_HOME=$GEM_HOME" "GEM_PATH=$GEM_PATH" \
    "$ruby_prefix/bin/ruby" "$stage/bin/wpscan" || return 1
  published=true
)

# Prefer WPScan's official Homebrew tap. If its source-only Nokogiri build is
# incompatible with the macOS release, fall back to the same stable gem.
_install_macos_wpscan() (
  local formula="wpscanteam/tap/wpscan" prefix="" wrapper=""
  local managed_bin="$HOME/.local/share/nyxstrike-tools/bin"
  command -v brew &>/dev/null || return 1
  unset GEM_HOME GEM_PATH RUBYOPT RUBYLIB RUBYGEMS_GEMDEPS
  prefix="$(brew --prefix "$formula" 2>/dev/null)" || prefix=""
  if [[ -z "$prefix" || ! -x "$prefix/bin/wpscan" ]] || \
      ! _run_install_logged "WPScan existing formula check" "$prefix/bin/wpscan" --version; then
    if [[ -n "$prefix" && -d "$prefix" ]]; then
      _run_install_logged "WPScan damaged formula repair" brew reinstall "$formula" || \
        { _install_macos_wpscan_gem; return $?; }
    else
      _pkg_install "$formula" || { _install_macos_wpscan_gem; return $?; }
    fi
    prefix="$(brew --prefix "$formula" 2>/dev/null)" || prefix=""
  fi
  [[ -x "$prefix/bin/wpscan" ]] || { _install_macos_wpscan_gem; return $?; }
  mkdir -p "$managed_bin" || return 1
  wrapper="$(mktemp "$managed_bin/.wpscan.XXXXXX")" || return 1
  trap '[[ -z "$wrapper" ]] || rm -f "$wrapper"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  printf '#!/usr/bin/env bash\nunset GEM_HOME GEM_PATH RUBYOPT RUBYLIB RUBYGEMS_GEMDEPS\nexec %q "$@"\n' \
    "$prefix/bin/wpscan" > "$wrapper" || return 1
  chmod +x "$wrapper" || return 1
  if ! _run_install_logged "WPScan startup check" "$wrapper" --version; then
    _install_macos_wpscan_gem
    return $?
  fi
  [[ ! -d "$managed_bin/wpscan" ]] || return 1
  mv -f "$wrapper" "$managed_bin/wpscan" || return 1
)

# git clone (shallow) to a target directory
_git_install() {
  local url="$1"
  local dir="$2"
  command -v git &>/dev/null || return 1
  mkdir -p "$(dirname "$dir")" 2>/dev/null || true
  rm -rf "$dir" 2>/dev/null || true
  git clone --depth 1 --quiet "$url" "$dir" 2>/dev/null
}

# Create a wrapper script in ~/.local/bin for a git-cloned tool
_make_wrapper() {
  local name="$1"    # binary name
  local run_cmd="$2"  # e.g. "python3 /path/to/tool.py"
  mkdir -p "$HOME/.local/bin"
  cat > "$HOME/.local/bin/$name" <<WRAP
#!/usr/bin/env bash
exec $run_cmd "\$@"
WRAP
  chmod +x "$HOME/.local/bin/$name"
}

# These two legacy tools need runtimes separate from the Python server and
# macOS's system Ruby. Keep their executables separate from unrelated user tools.
_install_macos_wfuzz() (
  local base="$HOME/.local/share/nyxstrike-tools"
  local wrapper=""
  command -v uv &>/dev/null || {
    echo "Wfuzz requires uv; run nyxstrike.sh first to prepare it." >&2
    return 1
  }
  export UV_TOOL_DIR="$base/uv"
  export UV_TOOL_BIN_DIR="$base/uv-bin"
  export PYTHONNOUSERSITE=1
  unset PYTHONHOME PYTHONPATH
  # Python 3.12 removes imp, and newer pyparsing breaks Wfuzz's filters. Use a
  # wheel for PycURL so a curl-config from Anaconda cannot enter its build.
  uv tool install --force --python 3.11 --managed-python \
    --with 'pyparsing==2.4.7' --with 'setuptools<82' \
    --with 'pycurl==7.47.0' --no-build-package pycurl \
    'wfuzz @ https://github.com/xmendez/wfuzz/archive/2263cd0932fef333118cd197656f709141bab615.tar.gz' || return 1
  mkdir -p "$base/bin" || return 1
  wrapper="$(mktemp "$base/bin/.wfuzz.XXXXXX")" || return 1
  trap '[[ -z "$wrapper" ]] || rm -f "$wrapper"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  # Keep Python environment isolation when the tool runs after this subshell.
  printf '#!/usr/bin/env bash\nexport PYTHONNOUSERSITE=1\nunset PYTHONHOME PYTHONPATH\nexec %q "$@"\n' \
    "$UV_TOOL_BIN_DIR/wfuzz" > "$wrapper" || return 1
  chmod +x "$wrapper" || return 1
  "$wrapper" --version || return 1
  [[ ! -d "$base/bin/wfuzz" ]] || return 1
  mv -f "$wrapper" "$base/bin/wfuzz" || return 1
)

_install_macos_whatweb() (
  local ruby_prefix ruby_bin gem_bin default_gems
  local base="$HOME/.local/share/nyxstrike-tools"
  local staging="" wrapper="" published=false
  local revision="d279d93042d034f3fd29d5a893d44ccc0595d3f8"
  command -v brew &>/dev/null && command -v git &>/dev/null || {
    echo "WhatWeb requires Homebrew and git." >&2
    return 1
  }
  ruby_prefix="$(brew --prefix ruby 2>/dev/null)" || ruby_prefix=""
  if [[ -z "$ruby_prefix" || ! -x "$ruby_prefix/bin/ruby" || ! -f "$ruby_prefix/bin/gem" ]]; then
    brew install ruby || return 1
    ruby_prefix="$(brew --prefix ruby)" || return 1
  fi
  ruby_bin="$ruby_prefix/bin/ruby"
  gem_bin="$ruby_prefix/bin/gem"
  [[ -x "$ruby_bin" && -f "$gem_bin" ]] || return 1
  unset RUBYOPT RUBYLIB RUBYGEMS_GEMDEPS
  default_gems="$("$ruby_bin" -e 'puts Gem.default_dir')" || return 1
  mkdir -p "$base/bin" || return 1
  staging="$(mktemp -d "$base/whatweb-v0.6.4.XXXXXX")" || return 1
  # Only remove paths created by this invocation; never replace a user checkout.
  trap '[[ -z "$wrapper" ]] || rm -f "$wrapper"; if [[ "$published" != true ]]; then rm -rf "$staging"; fi' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  git clone --depth 1 --branch v0.6.4 \
    https://github.com/urbanadventurer/WhatWeb.git "$staging/source" || return 1
  [[ "$(git -C "$staging/source" rev-parse HEAD)" == "$revision" ]] || {
    echo "WhatWeb v0.6.4 did not match the expected official revision." >&2
    return 1
  }
  export GEM_HOME="$staging/gems"
  export GEM_PATH="$GEM_HOME:$default_gems"
  "$ruby_bin" "$gem_bin" install --no-document ipaddr addressable json || return 1
  wrapper="$(mktemp "$base/bin/.whatweb.XXXXXX")" || return 1
  # Bash %q safely preserves spaces, quotes and shell metacharacters in paths.
  printf '#!/usr/bin/env bash\nexport GEM_HOME=%q\nexport GEM_PATH=%q\nunset RUBYOPT RUBYLIB RUBYGEMS_GEMDEPS\nexec %q %q "$@"\n' \
    "$GEM_HOME" "$GEM_PATH" "$ruby_bin" "$staging/source/whatweb" > "$wrapper" || return 1
  chmod +x "$wrapper" || return 1
  "$wrapper" --version || return 1
  [[ ! -d "$base/bin/whatweb" ]] || return 1
  mv -f "$wrapper" "$base/bin/whatweb" || return 1
  published=true
)

_install_verified_macos_web_tool() {
  local name="$1" installer="$2" description="$3"
  local probe="${4:---version}" managed_only="${5:-false}" executable=""
  local managed_bin="$HOME/.local/share/nyxstrike-tools/bin"
  if [[ "$DRY_RUN" == true ]]; then
    dry "$name ($description)"
    return 0
  fi
  export PATH="$managed_bin:$PATH"
  if [[ "$managed_only" == true ]]; then
    executable="$managed_bin/$name"
  else
    executable="$(command -v "$name")" || executable=""
  fi
  if [[ -x "$executable" ]] && "$executable" "$probe" >> "$LOG_FILE" 2>&1; then
    skip "$name — already installed and $probe verified ($executable)"
    (( COUNT_ALREADY++ )) || true
    return 0
  fi
  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}$name${RESET} ($description) ... "
  if "$installer" >> "$LOG_FILE" 2>&1 && \
      "$managed_bin/$name" "$probe" >> "$LOG_FILE" 2>&1; then
    echo -e "${GREEN}done${RESET}"
    success "$name installed and $probe verified"
    (( COUNT_INSTALLED++ )) || true
    return 0
  fi
  local reason="installation or $probe check failed; details: $LOG_FILE"
  echo -e "${RED}failed${RESET}"
  error "$name: $reason"
  tail -n 8 "$LOG_FILE" >&2
  FAILED_TOOLS+=("$name")
  FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="$reason"
  (( COUNT_FAILED++ )) || true
  return 1
}

# macOS recipes share their inventory with the server's availability checks.
# Keep this compatible with Apple's Bash 3.2 (no associative arrays).
MACOS_HANDLED="|"

_macos_probe() {
  env -u PYTHONHOME -u PYTHONPATH python3 - "$@" <<'PY'
import os
import signal
import subprocess
import sys

try:
    child = subprocess.Popen(sys.argv[1:], stdin=subprocess.DEVNULL,
                             start_new_session=True)
    try:
        status = child.wait(timeout=60)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()
        print("Startup validation timed out", file=sys.stderr)
        status = 124
except OSError as error:
    print(error, file=sys.stderr)
    status = 1
sys.exit(status if status >= 0 else 1)
PY
}

_macos_publish() (
  local name="$1" executable="$2" wrapper=""
  shift 2
  local bindir="$HOME/.local/share/nyxstrike-tools/bin"
  [[ -x "$executable" && "$name" != */* ]] || return 1
  mkdir -p "$bindir" || return 1
  [[ ! -d "$bindir/$name" ]] || return 1
  wrapper="$(mktemp "$bindir/.$name.XXXXXX")" || return 1
  trap 'rm -f "$wrapper"' EXIT
  {
    printf '#!/usr/bin/env bash\nunset PYTHONHOME PYTHONPATH RUBYOPT RUBYLIB\nexport PYTHONNOUSERSITE=1\nexec %q' "$executable"
    [[ "$#" -eq 0 ]] || printf ' %q' "$@"
    printf ' "$@"\n'
  } > "$wrapper" || return 1
  chmod +x "$wrapper" && mv -f "$wrapper" "$bindir/$name"
)

_macos_check() {
  local name="$1" binary="$2" probe="$3" executable="${4:-}" output
  if [[ -z "$executable" ]]; then
    executable="$(command -v "$binary")" || return 1
  fi
  [[ -x "$executable" ]] || return 1
  [[ "$probe" != "@file" ]] || { [[ -x "$executable" ]]; return; }
  if [[ "$name" == "httpx" ]]; then
    # This path is also the server's default BINARY_PATH_OVERRIDES entry.
    executable="$HOME/go/bin/httpx"
    output="$(_macos_probe "$executable" -version 2>&1)" || return 1
    printf '%s\n' "$output"
    [[ "$output" == *projectdiscovery.io* ]] || return 1
    return 0
  fi
  case "$name" in
    msfvenom)
      local status=0
      output="$(_macos_probe "$executable" --help 2>&1)" || status=$?
      printf '%s\n' "$output"
      [[ "$status" -le 1 && "$output" == *MsfVenom* && "$output" == *Usage:* ]]
      return ;;
    airbase-ng|airdecap-ng|aireplay-ng|airodump-ng)
      # These upstream CLIs intentionally return 1 when printing --help.
      local status=0
      output="$(_macos_probe "$executable" --help 2>&1)" || status=$?
      printf '%s\n' "$output"
      [[ "$status" -le 1 && "$output" == *"$name"* && "$output" == *[Uu]sage* ]]
      return ;;
  esac
  local arguments=()
  # Recipe arguments are literal, space-separated flags; never evaluate them.
  read -r -a arguments <<< "$probe"
  _macos_probe "$executable" "${arguments[@]}" || return 1
  if [[ "$name" == "vulnx" ]]; then
    _macos_probe "$executable" id --help --disable-update-check &&
      _macos_probe "$executable" search --help --disable-update-check &&
      _macos_probe "$executable" auth --help --disable-update-check || return 1
  elif [[ "$name" == "shuffledns" ]]; then
    _macos_probe "$(command -v massdns)" --help || return 1
  elif [[ "$name" == "impacket-scripts" ]]; then
    local required
    for required in secretsdump.py impacket-secretsdump; do
      executable="$(command -v "$required" 2>/dev/null)" || continue
      _macos_probe "$executable" -h && return 0
    done
    return 1
  fi
}

_macos_brew() {
  local name="$1" binary="$2" formula="$3" probe="${4:---help}" prefix candidate healthy
  if [[ "$name" == kismet ]] && brew command trust >/dev/null 2>&1; then
    # Homebrew also loads this official companion formula during conflict checks.
    brew tap kismetwireless/kismet || return 1
    brew trust --formula kismetwireless/kismet/kismet || return 1
    brew trust --formula kismetwireless/kismet/kismet-git || return 1
  fi
  prefix="$(brew --prefix "$formula" 2>/dev/null)" || prefix=""
  if [[ -z "$prefix" || ! -d "$prefix" ]]; then
    brew install "$formula" || return 1
    prefix="$(brew --prefix "$formula")" || return 1
  elif [[ "$name" == "ghidra" ]]; then
    if [[ ! -x "$prefix/libexec/support/analyzeHeadless" ||
          ! -x "$prefix/bin/ghidraRun" ]]; then
      brew reinstall "$formula" || return 1
      prefix="$(brew --prefix "$formula")" || return 1
    fi
  else
    healthy=""
    for candidate in "$prefix/bin/$binary" "$prefix/sbin/$binary" \
                     "$prefix/libexec/bin/$binary"; do
      [[ -x "$candidate" ]] || continue
      if _macos_check "$name" "$binary" "$probe" "$candidate"; then
        healthy="$candidate"
        break
      fi
    done
    if [[ -z "$healthy" ]]; then
      brew reinstall "$formula" || return 1
      prefix="$(brew --prefix "$formula")" || return 1
    fi
  fi
  if [[ "$name" == "ghidra" ]]; then
    local java_prefix
    java_prefix="$(brew --prefix openjdk@21)" || return 1
    [[ -x "$prefix/libexec/support/analyzeHeadless" ]] || return 1
    _macos_probe "$java_prefix/bin/java" -version || return 1
    _macos_publish analyzeHeadless /usr/bin/env \
      "JAVA_HOME=$java_prefix/libexec/openjdk.jdk/Contents/Home" \
      "$prefix/libexec/support/analyzeHeadless" || return 1
    _macos_publish ghidra "$prefix/bin/ghidraRun"
    return
  fi
  for candidate in "$prefix/bin/$binary" "$prefix/sbin/$binary" \
                   "$prefix/libexec/bin/$binary"; do
    if [[ -x "$candidate" ]]; then
      _macos_check "$name" "$binary" "$probe" "$candidate" || continue
      _macos_publish "$binary" "$candidate" || return 1
      if [[ "$name" == "rpcclient" ]]; then
        local dependency
        for dependency in net nmblookup smbclient; do
          [[ ! -x "$prefix/bin/$dependency" ]] ||
            _macos_publish "$dependency" "$prefix/bin/$dependency" || return 1
        done
      elif [[ "$name" == "sleuthkit" ]]; then
        _macos_publish icat "$prefix/bin/icat" || return 1
      fi
      return 0
    fi
  done
  echo "Homebrew package $formula did not provide $binary ($prefix)" >&2
  return 1
}

_macos_java11_home() {
  /usr/libexec/java_home -v 11 2>/dev/null
}

_macos_java11_check() {
  local java_home
  java_home="$(_macos_java11_home)" || return 1
  [[ -x "$java_home/bin/java" ]] || return 1
  _macos_probe "$java_home/bin/java" -version || return 1
  printf '%s\n' "$java_home"
}

_macos_cask_check() {
  local name="$1" application appdir executable java_home
  case "$name" in
    burpsuite) application="Burp Suite.app" ;;
    maltego) application="Maltego.app" ;;
    *) return 1 ;;
  esac
  for appdir in "/Applications/$application" "$HOME/Applications/$application"; do
    [[ -d "$appdir" ]] || continue
    executable="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$appdir/Contents/Info.plist")" || return 1
    [[ -x "$appdir/Contents/MacOS/$executable" ]] || return 1
    if [[ "$name" == maltego ]]; then
      java_home="$(_macos_java11_check)" || return 1
    fi
    printf '%s\n' "$appdir/Contents/MacOS/$executable"
    return 0
  done
  return 1
}

_macos_cask() {
  local name="$1" cask="$2" application executable java_home
  case "$name" in
    burpsuite) application="Burp Suite.app" ;;
    maltego) application="Maltego.app" ;;
    *) return 1 ;;
  esac
  if [[ "$name" == maltego ]] && ! java_home="$(_macos_java11_check)"; then
    if brew list --cask temurin@11 >/dev/null 2>&1; then
      brew reinstall --cask temurin@11 || return 1
    else
      brew install --cask temurin@11 || return 1
    fi
    java_home="$(_macos_java11_check)" || return 1
  fi
  if ! executable="$(_macos_cask_check "$name")"; then
    if brew list --cask "$cask" >/dev/null 2>&1; then
      brew reinstall --cask "$cask" || return 1
    elif [[ -d "/Applications/$application" || -d "$HOME/Applications/$application" ]]; then
      # A broken app copied outside Homebrew is not eligible for `reinstall`.
      # Cask --force replaces the conflicting app bundle with the signed cask.
      brew install --cask --force "$cask" || return 1
    else
      brew install --cask "$cask" || return 1
    fi
    executable="$(_macos_cask_check "$name")" || return 1
  fi
  _macos_publish "$name" "$executable"
}

# Go 1.25 supports macOS 12. Resolve its latest patch and verify the official
# archive checksum instead of depending on current Homebrew's OS requirements.
_macos_go_runtime() (
  local base="$HOME/.local/share/nyxstrike-tools" stage="" published=false
  local version filename checksum arch
  arch="$(uname -m)"
  case "$arch" in x86_64) arch=amd64 ;; arm64) ;; *) return 1 ;; esac
  mkdir -p "$base/bin" || return 1
  stage="$(mktemp -d "$base/go-runtime.XXXXXX")" || return 1
  trap 'if [[ "$published" != true ]]; then rm -rf "$stage"; fi' EXIT
  curl --fail --location --retry 2 --output "$stage/releases.json" \
    'https://go.dev/dl/?mode=json&include=all' || return 1
  read -r version filename checksum < <(python3 - "$stage/releases.json" "$arch" <<'PY'
import json
import sys
with open(sys.argv[1]) as source:
    releases = json.load(source)
for release in releases:
    if release['stable'] and release['version'].startswith('go1.25.'):
        for asset in release['files']:
            if asset['os'] == 'darwin' and asset['arch'] == sys.argv[2] and asset['kind'] == 'archive':
                print(release['version'], asset['filename'], asset['sha256'])
                sys.exit(0)
sys.exit(1)
PY
  ) || return 1
  [[ "$filename" == go1.25.*.darwin-*.tar.gz && "$checksum" =~ ^[a-f0-9]{64}$ ]] || return 1
  curl --fail --location --retry 2 --output "$stage/go.tar.gz" "https://go.dev/dl/$filename" || return 1
  [[ "$(shasum -a 256 "$stage/go.tar.gz" | cut -d ' ' -f 1)" == "$checksum" ]] || return 1
  tar -xzf "$stage/go.tar.gz" -C "$stage" || return 1
  _macos_probe "$stage/go/bin/go" version || return 1
  _macos_publish go "$stage/go/bin/go" || return 1
  published=true
)

_macos_go() (
  local name="$1" binary="$2" target="$3" probe="$4"
  local base="$HOME/.local/share/nyxstrike-tools" stage="" published=false
  if ! command -v go &>/dev/null || ! _macos_probe go version; then
    _macos_go_runtime || return 1
  fi
  [[ "$name" != "shuffledns" ]] || _macos_brew massdns massdns massdns || return 1
  mkdir -p "$base" "$HOME/go/bin" || return 1
  stage="$(mktemp -d "$base/$name-go.XXXXXX")" || return 1
  trap 'if [[ "$published" != true ]]; then rm -rf "$stage"; fi' EXIT
  unset GOOS GOARCH GOFLAGS GOROOT GOAMD64 GOARM64
  export GOBIN="$stage/bin" GOTOOLCHAIN=auto
  go install "$target" || {
    _macos_go_runtime || return 1
    hash -r
    GOTOOLCHAIN=local go install "$target" || return 1
  }
  [[ -x "$stage/bin/$binary" ]] || return 1
  local arguments=()
  read -r -a arguments <<< "$probe"
  _macos_probe "$stage/bin/$binary" "${arguments[@]}" || return 1
  # Preserve the documented ~/go/bin location, including HTTPX's API override.
  [[ ! -d "$HOME/go/bin/$binary" ]] || return 1
  local temporary
  temporary="$(mktemp "$HOME/go/bin/.$binary.XXXXXX")" || return 1
  cp "$stage/bin/$binary" "$temporary" && chmod +x "$temporary" &&
    mv -f "$temporary" "$HOME/go/bin/$binary" || { rm -f "$temporary"; return 1; }
  _macos_publish "$binary" "$stage/bin/$binary" || return 1
  published=true
)

_macos_gem() (
  local binary="$1" package="$2" base="$HOME/.local/share/nyxstrike-tools"
  local stage="" prefix default_gems published=false
  prefix="$(brew --prefix ruby 2>/dev/null)" || prefix=""
  if [[ ! -x "$prefix/bin/ruby" ]]; then
    brew install ruby || return 1
    prefix="$(brew --prefix ruby)" || return 1
  fi
  mkdir -p "$base" || return 1
  stage="$(mktemp -d "$base/$binary-gems.XXXXXX")" || return 1
  trap 'if [[ "$published" != true ]]; then rm -rf "$stage"; fi' EXIT
  unset GEM_HOME GEM_PATH RUBYOPT RUBYLIB RUBYGEMS_GEMDEPS
  default_gems="$("$prefix/bin/ruby" -e 'puts Gem.default_dir')" || return 1
  export GEM_HOME="$stage/gems" GEM_PATH="$stage/gems:$default_gems"
  export PATH="$prefix/bin:$PATH"
  "$prefix/bin/ruby" "$prefix/bin/gem" install --no-document "$package" || return 1
  _macos_probe "$GEM_HOME/bin/$binary" --help || return 1
  _macos_publish "$binary" /usr/bin/env "GEM_HOME=$GEM_HOME" "GEM_PATH=$GEM_PATH" \
    "$prefix/bin/ruby" "$GEM_HOME/bin/$binary" || return 1
  published=true
)

_macos_cargo() (
  local binary="$1" spec="$2" base="$HOME/.local/share/nyxstrike-tools"
  local stage="" published=false
  brew install pkg-config openssl@3 xz || return 1
  command -v cargo &>/dev/null || _install_rust || return 1
  export OPENSSL_DIR="$(brew --prefix openssl@3)"
  export PKG_CONFIG_PATH="$(brew --prefix xz)/lib/pkgconfig:$OPENSSL_DIR/lib/pkgconfig"
  mkdir -p "$base" || return 1
  stage="$(mktemp -d "$base/$binary-cargo.XXXXXX")" || return 1
  trap 'if [[ "$published" != true ]]; then rm -rf "$stage"; fi' EXIT
  if [[ "$spec" == *@* ]]; then
    cargo install --root "$stage" "${spec%%@*}" --version "${spec#*@}" || return 1
  else
    cargo install --root "$stage" "$spec" || return 1
  fi
  _macos_probe "$stage/bin/$binary" --help || return 1
  _macos_publish "$binary" "$stage/bin/$binary" || return 1
  published=true
)

# Successful staging directories remain in place: venv entrypoints embed their
# absolute paths. Only the public wrapper is replaced, after its probe passes.
_macos_python_package() (
  local package="$1" binary="$2" spec="$3" python="$4"
  local base="$HOME/.local/share/nyxstrike-tools" staging="" published=0 script name
  local -a probe_args
  [[ "$package" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || return 1
  [[ "$binary" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || return 1
  [[ -n "$spec" && -n "$python" ]] || return 1
  command -v uv >/dev/null 2>&1 || return 1
  umask 077
  mkdir -p "$base" || return 1
  staging="$(mktemp -d "$base/${package}.XXXXXX")" || return 1
  trap 'if [[ "$published" != 1 && -n "$staging" ]]; then rm -rf -- "$staging"; fi' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  mkdir -p "$staging/tmp" "$staging/cache" "$base/python" || return 1
  unset VIRTUAL_ENV PYTHONHOME PYTHONPATH UV_PROJECT_ENVIRONMENT UV_PYTHON
  export PYTHONNOUSERSITE=1 TMPDIR="$staging/tmp"
  export UV_CACHE_DIR="$staging/cache/uv" UV_PYTHON_INSTALL_DIR="$base/python"
  _run_install_logged "macOS $package: private Python $python" \
    uv --no-config venv --managed-python --python "$python" "$staging/venv" || return 1
  if [[ "$package" == patator ]]; then
    # Patator declares every database adapter as mandatory even though its CLI
    # treats them as optional modules. cx_Oracle 8.3 has no CPython 3.13 macOS
    # wheel and breaks the entire installation before http_fuzz can be used.
    # Install the official pinned source plus the portable module dependencies.
    local patator_dependencies=(
      paramiko==3.5.1 pycurl==7.45.4 ajpy==0.0.5 impacket==0.12.0
      pycryptodomex==3.21.0 dnspython==2.7.0 IPy==1.1 pysnmp==7.1.16
      telnetlib-313-and-up==3.13.1
    )
    _macos_native_packages curl openssl@3 || return 1
    export PYCURL_SSL_LIBRARY=openssl
    export CPPFLAGS="-I$(brew --prefix openssl@3)/include -I$(brew --prefix curl)/include"
    export LDFLAGS="-L$(brew --prefix openssl@3)/lib -L$(brew --prefix curl)/lib"
    _run_install_logged "macOS patator: portable dependencies" \
      uv --no-config pip install --python "$staging/venv/bin/python" \
      "${patator_dependencies[@]}" || return 1
    _run_install_logged "macOS patator: official pinned source" \
      uv --no-config pip install --python "$staging/venv/bin/python" --no-deps "$spec" || return 1
  else
    _run_install_logged "macOS $package: $spec" \
      uv --no-config pip install --python "$staging/venv/bin/python" "$spec" || return 1
  fi
  [[ -x "$staging/venv/bin/$binary" ]] || return 1
  {
    printf '#!/bin/bash\n'
    printf 'unset VIRTUAL_ENV PYTHONHOME PYTHONPATH UV_PROJECT_ENVIRONMENT UV_PYTHON\n'
    printf 'export PYTHONNOUSERSITE=1\n'
    printf 'exec %q "$@"\n' "$staging/venv/bin/$binary"
  } > "$staging/launch" || return 1
  chmod 700 "$staging/launch" || return 1
  probe_args=(--help)
  case "$package" in
    patator) probe_args=(http_fuzz --help) ;;
    impacket|impacket-scripts) probe_args=(-h) ;;
  esac
  _macos_probe "$staging/launch" "${probe_args[@]}" || return 1
  if [[ "$package" == impacket || "$package" == impacket-scripts ]]; then
    _macos_probe "$staging/venv/bin/secretsdump.py" -h || return 1
    _macos_probe "$staging/venv/bin/smbclient.py" -h || return 1
  fi
  if [[ "$package" == impacket || "$package" == impacket-scripts ]]; then
    # Retain the validated runtime as soon as alias publication starts. The
    # primary smbclient.py wrapper is published last, so a partial attempt is
    # never accepted by the next catalog precheck.
    published=1
    for script in "$staging/venv/bin/"*.py; do
      [[ -x "$script" ]] || continue
      name="${script##*/}"
      [[ "$name" == "$binary" ]] || _macos_publish "$name" "$script" || return 1
      _macos_publish "impacket-${name%.py}" "$script" || return 1
    done
    _macos_publish "$binary" "$staging/launch" || return 1
  else
    _macos_publish "$binary" "$staging/launch" || return 1
    published=1
  fi
)

_macos_python_source() (
  local tool="$1" repository revision python entry
  local base="$HOME/.local/share/nyxstrike-tools" staging="" published=0
  local -a probe_args
  probe_args=(--help)
  case "$tool" in
    cloudmapper)
      repository=https://github.com/duo-labs/cloudmapper.git
      revision=ec8fbf201b8b43e66720cd3ee9079a801e49c61c
      python=3.9
      entry=cloudmapper.py
      # Root help intentionally exits 255; collect's argparse help exits zero.
      probe_args=(collect --help)
      ;;
    spiderfoot)
      repository=https://github.com/smicallef/spiderfoot.git
      revision=b9c345de5b085debc7444fc10e0e26e7745df5f2
      python=3.9
      entry=sf.py
      ;;
    xsser)
      repository=https://github.com/epsylon/xsser.git
      revision=dc72706d2c0dcfe52e355194d1be3b1aed4afca2
      python=3.12
      entry=xsser
      ;;
    *) return 1 ;;
  esac
  command -v uv >/dev/null 2>&1 || return 1
  command -v git >/dev/null 2>&1 || return 1
  umask 077
  mkdir -p "$base" || return 1
  staging="$(mktemp -d "$base/${tool}.XXXXXX")" || return 1
  trap 'if [[ "$published" != 1 && -n "$staging" ]]; then rm -rf -- "$staging"; fi' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  mkdir -p "$staging/tmp" "$staging/cache" "$base/python" || return 1
  unset VIRTUAL_ENV PYTHONHOME PYTHONPATH UV_PROJECT_ENVIRONMENT UV_PYTHON
  export PYTHONNOUSERSITE=1 TMPDIR="$staging/tmp"
  export UV_CACHE_DIR="$staging/cache/uv" UV_PYTHON_INSTALL_DIR="$base/python"
  if [[ "$tool" == cloudmapper ]]; then
    mkdir -p "$base/cloudmapper-config/matplotlib" || return 1
    export MPLCONFIGDIR="$base/cloudmapper-config/matplotlib"
  fi
  _run_install_logged "macOS $tool: initialize isolated source" \
    git init --quiet "$staging/source" || return 1
  git -C "$staging/source" remote add origin "$repository" || return 1
  _run_install_logged "macOS $tool: fetch $revision" \
    git -C "$staging/source" fetch --depth 1 origin "$revision" || return 1
  git -C "$staging/source" checkout --quiet --detach FETCH_HEAD || return 1
  [[ "$(git -C "$staging/source" rev-parse HEAD)" == "$revision" ]] || return 1
  [[ -f "$staging/source/$entry" && -f "$staging/source/requirements.txt" ]] || return 1
  _run_install_logged "macOS $tool: private Python $python" \
    uv --no-config venv --managed-python --python "$python" "$staging/venv" || return 1
  # Install requirements only. In particular, XSSer's legacy setup.py includes
  # absolute /usr/share data paths and must not be installed into the system.
  case "$tool" in
    cloudmapper)
      # Legacy setuptools_scm imports pkg_resources during isolated builds.
      printf 'setuptools<82\n' > "$staging/build-constraints.txt" || return 1
      _run_install_logged "macOS $tool: source dependencies" \
        uv --no-config pip install --python "$staging/venv/bin/python" \
          --build-constraint "$staging/build-constraints.txt" \
          -r "$staging/source/requirements.txt" || return 1
      ;;
    xsser)
      _run_install_logged "macOS $tool: source dependencies with bundled curl wheel" \
        uv --no-config pip install --python "$staging/venv/bin/python" \
          --only-binary pycurl -r "$staging/source/requirements.txt" pycurl==7.47.0 || return 1
      ;;
    spiderfoot)
      # PyYAML 5.x's source build predates Cython 3 (Apple Silicon lacks some
      # historical wheels). This constrains the isolated build environment.
      printf 'Cython<3\n' > "$staging/build-constraints.txt" || return 1
      _run_install_logged "macOS $tool: source dependencies" \
        uv --no-config pip install --python "$staging/venv/bin/python" \
          --build-constraint "$staging/build-constraints.txt" \
          -r "$staging/source/requirements.txt" || return 1
      ;;
    *)
      _run_install_logged "macOS $tool: source dependencies" \
        uv --no-config pip install --python "$staging/venv/bin/python" \
          -r "$staging/source/requirements.txt" || return 1
      ;;
  esac
  {
    printf '#!/bin/bash\n'
    printf 'unset VIRTUAL_ENV PYTHONHOME PYTHONPATH UV_PROJECT_ENVIRONMENT UV_PYTHON\n'
    printf 'export PYTHONNOUSERSITE=1\n'
    if [[ "$tool" == cloudmapper ]]; then
      printf 'export MPLCONFIGDIR=%q\n' "$base/cloudmapper-config/matplotlib"
    fi
    printf 'cd %q || exit 1\n' "$staging/source"
    printf 'exec %q %q "$@"\n' "$staging/venv/bin/python" "$staging/source/$entry"
  } > "$staging/launch" || return 1
  chmod 700 "$staging/launch" || return 1
  _macos_probe "$staging/launch" "${probe_args[@]}" || return 1
  _macos_publish "$tool" "$staging/launch" || return 1
  published=1
)

# Official source recipes. Successful staging directories are immutable runtimes;
# failed attempts are removed without changing a previous working installation.
_macos_native_packages() {
    local package
    for package in "$@"; do
        _pkg_install "$package" || return 1
    done
}

_macos_native_checkout() {
    local repo="$1" revision="$2" destination="$3"
    git init -q "$destination" &&
        git -C "$destination" remote add origin "https://github.com/${repo}.git" &&
        git -C "$destination" fetch -q --depth 1 origin "$revision" &&
        git -C "$destination" checkout -q --detach FETCH_HEAD &&
        [[ "$(git -C "$destination" rev-parse HEAD)" == "$revision" ]]
}

_macos_native_download() {
    local url="$1" destination="$2" digest="${3:-}"
    curl --fail --location --retry 2 --connect-timeout 20 --max-time 1800 \
        --proto '=https' --tlsv1.2 "$url" -o "$destination" || return 1
    if [[ -n "$digest" ]]; then
        [[ "$(shasum -a 256 "$destination" | awk '{print $1}')" == "$digest" ]] || {
            echo "Source archive checksum mismatch: $url" >&2
            return 1
        }
    fi
}

_macos_native_perl() {
    local tool="$1" stage="$2" repo revision script perl_prefix perl_bin cpan_bin
    local modules=()
    case "$tool" in
        dnsenum)
            repo=fwaeytens/dnsenum; revision=e3336c51a6d43d1ebb292970958e9cdc0cf93419
            script=dnsenum.pl
            modules=(Net::IP Net::DNS Net::Netmask XML::Writer String::Random)
            ;;
        dotdotpwn)
            repo=wireghoul/dotdotpwn; revision=1d3af99d7de1ab7f2a321934891ecd3ff1a02734
            script=dotdotpwn.pl; modules=(Net::FTP TFTP HTTP::Lite LWP::UserAgent LWP::Protocol::https)
            ;;
        hurl)
            repo=fnord0/hURL; revision=afca9c54c72426c52d317cb921b6965320e2f5bb
            script=hURL; modules=(CGI URI::Escape HTML::Entities)
            ;;
        joomscan)
            repo=OWASP/joomscan; revision=2ea8cc7792b3893b80a52e4ad7cc32a1a9dbf7fc
            script=joomscan.pl; modules=(LWP::UserAgent LWP::Protocol::https)
            ;;
        *) return 1 ;;
    esac
    _macos_native_packages perl cpanminus || return 1
    perl_prefix=$(brew --prefix perl) || return 1
    perl_bin="$perl_prefix/bin/perl"
    cpan_bin="$(brew --prefix cpanminus)/bin/cpanm"
    [[ -x "$perl_bin" && -f "$cpan_bin" ]] || return 1
    _macos_native_checkout "$repo" "$revision" "$stage/source" || return 1
    env -u PERL5OPT -u PERL5LIB -u PERL_LOCAL_LIB_ROOT -u PERL_MB_OPT -u PERL_MM_OPT \
        "$perl_bin" "$cpan_bin" --local-lib-contained "$stage/perl" \
        --mirror https://cpan.metacpan.org --mirror-only "${modules[@]}" || return 1
    # DotDotPwn uses relative module/data paths. Keep its working directory local
    # to its private source tree without changing the caller's shell directory.
    {
        printf '#!/bin/bash\n'
        printf 'cd %q || exit 1\n' "$stage/source"
        printf 'unset PERL5OPT PERL_LOCAL_LIB_ROOT PERL_MB_OPT PERL_MM_OPT\n'
        printf 'export PERL5LIB=%q\n' "$stage/perl/lib/perl5:$stage/source"
        printf 'exec %q %q "$@"\n' "$perl_bin" "$stage/source/$script"
    } > "$stage/launch" || return 1
    chmod 755 "$stage/launch" || return 1
    (cd "$stage/source" && env -u PERL5OPT PERL5LIB="$stage/perl/lib/perl5:$stage/source" \
        "$perl_bin" -c "$stage/source/$script") || return 1
    [[ "$tool" != hurl ]] || tool=hURL
    _macos_publish "$tool" "$stage/launch"
}

_macos_native_autotools() {
    local tool="$1" stage="$2" prefix="$2/install" source="$2/source" repo revision
    local configure_args=() make_args=() deps=(autoconf automake libtool pkg-config)
    case "$tool" in
        nbtscan)
            repo=resurrecting-open-source-projects/nbtscan
            revision=e09e22a2a322ba74bb0b3cd596933fe2e31f4b2b ;;
        outguess)
            repo=resurrecting-open-source-projects/outguess
            revision=24810e14327c2bbeedeaadd3e24491f2a4425c02
            configure_args=(--with-generic-jconfig) ;;
        scalpel)
            repo=sleuthkit/scalpel; revision=35e1367ef2232c0f4883c92ec2839273c821dd39
            deps+=(tre) ;;
        dirb)
            deps+=(curl) ;;
        *) return 1 ;;
    esac
    _macos_native_packages "${deps[@]}" || return 1
    if [[ "$tool" == dirb ]]; then
        _macos_native_download https://downloads.sourceforge.net/project/dirb/dirb/2.22/dirb222.tar.gz \
            "$stage/source.tar.gz" f3748ade231ca211a01acbec31cc6a3b576f6c56c906d73329d7dbb79f60fc2c || return 1
        mkdir -p "$source" || return 1
        tar -xzf "$stage/source.tar.gz" --strip-components=1 -C "$source" || return 1
        # Upstream DIRB's archive stores directories without search permission.
        chmod -R u+rwX "$source" || return 1
    else
        _macos_native_checkout "$repo" "$revision" "$source" || return 1
    fi
    (
        cd "$source" || exit 1
        export PATH="$(brew --prefix libtool)/libexec/gnubin:$PATH"
        if [[ "$tool" == outguess ]]; then
            local apple_ar apple_ranlib
            apple_ar=$(xcrun --find ar) && apple_ranlib=$(xcrun --find ranlib) || exit 1
            printf -v apple_ar '%q' "$apple_ar"
            printf -v apple_ranlib '%q' "$apple_ranlib"
            # The bundled JPEG makefile uses AR2, and overrides environment AR.
            make_args=("AR=$apple_ar rc" "AR2=$apple_ranlib" "RANLIB=$apple_ranlib")
        fi
        if [[ "$tool" == scalpel ]]; then
            export CPPFLAGS="-I$(brew --prefix tre)/include ${CPPFLAGS:-}"
            export LDFLAGS="-L$(brew --prefix tre)/lib ${LDFLAGS:-}"
        elif [[ "$tool" == dirb ]]; then
            export PATH="$(brew --prefix curl)/bin:$PATH"
            export CPPFLAGS="-I$(brew --prefix curl)/include ${CPPFLAGS:-}"
            export LDFLAGS="-L$(brew --prefix curl)/lib ${LDFLAGS:-}"
            # Original 2014 code relies on common global declarations.
            export CFLAGS="-fcommon ${CFLAGS:-}"
        fi
        if [[ -f autogen.sh ]]; then bash ./autogen.sh || exit 1
        elif [[ -f bootstrap ]]; then bash ./bootstrap || exit 1
        elif [[ ! -f configure ]]; then autoreconf -fi || exit 1
        fi
        bash ./configure --prefix="$prefix" ${configure_args[@]+"${configure_args[@]}"} &&
            make -j2 ${make_args[@]+"${make_args[@]}"} && make install ${make_args[@]+"${make_args[@]}"}
    ) || return 1
    [[ -x "$prefix/bin/$tool" ]] || return 1
    # Some legacy tools return 1 on their usage screen. Loading the executable
    # is checked without a target, and the actual usage banner must be present.
    local output status=0
    if [[ "$tool" == dirb || "$tool" == nbtscan ]]; then
        output=$(_macos_probe "$prefix/bin/$tool" 2>&1) || status=$?
    else
        output=$(_macos_probe "$prefix/bin/$tool" -h 2>&1) || status=$?
    fi
    [[ "$status" -le 2 && "$output" == *[Uu]sage* ]] || return 1
    _macos_publish "$tool" "$prefix/bin/$tool"
}

_macos_native_steghide() {
    local stage="$1" patch_name dep_prefix
    local patches=(patch-build-with-gcc-4.diff patch-MHashPP.diff patch-src-BmpFile.cc.diff
        patch-src-Makefile.am.diff patch-src-Makefile.in.diff patch-src-gettext.h.diff
        patch-configure.diff libtool-tag.diff)
    _macos_native_packages automake libtool libjpeg-turbo mhash gettext libiconv zlib || return 1
    # Homebrew no longer provides libmcrypt. Build the actual dependency privately;
    # libtomcrypt is a different API and cannot replace it.
    _macos_native_download \
        https://downloads.sourceforge.net/project/mcrypt/Libmcrypt/2.5.8/libmcrypt-2.5.8.tar.bz2 \
        "$stage/libmcrypt.tar.bz2" bf2f1671f44af88e66477db0982d5ecb5116a5c767b0a0d68acb34499d41b793 || return 1
    mkdir -p "$stage/libmcrypt" || return 1
    tar -xjf "$stage/libmcrypt.tar.bz2" --strip-components=1 -C "$stage/libmcrypt" || return 1
    for patch_name in Makefile.in.patch configure.patch implicit.patch tripledes.c.patch; do
        _macos_native_download \
            "https://raw.githubusercontent.com/macports/macports-ports/6e6c4e936380329061b22afd7b103993c07dd326/devel/libmcrypt/files/$patch_name" \
            "$stage/$patch_name" || return 1
        (cd "$stage/libmcrypt" && patch -p0 < "$stage/$patch_name") || return 1
    done
    local config_file config_source automake_prefix
    automake_prefix=$(brew --prefix automake) || return 1
    for config_file in config.guess config.sub; do
        config_source=$(find "$automake_prefix/share" -name "$config_file" -type f -print -quit)
        [[ -n "$config_source" ]] || return 1
        cp "$config_source" "$stage/libmcrypt/$config_file" || return 1
    done
    (
        cd "$stage/libmcrypt" || exit 1
        export CC="$(xcrun --find clang)" AR="$(xcrun --find ar)" RANLIB="$(xcrun --find ranlib)"
        bash ./configure --prefix="$stage/deps" --disable-posix-threads --enable-static --disable-shared &&
            make -j2 && make install
    ) || return 1
    [[ -f "$stage/deps/lib/libmcrypt.a" && -x "$stage/deps/bin/libmcrypt-config" ]] || return 1
    _macos_native_download https://downloads.sourceforge.net/project/steghide/steghide/0.5.1/steghide-0.5.1.tar.gz \
        "$stage/source.tar.gz" || return 1
    # Published by the official MacPorts Portfile for this unchanged upstream release.
    [[ "$(shasum -a 1 "$stage/source.tar.gz" | awk '{print $1}')" == a6d204744fabfe5751ab5e2d889ac373c0b0a30c ]] || return 1
    mkdir -p "$stage/source" || return 1
    tar -xzf "$stage/source.tar.gz" --strip-components=1 -C "$stage/source" || return 1
    for patch_name in "${patches[@]}"; do
        _macos_native_download \
            "https://raw.githubusercontent.com/macports/macports-ports/6e6c4e936380329061b22afd7b103993c07dd326/security/steghide/files/$patch_name" \
            "$stage/$patch_name" || return 1
        (cd "$stage/source" && patch -p0 < "$stage/$patch_name") || return 1
    done
    (
        cd "$stage/source" || exit 1
        export PATH="$stage/deps/bin:$(brew --prefix libtool)/libexec/gnubin:$PATH"
        CPPFLAGS="-I$stage/deps/include ${CPPFLAGS:-}"
        LDFLAGS="-L$stage/deps/lib ${LDFLAGS:-}"
        for dep_prefix in libjpeg-turbo mhash gettext libiconv zlib; do
            dep_prefix=$(brew --prefix "$dep_prefix") || exit 1
            CPPFLAGS="-I$dep_prefix/include ${CPPFLAGS:-}"
            LDFLAGS="-L$dep_prefix/lib ${LDFLAGS:-}"
        done
        export CPPFLAGS LDFLAGS
        bash ./configure --prefix="$stage/install" && make -j2 && make install
    ) || return 1
    _macos_probe "$stage/install/bin/steghide" --version || return 1
    _macos_publish steghide "$stage/install/bin/steghide"
}

_macos_native_zap() {
    local stage="$1" java_home
    _macos_native_packages openjdk@17 || return 1
    java_home="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
    [[ -x "$java_home/bin/java" ]] || return 1
    _macos_native_download \
        https://github.com/zaproxy/zaproxy/releases/download/v2.17.0/ZAP_2.17.0_Crossplatform.zip \
        "$stage/zap.zip" 94c8f767b1c2e94f0db66b3ae56514d5e3f5a728ee1b6c798e0c8fe2d61fbff0 || return 1
    unzip -q "$stage/zap.zip" -d "$stage/app" || return 1
    local zap_script
    zap_script=$(find "$stage/app" -name zap.sh -type f -print -quit)
    [[ -n "$zap_script" ]] || return 1
    _macos_probe /usr/bin/env JAVA_HOME="$java_home" bash "$zap_script" -version || return 1
    _macos_publish zaproxy /usr/bin/env JAVA_HOME="$java_home" bash "$zap_script"
}

_macos_native_gdb() {
    local stage="$1" dep dep_prefix python_prefix compiler archiver ranlib
    local configure_args=()
    _macos_native_packages pkg-config gmp mpfr ncurses python@3.14 readline xz zstd expat || return 1
    _macos_native_download https://ftp.gnu.org/gnu/gdb/gdb-17.2.tar.xz \
        "$stage/gdb.tar.xz" 1c036c0d72e4b3d1fb5c94c88632add6f9d76f4d7c4d2ea793c12a9f19a3228c || return 1
    mkdir -p "$stage/source" "$stage/build" || return 1
    tar -xJf "$stage/gdb.tar.xz" --strip-components=1 -C "$stage/source" || return 1
    python3 - "$stage/source" <<'PY' || return 1
from pathlib import Path
import sys

root = Path(sys.argv[1])
for name in ("amd64-linux-tdesc.c", "i386-linux-tdesc.c"):
    path = root / "gdb" / "arch" / name
    text = path.read_text()
    if "std::unordered_map" not in text:
        raise SystemExit("Unexpected GDB target-description source")
    # Do not rely on transitive C++ library includes, which differ on older SDKs.
    lines = text.splitlines(keepends=True)
    position = next(i for i, line in enumerate(lines) if line.startswith("#include "))
    lines.insert(position + 1, "#include <unordered_map>\n")
    path.write_text("".join(lines))
path = root / "gdb" / "darwin-nat.c"
text = path.read_text()
anchor = '#include "inferior.h"'
if text.count(anchor) != 1:
    raise SystemExit("Unexpected GDB Darwin source")
path.write_text(text.replace(anchor, anchor + '\n#include "gdbsupport/common-inferior.h"'))
PY
    python_prefix=$(brew --prefix python@3.14) || return 1
    [[ -x "$python_prefix/bin/python3.14" ]] || return 1
    [[ "$(uname -m)" != arm64 ]] || configure_args=(--target=x86_64-apple-darwin20 --program-prefix=)
    (
        cd "$stage/build" || exit 1
        compiler=$(xcrun --find clang) && archiver=$(xcrun --find ar) &&
            ranlib=$(xcrun --find ranlib) || exit 1
        export CC="$compiler" AR="$archiver" RANLIB="$ranlib"
        export CXX="$(xcrun --find clang++)"
        for dep in gmp mpfr ncurses readline xz zstd expat; do
            dep_prefix=$(brew --prefix "$dep") || exit 1
            CPPFLAGS="-I$dep_prefix/include ${CPPFLAGS:-}"
            LDFLAGS="-L$dep_prefix/lib ${LDFLAGS:-}"
            PKG_CONFIG_PATH="$dep_prefix/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
        done
        export CPPFLAGS LDFLAGS PKG_CONFIG_PATH
        bash ../source/configure --prefix="$stage/install" --enable-targets=all \
            --disable-binutils --disable-nls --disable-werror --enable-tui --with-curses \
            --with-expat --with-lzma --with-python="$python_prefix/bin/python3.14" \
            --with-system-readline --with-system-zlib --with-zstd \
            ${configure_args[@]+"${configure_args[@]}"} &&
            make -j2 && make install-gdb maybe-install-gdbserver
    ) || return 1
    _macos_probe "$stage/install/bin/gdb" --batch -nx -ex 'python import sys; print(sys.version)' || return 1
    _macos_publish gdb "$stage/install/bin/gdb" || return 1
    echo 'GDB installed; attaching to macOS processes still requires an appropriate code-signing certificate.'
}

_macos_native_tshark() (
    local stage="$1" mountpoint="$1/mount" mounted=false
    local app="$1/Wireshark.app" executable
    # The official universal bundle includes compatible libxml2 and other dylibs.
    # The 4.6.8 release supports macOS 12; do not rebuild against the old SDK.
    _macos_native_download \
        https://www.wireshark.org/download/osx/all-versions/Wireshark%204.6.8.dmg \
        "$stage/wireshark.dmg" 7de945ed1ba324259ba7e3b2ca2fe11a854cf48a33dc6d4423dd531e466a1f3a || return 1
    mkdir -p "$mountpoint" || return 1
    trap 'if [[ "$mounted" == true ]]; then
        if hdiutil detach "$mountpoint" || hdiutil detach -force "$mountpoint"; then
            rm -f "$stage/.mounted-image"
        else
            echo "Could not detach read-only image; retained staging directory: $stage" >&2
        fi
    fi' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    hdiutil attach -readonly -nobrowse -mountpoint "$mountpoint" "$stage/wireshark.dmg" || return 1
    mounted=true
    touch "$stage/.mounted-image" || return 1
    [[ -d "$mountpoint/Wireshark.app" ]] || return 1
    ditto "$mountpoint/Wireshark.app" "$app" || return 1
    hdiutil detach "$mountpoint" || hdiutil detach -force "$mountpoint" || return 1
    mounted=false
    rm -f "$stage/.mounted-image" || return 1
    codesign --verify --deep --strict "$app" || return 1
    executable="$app/Contents/MacOS/tshark"
    _macos_probe "$executable" --version || return 1
    _macos_publish tshark "$executable"
)

_macos_native_autopsy() {
    local stage="$1" java_home brew_root app_path jar_path
    local gst_root=/Library/Frameworks/GStreamer.framework/Versions/1.0
    _macos_native_packages openjdk@17 ant autoconf automake libtool pkg-config afflib libewf \
        postgresql@15 testdisk libheif || return 1
    if ! _macos_gstreamer_check "$gst_root"; then
        # Official nonrelocatable universal runtime, checked against upstream SHA256.
        # Avoid Homebrew's failing DBus build on Monterey. This PKG is not Apple-signed.
        _macos_native_download \
            https://gstreamer.freedesktop.org/data/pkg/osx/1.28.7/gstreamer-1.0-1.28.7-universal.pkg \
            "$stage/gstreamer.pkg" 529fdf4a4027d942e59b5b3564f6400adaa008f63ce5f3fed4ffe35d73911994 || return 1
        if [[ "$EUID" -eq 0 ]]; then
            /usr/sbin/installer -pkg "$stage/gstreamer.pkg" -target / || return 1
        else
            sudo /usr/sbin/installer -pkg "$stage/gstreamer.pkg" -target / || return 1
        fi
        _macos_gstreamer_check "$gst_root" || return 1
    fi
    java_home="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
    brew_root=$(brew --prefix) || return 1
    _macos_native_checkout sleuthkit/sleuthkit \
        01de0345edaa1ebf21dba6939a7c6bc7129e6e7d "$stage/sleuthkit" || return 1
    (
        cd "$stage/sleuthkit" || exit 1
        export JAVA_HOME="$java_home"
        export PATH="$java_home/bin:$(brew --prefix libtool)/libexec/gnubin:$(brew --prefix postgresql@15)/bin:$PATH"
        export CPPFLAGS="-I$brew_root/include ${CPPFLAGS:-}"
        export LDFLAGS="-L$brew_root/lib ${LDFLAGS:-}"
        bash ./bootstrap && bash ./configure --prefix="$stage/tsk" --enable-java && make -j2 && make install
    ) || return 1
    jar_path="$stage/tsk/share/java"
    [[ -f "$jar_path/sleuthkit-4.15.0.jar" ]] || return 1
    _macos_native_download \
        https://github.com/sleuthkit/autopsy/releases/download/autopsy-4.23.1/autopsy-4.23.1.zip \
        "$stage/autopsy.zip" b58cd4c04f42f49823488f05f6a5b43ada470ff7343c2d71dd2e154114d09eae || return 1
    unzip -q "$stage/autopsy.zip" -d "$stage/app" || return 1
    app_path=$(find "$stage/app" -name unix_setup.sh -type f -print -quit)
    [[ -n "$app_path" ]] || return 1
    app_path=$(dirname "$app_path")
    env TSK_JAVA_LIB_PATH="$jar_path" JAVA_HOME="$java_home" \
        PATH="$(brew --prefix testdisk)/bin:$PATH" bash "$app_path/unix_setup.sh" -j "$java_home" || return 1
    # Apply upstream JNA guidance using actual Intel/Silicon Homebrew prefixes.
    {
        printf '\nexport jreflags=%q" $jreflags"\n' "-Djna.library.path=$gst_root/lib:$stage/tsk/lib:$brew_root/lib"
        printf 'export GST_PLUGIN_SYSTEM_PATH=%q\n' "$gst_root/lib/gstreamer-1.0"
        printf 'export GST_PLUGIN_SYSTEM_PATH_1_0=%q\n' "$gst_root/lib/gstreamer-1.0"
        printf 'export GST_PLUGIN_SCANNER=%q\n' "$gst_root/libexec/gstreamer-1.0/gst-plugin-scanner"
        printf 'export GST_PLUGIN_SCANNER_1_0=%q\n' "$gst_root/libexec/gstreamer-1.0/gst-plugin-scanner"
        printf 'unset GST_PLUGIN_PATH GST_PLUGIN_PATH_1_0\n'
    } >> "$app_path/etc/autopsy.conf" || return 1
    [[ -x "$app_path/bin/autopsy" ]] || return 1
    [[ -n "$(find "$stage/tsk/lib" -name '*tsk*jni*.dylib' -type f -print -quit)" ]] || {
        echo 'Autopsy native Sleuth Kit JNI library was not installed.' >&2
        return 1
    }
    _macos_probe "$java_home/bin/java" -version || return 1
    _macos_publish autopsy /usr/bin/env JAVA_HOME="$java_home" "$app_path/bin/autopsy"
}

_macos_gstreamer_check() (
    local prefix="$1" plugin
    [[ -f "$prefix/lib/libgstreamer-1.0.dylib" &&
       -x "$prefix/libexec/gstreamer-1.0/gst-plugin-scanner" ]] || return 1
    export GST_PLUGIN_SYSTEM_PATH="$prefix/lib/gstreamer-1.0"
    export GST_PLUGIN_SYSTEM_PATH_1_0="$GST_PLUGIN_SYSTEM_PATH"
    export GST_PLUGIN_SCANNER="$prefix/libexec/gstreamer-1.0/gst-plugin-scanner"
    export GST_PLUGIN_SCANNER_1_0="$GST_PLUGIN_SCANNER"
    unset GST_PLUGIN_PATH GST_PLUGIN_PATH_1_0
    _macos_probe "$prefix/bin/gst-inspect-1.0" --version || return 1
    for plugin in playbin jpegdec avdec_h264; do
        _macos_probe "$prefix/bin/gst-inspect-1.0" "$plugin" || return 1
    done
)

_macos_native_metasploit() {
    local tool="$1" stage="$2" installed=/opt/metasploit-framework/bin
    if [[ ! -x "$installed/$tool" ]]; then
        [[ "$(uname -m)" == x86_64 ]] || {
            echo 'Official Metasploit macOS package is x86_64; no native Apple Silicon package verified.' >&2
            return 1
        }
        _macos_native_download \
            https://osx.metasploit.com/metasploit-framework-6.5.3-20260826055538-1rapid7-1.x86_64.pkg \
            "$stage/metasploit.pkg" || return 1
        # Refuse untrusted packages. No Gatekeeper or quarantine changes.
        /usr/sbin/pkgutil --check-signature "$stage/metasploit.pkg" || return 1
        if [[ "$EUID" -eq 0 ]]; then
            /usr/sbin/installer -pkg "$stage/metasploit.pkg" -target / || return 1
        else
            sudo /usr/sbin/installer -pkg "$stage/metasploit.pkg" -target / || return 1
        fi
    fi
    [[ -x "$installed/$tool" ]] || return 1
    if [[ "$tool" == msfconsole ]]; then
        _macos_probe "$installed/$tool" --version || return 1
    else
        _macos_check "$tool" "$tool" --help "$installed/$tool" || return 1
    fi
    _macos_publish "$tool" "$installed/$tool"
}

_macos_native() (
    local tool="$1" root="$HOME/.local/share/nyxstrike-tools" stage keep=false binary
    mkdir -p "$root" || return 1
    stage=$(mktemp -d "$root/${tool}.XXXXXX") || return 1
    trap '[[ "$keep" == true || -e "$stage/.mounted-image" ]] || rm -rf -- "$stage"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    case "$tool" in
        dnsenum|dotdotpwn|hurl|joomscan) _macos_native_perl "$tool" "$stage" || return 1 ;;
        dirb|nbtscan|outguess|scalpel) _macos_native_autotools "$tool" "$stage" || return 1 ;;
        steghide) _macos_native_steghide "$stage" || return 1 ;;
        gdb) _macos_native_gdb "$stage" || return 1 ;;
        tshark) _macos_native_tshark "$stage" || return 1 ;;
        zaproxy) _macos_native_zap "$stage" || return 1 ;;
        autopsy) _macos_native_autopsy "$stage" || return 1 ;;
        msfconsole|msfvenom) _macos_native_metasploit "$tool" "$stage" || return 1 ;;
        testssl)
            _macos_native_checkout testssl/testssl.sh \
                97763a411c525720a5f9bd9d2cded416b10f210a "$stage/source" || return 1
            [[ -x "$stage/source/testssl.sh" ]] || return 1
            bash -n "$stage/source/testssl.sh" || return 1
            _macos_probe "$stage/source/testssl.sh" --version || return 1
            _macos_publish testssl.sh /bin/bash "$stage/source/testssl.sh" || return 1
            ;;
        sslscan)
            _macos_native_packages openssl@3 || return 1
            _macos_native_checkout rbsec/sslscan \
                9c3fefa0a4b6b743c820e4f813ae2f8b695ab67e "$stage/source" || return 1
            local openssl_prefix
            openssl_prefix=$(brew --prefix openssl@3) || return 1
            make -C "$stage/source" -j2 CC=clang \
                CPPFLAGS="-I$openssl_prefix/include" \
                LDFLAGS="-L$openssl_prefix/lib -Wl,-rpath,$openssl_prefix/lib" || return 1
            _macos_probe "$stage/source/sslscan" --version || return 1
            _macos_publish sslscan "$stage/source/sslscan" || return 1
            ;;
        hashcat-utils)
            _macos_native_checkout hashcat/hashcat-utils 8bbf2baf7b341c8ec23ca91e44e0ac7d7fcc0355 "$stage/source" || return 1
            make -C "$stage/source" native MAINTAINER_MODE=1 -j2 || return 1
            [[ -x "$stage/source/bin/combinator.bin" ]] || return 1
            local output status=0
            output=$(_macos_probe "$stage/source/bin/cap2hccapx.bin" 2>&1) || status=$?
            # Upstream returns -1 (255) for its usage screen.
            [[ "$status" == 255 && "$output" == *usage:* ]] || return 1
            # Every published member has a persistent target even if publication
            # of a later member fails (for example a pre-existing directory).
            keep=true
            for binary in "$stage/source/bin/"*.bin; do
                _macos_publish "$(basename "$binary")" "$binary" || return 1
            done
            ;;
        hashpump)
            _macos_native_packages openssl@3 || return 1
            _macos_native_download \
                https://files.pythonhosted.org/packages/c1/21/7440b50f49b4e64a9eb66de8d6771e0eb91dfc8375f39c1e01a71570e589/hashpumpy-1.2.tar.gz \
                "$stage/source.tar.gz" e63a164027e8fe1752ae0a395671489fa3ad77366ae2b1d9972f6662dd53cb8d || return 1
            mkdir -p "$stage/source" || return 1
            tar -xzf "$stage/source.tar.gz" --strip-components=1 -C "$stage/source" || return 1
            local cpp_files=() source_file openssl_prefix
            openssl_prefix=$(brew --prefix openssl@3) || return 1
            for source_file in "$stage/source/"*.cpp; do
                [[ "$(basename "$source_file")" == hashpumpy.cpp ]] || cpp_files+=("$source_file")
            done
            c++ -std=c++11 -Wno-deprecated-declarations \
                "-I$openssl_prefix/include" "-L$openssl_prefix/lib" \
                "${cpp_files[@]}" -lcrypto -o "$stage/hashpump" || return 1
            _macos_probe "$stage/hashpump" -t || return 1
            _macos_probe "$stage/hashpump" -h || return 1
            _macos_publish hashpump "$stage/hashpump" || return 1 ;;
        libc-database)
            _macos_native_packages binutils coreutils gnu-sed gnu-tar findutils grep wget || return 1
            _macos_native_checkout niklasb/libc-database b7e948f7324cde8ac5cdb26bc4d58fbeeb1fbb5c "$stage/source" || return 1
            # Install the upstream query command; do not fetch all distribution
            # libraries during setup. Users supply their own ELF library data.
            bash -n "$stage/source/find" || return 1
            if [[ -e "$HOME/libc-database" || -L "$HOME/libc-database" ]]; then
                [[ -f "$HOME/libc-database/find" ]] || return 1
                bash -n "$HOME/libc-database/find" || return 1
                _macos_publish libc-database /bin/bash "$HOME/libc-database/find" || return 1
            else
                ln -s "$stage/source" "$HOME/libc-database" || return 1
                keep=true
                _macos_publish libc-database /bin/bash "$stage/source/find" || return 1
            fi
            ;;
        *) echo "No native source recipe for $tool" >&2; return 1 ;;
    esac
    keep=true
)

# Recheck managed commands locally before rebuilding source. No network requests,
# GUI launches, database imports, or test targets are involved in these probes.
_macos_native_check() {
    local tool="$1" root="$HOME/.local/share/nyxstrike-tools" binary="$1" output status=0
    [[ "$tool" != hurl ]] || binary=hURL
    [[ "$tool" != hashcat-utils ]] || binary=cap2hccapx.bin
    [[ "$tool" != testssl ]] || binary=testssl.sh
    binary="$root/bin/$binary"
    [[ -x "$binary" ]] || return 1
    case "$tool" in
        hashcat-utils)
            [[ -x "$root/bin/combinator.bin" && -x "$root/bin/len.bin" ]] || return 1
            output=$(_macos_probe "$binary" 2>&1) || status=$?
            [[ "$status" == 255 && "$output" == *usage:* ]] ;;
        hashpump) _macos_probe "$binary" -t ;;
        gdb) _macos_probe "$binary" --batch -nx -ex 'python import sys; print(sys.version)' ;;
        steghide|msfconsole|sslscan|testssl|tshark) _macos_probe "$binary" --version ;;
        zaproxy) _macos_probe "$binary" -version ;;
        msfvenom) _macos_check "$tool" "$tool" --help "$binary" ;;
        hurl) _macos_probe "$binary" --help ;;
        dirb|nbtscan|dotdotpwn)
            output=$(_macos_probe "$binary" 2>&1) || status=$?
            [[ "$status" -le 2 && "$output" == *[Uu]sage* ]] ;;
        dnsenum|joomscan|outguess|scalpel)
            output=$(_macos_probe "$binary" -h 2>&1) || status=$?
            [[ "$status" -le 2 && "$output" == *[Uu]sage* ]] ;;
        libc-database)
            [[ -f "$HOME/libc-database/find" ]] && bash -n "$HOME/libc-database/find" ;;
        autopsy)
            # Read our launcher as data to locate its exact installation. Never
            # source a generated wrapper or start a GUI to test availability.
            local app_executable app_dir stage java_home
            app_executable=$(python3 - "$binary" "$root" <<'PY'
import pathlib
import shlex
import sys
try:
    tokens = shlex.split(pathlib.Path(sys.argv[1]).read_text())
    root = pathlib.Path(sys.argv[2]).resolve()
    matches = [pathlib.Path(token).resolve() for token in tokens
               if token.endswith('/bin/autopsy')]
    matches = [path for path in matches if root in path.parents and path.is_file()]
    if len(matches) != 1:
        raise ValueError('Expected one managed Autopsy executable')
    print(matches[0])
except (OSError, ValueError):
    sys.exit(1)
PY
            ) || return 1
            [[ -x "$app_executable" ]] || return 1
            app_dir=$(dirname "$(dirname "$app_executable")")
            stage=$(dirname "$(dirname "$app_dir")")
            [[ -f "$app_dir/autopsy/modules/ext/sleuthkit-4.15.0.jar" &&
               -f "$app_dir/etc/autopsy.conf" &&
               -n "$(find "$stage/tsk/lib" -name '*tsk*jni*.dylib' -type f -print -quit 2>/dev/null)" ]] || return 1
            _macos_gstreamer_check /Library/Frameworks/GStreamer.framework/Versions/1.0 || return 1
            java_home="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
            _macos_probe "$java_home/bin/java" -version ;;
        *) return 1 ;;
    esac
}

_macos_catalog_contains() {
  [[ "$OS" == macos && "$MACOS_HANDLED" == *"|$1|"* ]]
}

_macos_server_python_check() {
  local name="$1" binary="$2" probe="$3" spec="$4" python=python3
  if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
    python="$VIRTUAL_ENV/bin/python"
  fi
  "$python" - "$spec" <<'PY' || return 1
import importlib.metadata
import re
import sys

distribution = re.split(r"[<>=!~;\s\[]", sys.argv[1], maxsplit=1)[0]
if not distribution:
    raise SystemExit(1)
try:
    installed = importlib.metadata.version(distribution)
except importlib.metadata.PackageNotFoundError:
    raise SystemExit(1)

try:
    from packaging.requirements import Requirement
except ModuleNotFoundError:
    # The server environment intentionally does not require packaging. All
    # current catalog constraints are simple numeric comparisons, so validate
    # those without accepting unsupported PEP 440 syntax.
    def numeric(value):
        if not re.fullmatch(r"\d+(?:\.\d+)*", value):
            raise ValueError(value)
        return tuple(int(part) for part in value.split("."))

    try:
        current = numeric(installed)
        for clause in sys.argv[1][len(distribution):].split(","):
            clause = clause.strip()
            if not clause:
                continue
            match = re.fullmatch(r"(==|!=|<=|>=|<|>)(\d+(?:\.\d+)*)", clause)
            if not match:
                raise ValueError(clause)
            operator, expected_text = match.groups()
            expected = numeric(expected_text)
            width = max(len(current), len(expected))
            left = current + (0,) * (width - len(current))
            right = expected + (0,) * (width - len(expected))
            accepted = {
                "==": left == right, "!=": left != right,
                "<=": left <= right, ">=": left >= right,
                "<": left < right, ">": left > right,
            }[operator]
            if not accepted:
                raise SystemExit(1)
    except ValueError:
        raise SystemExit(1)
else:
    requirement = Requirement(sys.argv[1])
    if installed not in requirement.specifier:
        raise SystemExit(1)
PY
  _macos_check "$name" "$binary" "$probe"
}

_install_macos_catalog() {
  local root rows name category binary method target probe interpreter reason
  root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || return 1
  rows="$(python3 - "$root/backend/server_core/tool_constants.py" <<'PY'
import runpy
import sys
catalog = runpy.run_path(sys.argv[1])['MACOS_TOOL_INSTALLATION']
for name, recipe in catalog.items():
    values = [name] + [recipe.get(key, '') for key in
              ('category', 'binary', 'method', 'target', 'probe', 'interpreter', 'reason')]
    if any('|' in value or '\n' in value for value in values):
        raise ValueError('Invalid macOS installation recipe')
    print('|'.join(values))
PY
  )" || { error "Cannot load the macOS installation catalog"; return 1; }
  section "macOS tool installation and validation"
  # Read catalog rows on a private descriptor. Package managers and build
  # scripts may read standard input; letting them inherit the here-string
  # caused the first Homebrew invocation to consume every remaining recipe.
  while IFS='|' read -r name category binary method target probe interpreter reason <&3; do
    [[ -z "$ONLY_CATEGORY" || "$category" == "$ONLY_CATEGORY" ]] || continue
    [[ "$method" != existing ]] || continue  # Existing isolated recipes run in their categories.
    MACOS_HANDLED+="$name|$binary|"
    [[ "$name" != bulk_extractor ]] || MACOS_HANDLED+="bulk-extractor|"
    if [[ "$method" == unsupported ]]; then
      skip "$name — NOT SUPPORTED ON MACOS: $reason"
      (( COUNT_SKIPPED++ )) || true
      continue
    fi
    if [[ "$DRY_RUN" == true ]]; then
      dry "$name ($method: $target; validation: $probe)"
      continue
    fi
    if [[ "$method" == native ]] && _macos_native_check "$name" >> "$LOG_FILE" 2>&1; then
      skip "$name — managed source installation verified"
      (( COUNT_ALREADY++ )) || true
      continue
    elif [[ "$method" == cask ]] && _macos_cask_check "$name" >> "$LOG_FILE" 2>&1; then
      skip "$name — application and runtime verified"
      (( COUNT_ALREADY++ )) || true
      continue
    elif [[ "$method" == server-python ]] &&
         _macos_server_python_check "$name" "$binary" "$probe" "$target" >> "$LOG_FILE" 2>&1; then
      skip "$name — server Python package and command verified"
      (( COUNT_ALREADY++ )) || true
      continue
    fi
    # Native recipes also verify resource trees; file presence alone cannot
    # validate a moved application, Java installation or deleted source checkout.
    if [[ "$method" != native && "$method" != cask && "$probe" != @file && "$method" != server-python ]] &&
        _macos_check "$name" "$binary" "$probe" >> "$LOG_FILE" 2>&1; then
      if [[ "$name" == patator ]]; then
        skip "$name — core/network modules verified; database modules are unavailable in this managed macOS runtime"
      else
        skip "$name — startup verified"
      fi
      (( COUNT_ALREADY++ )) || true
      continue
    fi
    info "Installing and validating $name ($method: $target)"
    local ok=false
    case "$method" in
      brew) _run_install_logged "$name Homebrew recipe" _macos_brew "$name" "$binary" "$target" "$probe" && ok=true ;;
      cask) _run_install_logged "$name application" _macos_cask "$name" "$target" && ok=true ;;
      go) _run_install_logged "$name Go source" _macos_go "$name" "$binary" "$target" "$probe" && ok=true ;;
      python) _run_install_logged "$name isolated Python" _macos_python_package "$name" "$binary" "$target" "${interpreter:-3.12}" && ok=true ;;
      python-source) _run_install_logged "$name Python source" _macos_python_source "$name" && ok=true ;;
      server-python) _pip_install "$target" && ok=true ;;
      gem) _run_install_logged "$name Ruby" _macos_gem "$binary" "$target" && ok=true ;;
      cargo) _run_install_logged "$name Rust source" _macos_cargo "$binary" "$target" && ok=true ;;
      native) _run_install_logged "$name native source" _macos_native "$name" && ok=true ;;
    esac
    # Source and application helpers validate their private resource trees.
    local verified=false
    if [[ "$ok" == true ]]; then
      case "$method" in
        native) _macos_check "$name" "$binary" @file >> "$LOG_FILE" 2>&1 && verified=true ;;
        cask) _macos_cask_check "$name" >> "$LOG_FILE" 2>&1 && verified=true ;;
        server-python) _macos_server_python_check "$name" "$binary" "$probe" "$target" >> "$LOG_FILE" 2>&1 && verified=true ;;
        *) _macos_check "$name" "$binary" "$probe" >> "$LOG_FILE" 2>&1 && verified=true ;;
      esac
    fi
    if [[ "$verified" == true ]]; then
      if [[ "$name" == patator ]]; then
        success "$name — core/network modules verified; database modules are unavailable in this managed macOS runtime"
      else
        success "$name — installation verified"
      fi
      (( COUNT_INSTALLED++ )) || true
    else
      reason="installation or startup check failed; see $LOG_FILE"
      error "$name — $reason"
      FAILED_TOOLS+=("$name")
      FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="$reason"
      (( COUNT_FAILED++ )) || true
    fi
  done 3<<< "$rows"
}

# ─── Master Install Function ──────────────────────────────────────────────────
# install_tool <display_name> <check_command> <method> <pkg_or_module>
#   method: pkg | pip | go | cargo | gem
install_tool() {
  local name="$1"
  local check_cmd="$2"
  local method="$3"
  local target="$4"

  if tool_exists "$check_cmd"; then
    skip "$name — already installed ($(command -v "$check_cmd"))"
    (( COUNT_ALREADY++ )) || true
    return 0
  fi

  if [[ "$DRY_RUN" == true ]]; then
    dry "$name  (via $method: $target)"
    return 0
  fi

  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}$name${RESET} via ${method} ... "

  local ok=false
  case "$method" in
    pkg)   _pkg_install "$target"    && ok=true ;;
    cask)  brew install --cask "$target" && ok=true ;;
    pip)   _pip_install "$target"    && ok=true ;;
    go)    _go_install "$target"     && ok=true ;;
    cargo) _cargo_install "$target"  && ok=true ;;
    gem)   _gem_install "$target"    && ok=true ;;
  esac

  if [[ "$ok" == true ]] && tool_exists "$check_cmd"; then
    echo -e "${GREEN}done${RESET}"
    success "$name installed successfully"
    (( COUNT_INSTALLED++ )) || true
  else
    echo -e "${RED}failed${RESET}"
    error "$name install failed (method: $method, target: $target)"
    FAILED_TOOLS+=("$name")
    (( COUNT_FAILED++ )) || true
  fi
}

# install_tool_multi — try multiple install methods in order, stop at first success
# install_tool_multi <name> <check_cmd> <"method:target" ...>
install_tool_multi() {
  local name="$1"
  local check_cmd="$2"
  shift 2
  local methods=("$@")
  local fail_hint="$FAIL_HINT"
  FAIL_HINT=""

  _macos_catalog_contains "$check_cmd" && return 0

  if tool_exists "$check_cmd"; then
    skip "$name — already installed ($(command -v "$check_cmd"))"
    (( COUNT_ALREADY++ )) || true
    return 0
  fi

  if [[ "$DRY_RUN" == true ]]; then
    local first="${methods[0]}"
    dry "$name  (preferred: ${first%%:*}: ${first#*:})"
    return 0
  fi

  echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}$name${RESET} ... "

  for entry in "${methods[@]}"; do
    local method="${entry%%:*}"
    local target="${entry#*:}"
    local ok=false

    case "$method" in
      pkg)   _pkg_install "$target"   && ok=true ;;
      cask)  _run_install_logged "Homebrew cask: $target" brew install --cask "$target" && ok=true ;;
      pip)   _pip_install "$target"   && ok=true ;;
      go)    _go_install "$target"    && ok=true ;;
      cargo) _cargo_install "$target" && ok=true ;;
      gem)   _gem_install "$target"   && ok=true ;;
      source) _install_macos_source_tool "$name" "$check_cmd" "$target" && ok=true ;;
    esac

    if [[ "$ok" == true ]] && tool_exists "$check_cmd"; then
      echo -e "${GREEN}done${RESET} (via $method)"
      success "$name installed successfully via $method"
      (( COUNT_INSTALLED++ )) || true
      return 0
    fi
  done

  # Build auto-reason from methods tried
  local tried=""
  for entry in "${methods[@]}"; do
    local m="${entry%%:*}"
    case "$m" in
      pkg)   tried+="package installation failed (see log), " ;;
      cask)  tried+="Homebrew cask failed, " ;;
      pip)   tried+="pip failed, " ;;
      go)    tried+="go build failed, " ;;
      cargo) tried+="cargo build failed, " ;;
      gem)   tried+="gem failed, " ;;
      source) tried+="isolated source installation failed (see log), " ;;
    esac
  done
  tried="${tried%, }"
  local reason="${fail_hint:-$tried}"

  echo -e "${RED}failed${RESET}"
  error "$name: $reason"
  FAILED_TOOLS+=("$name")
  FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="$reason"
  (( COUNT_FAILED++ )) || true
}

# skip_manual_install — for GUI/manual tools
skip_manual_install() {
  local name="$1"
  local url="$2"
  manual "$name — requires manual install. Download from: ${BOLD}$url${RESET}"
  MANUAL_TOOLS+=("$name  →  $url")
  (( COUNT_MANUAL++ )) || true
  log "[MANUAL] $name — $url"
}

# macOS SYN scans need BPF access, not a root-owned Nmap wrapper.
_macos_install_nmap_bpf() {
  local install_user root_command=(/usr/bin/sudo /usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash -p)
  if [[ "$(/usr/bin/id -u)" == 0 ]]; then
    install_user="${SUDO_USER:-}"
    root_command=(/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash -p)
  else
    install_user="$(/usr/bin/id -un)" || return 1
  fi
  # Validate before escalation and again inside the privileged setup.
  if [[ ! "$install_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]*$ ]] ||
      [[ "$(/usr/bin/id -u "$install_user" 2>/dev/null)" -le 0 ]]; then
    echo "Cannot identify the nonroot user who requested BPF access." >&2
    return 1
  fi
  "${root_command[@]}" -s -- "$install_user" <<'NYXSTRIKE_BPF_SETUP'
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
umask 077
install_user="$1"
[[ "$EUID" == 0 && "$install_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]*$ ]]
[[ "$(/usr/bin/id -u "$install_user")" -gt 0 ]]
base='/Library/Application Support/NyxStrike'
plist='/Library/LaunchDaemons/org.nyxstrike.bpf.plist'
helper="$base/configure-bpf"
# A same-named group created elsewhere must not inherit packet access.
group_marker='NyxStrike-managed-BPF-v1'
group_exists=false
if group_record="$(/usr/bin/dscl . -read /Groups/nyxstrike_bpf 2>/dev/null)"; then
  group_exists=true
  group_values() {
    printf '%s\n' "$group_record" | /usr/bin/awk -v attribute="$1:" '
      /^[^[:space:]]/ { active = ($1 == attribute); if (active) $1 = ""; else next }
      active { for (i = 1; i <= NF; i++) if ($i != "") print $i }
    '
  }
  [[ "$(group_values Comment)" == "$group_marker" ]] || { echo "Existing BPF group is not managed by NyxStrike." >&2; exit 1; }
  [[ -z "$(group_values NestedGroups)" ]] || { echo "Nested BPF group memberships are not allowed." >&2; exit 1; }
  user_guid="$(/usr/bin/dscl . -read "/Users/$install_user" GeneratedUID)"
  user_guid="${user_guid#GeneratedUID: }"
  [[ "$user_guid" =~ ^[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}$ ]]
  for attribute in GroupMembership GroupMembers; do
    expected="$install_user"
    [[ "$attribute" != GroupMembers ]] || expected="$user_guid"
    while IFS= read -r member; do
      [[ -z "$member" || "$member" == "$expected" ]] || { echo "BPF group includes another user; leaving access unchanged." >&2; exit 1; }
    done < <(group_values "$attribute")
  done
fi
safe_acl() {
  local listing
  listing="$(/bin/ls -lde "$1")" || return 1
  # Preserve normal deny-delete ACLs, but reject grants that allow replacement.
  printf '%s\n' "$listing" | /usr/bin/awk '
    /^[[:space:]]*[0-9]+:.* allow / && /(^|[ ,])(write|write_data|append|append_data|add_file|add_subdirectory|delete|delete_child|writeattr|writeextattr|writesecurity|chown)([ ,]|$)/ { unsafe = 1 }
    END { exit unsafe }
  '
}
secure_directory() {
  local mode
  [[ -d "$1" && ! -L "$1" && "$(/usr/bin/stat -f %u "$1")" == 0 ]] || return 1
  mode="$(/usr/bin/stat -f %Lp "$1")" || return 1
  (( (8#$mode & 022) == 0 )) || return 1
  safe_acl "$1"
}
for directory in / /Library '/Library/Application Support' /Library/LaunchDaemons; do
  secure_directory "$directory" || { echo "Unsafe BPF installation directory: $directory" >&2; exit 1; }
done
if [[ ! -e "$base" && ! -L "$base" ]]; then
  /usr/bin/install -d -o root -g wheel -m 755 "$base"
fi
secure_directory "$base" || { echo "Unsafe BPF helper directory." >&2; exit 1; }
for destination in "$helper" "$plist"; do
  if [[ -e "$destination" || -L "$destination" ]]; then
    [[ -f "$destination" && ! -L "$destination" && "$(/usr/bin/stat -f %u "$destination")" == 0 ]] || exit 1
    mode="$(/usr/bin/stat -f %Lp "$destination")"
    (( (8#$mode & 022) == 0 )) || exit 1
    safe_acl "$destination" || { echo "Unsafe BPF destination ACL." >&2; exit 1; }
  fi
done
stage="$(/usr/bin/mktemp -d "$base/.bpf-setup.XXXXXX")"
trap '/bin/rm -rf "$stage"' EXIT
/bin/cat > "$stage/configure-bpf" <<'NYXSTRIKE_BPF_HELPER'
#!/bin/bash -p
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
[[ "$EUID" == 0 ]]
# Do not compete with another packet-capture service or take its group away.
for service in /Library/LaunchDaemons/*[Cc]hmodBPF*.plist; do
  if [[ -e "$service" || -L "$service" ]]; then
    echo "Existing Wireshark BPF service detected; NyxStrike did not change device permissions." >&2
    exit 1
  fi
done
count=0
for device in /dev/bpf[0-9]*; do
  [[ "${device#/dev/bpf}" =~ ^[0-9]+$ && -c "$device" && ! -L "$device" ]] || continue
  group="$(/usr/bin/stat -f %Sg "$device")"
  case "$group" in
    wheel|nyxstrike_bpf) ;;
    *) echo "BPF device uses another group ($group); leaving permissions unchanged." >&2; exit 1 ;;
  esac
  count=$((count + 1))
done
[[ "$count" -gt 0 ]] || { echo "No BPF devices found." >&2; exit 1; }
[[ "${1:-}" != --check ]] || exit 0
for device in /dev/bpf[0-9]*; do
  [[ "${device#/dev/bpf}" =~ ^[0-9]+$ && -c "$device" && ! -L "$device" ]] || continue
  /usr/sbin/chown root:nyxstrike_bpf "$device"
  /bin/chmod 660 "$device"
done
NYXSTRIKE_BPF_HELPER
/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash -p "$stage/configure-bpf" --check
if [[ "$group_exists" == false ]]; then
  /usr/sbin/dseditgroup -o create nyxstrike_bpf
  /usr/bin/dscl . -create /Groups/nyxstrike_bpf Comment "$group_marker"
fi
/usr/sbin/dseditgroup -o edit -a "$install_user" -t user nyxstrike_bpf
/usr/bin/install -o root -g wheel -m 755 "$stage/configure-bpf" "$helper"
/bin/cat > "$stage/bpf.plist" <<'NYXSTRIKE_BPF_PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>org.nyxstrike.bpf</string>
  <key>ProgramArguments</key><array><string>/Library/Application Support/NyxStrike/configure-bpf</string></array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>60</integer>
</dict></plist>
NYXSTRIKE_BPF_PLIST
/usr/bin/plutil -lint "$stage/bpf.plist"
/usr/bin/install -o root -g wheel -m 644 "$stage/bpf.plist" "$plist"
/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash -p "$helper"
if /bin/launchctl print system/org.nyxstrike.bpf >/dev/null 2>&1; then
  /bin/launchctl bootout system/org.nyxstrike.bpf
fi
/bin/launchctl bootstrap system "$plist"
/bin/launchctl print system/org.nyxstrike.bpf >/dev/null
NYXSTRIKE_BPF_SETUP
}

_macos_setup_nmap_bpf() {
  [[ "$OS" == macos ]] || return 0
  if [[ "$DRY_RUN" == true ]]; then
    dry "Nmap BPF access for the initiating user (nyxstrike_bpf group and boot service)"
    return 0
  fi
  tool_exists nmap || return 0
  if _macos_install_nmap_bpf >> "$LOG_FILE" 2>&1; then
    success "Nmap packet access configured; sign out and back in before starting NyxStrike."
  else
    warn "Nmap is installed, but packet-access setup failed. See $LOG_FILE; SYN scans may be unavailable."
    MANUAL_TOOLS+=("Nmap packet access — resolve the permissions/service conflict reported in $LOG_FILE")
    (( COUNT_MANUAL++ )) || true
  fi
}

# ─── Category: Network / Recon ───────────────────────────────────────────────
install_network() {
  section "🔍 Network Reconnaissance & Scanning Tools"

  install_tool_multi "nmap" "nmap" \
    "pkg:nmap"
  _macos_setup_nmap_bpf

  install_tool_multi "masscan" "masscan" \
    "pkg:masscan"

  # rustscan: cargo (user-level) or brew on macOS
  if [[ "$OS" == "macos" ]]; then
    install_tool_multi "rustscan" "rustscan" \
      "pkg:rustscan" \
      "cargo:rustscan"
  else
    install_tool_multi "rustscan" "rustscan" \
      "cargo:rustscan"
  fi

  # amass: fixed go install path (v4 cmd/amass)
  install_tool_multi "amass" "amass" \
    "pkg:amass" \
    "go:github.com/owasp-amass/amass/v4/cmd/amass@latest"

  # subfinder: try apt first, then go install
  install_tool_multi "subfinder" "subfinder" \
    "pkg:subfinder" \
    "go:github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"

  if [[ "$OS" == "macos" ]]; then
    _install_verified_macos_web_tool "sublist3r" "_install_macos_sublist3r" \
      "official Git source with isolated Python 3.12" --help true
  else
    install_tool_multi "sublist3r" "sublist3r" "pip:sublist3r" "pkg:sublist3r"
  fi

  # nuclei — go install
  install_tool_multi "nuclei" "nuclei" \
    "go:github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"

  # fierce — pip (Python tool)
  install_tool_multi "fierce" "fierce" \
    "pip:fierce" \
    "pkg:fierce"

  # dnsenum — apt/brew
  install_tool_multi "dnsenum" "dnsenum" \
    "pkg:dnsenum"

  # theharvester — pip; git clone fallback
  if ! tool_exists theHarvester && ! tool_exists theharvester; then
    FAIL_HINT="pip/pkg failed; try: git clone https://github.com/laramies/theHarvester"
    install_tool_multi "theharvester" "theHarvester" \
      "pip:theHarvester" \
      "pkg:theharvester"
  else
    skip "theharvester — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # responder — Kali-only pkg; git clone fallback
  if ! tool_exists responder; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "responder (via pkg or git clone)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}responder${RESET} ... "
      local resp_ok=false
      _pkg_install responder &>/dev/null && tool_exists responder && resp_ok=true
      if [[ "$resp_ok" != true ]]; then
        if _git_install "https://github.com/lgandx/Responder.git" "$HOME/.local/share/responder"; then
          _pip_install netifaces || true
          _make_wrapper "responder" "python3 $HOME/.local/share/responder/Responder.py"
          tool_exists responder && resp_ok=true
        fi
      fi
      if [[ "$resp_ok" == true ]]; then
        echo -e "${GREEN}done${RESET}"
        success "responder installed"
        (( COUNT_INSTALLED++ )) || true
      else
        echo -e "${RED}failed${RESET}"
        error "responder: Kali-only; git clone also failed"
        FAILED_TOOLS+=("responder")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="Kali-only pkg; git clone failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "responder — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # netexec (formerly crackmapexec)
  if [[ "$OS" == "macos" ]]; then
    install_tool_multi "netexec" "nxc" \
      "source:git+https://github.com/Pennyw0rth/NetExec.git@d4cdc6c0192f735134d18bfc2c1317e9d5489525"
  else
    install_tool_multi "netexec" "nxc" "pip:netexec"
  fi

  # enum4linux — Kali-only; git clone fallback
  if ! tool_exists enum4linux; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "enum4linux (via pkg or git clone)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}enum4linux${RESET} ... "
      local e4l_ok=false
      _pkg_install enum4linux &>/dev/null && tool_exists enum4linux && e4l_ok=true
      if [[ "$e4l_ok" != true ]]; then
        if _git_install "https://github.com/CiscoCXSecurity/enum4linux.git" "$HOME/.local/share/enum4linux"; then
          chmod +x "$HOME/.local/share/enum4linux/enum4linux.pl" 2>/dev/null || true
          _make_wrapper "enum4linux" "perl $HOME/.local/share/enum4linux/enum4linux.pl"
          tool_exists enum4linux && e4l_ok=true
        fi
      fi
      if [[ "$e4l_ok" == true ]]; then
        echo -e "${GREEN}done${RESET}"
        success "enum4linux installed"
        (( COUNT_INSTALLED++ )) || true
      else
        echo -e "${RED}failed${RESET}"
        FAILED_TOOLS+=("enum4linux")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="needs samba-tools; Kali/Parrot recommended"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "enum4linux — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # enum4linux-ng
  if [[ "$OS" == "macos" ]]; then
    install_tool_multi "enum4linux-ng" "enum4linux-ng" \
      "source:git+https://github.com/cddmp/enum4linux-ng.git@288826fd9ee89b61d846e59f17b77bae4fb671ee"
  else
    install_tool_multi "enum4linux-ng" "enum4linux-ng" "pip:enum4linux-ng"
  fi

  # arp-scan
  install_tool_multi "arp-scan" "arp-scan" \
    "pkg:arp-scan"

  # nbtscan
  install_tool_multi "nbtscan" "nbtscan" \
    "pkg:nbtscan"

  # smbmap
  install_tool_multi "smbmap" "smbmap" \
    "pip:smbmap" \
    "pkg:smbmap"

  # autorecon
  install_tool_multi "autorecon" "autorecon" \
    "pip:autorecon"

  # Homebrew supplies native dependencies that BBOT's Python build needs on macOS.
  if [[ "$OS" == "macos" ]]; then
    install_tool_multi "bbot" "bbot" "pkg:bbot"
    info "BBOT on macOS is provided by Homebrew; Python extras manage it on Linux."
  fi
}

# ─── Category: Web Application Security ──────────────────────────────────────
install_web() {
  section "🌐 Web Application Security Tools"

  # gobuster — go install or brew
  install_tool_multi "gobuster" "gobuster" \
    "go:github.com/OJ/gobuster/v3@latest" \
    "pkg:gobuster"

  # ffuf — go install or brew/apt
  install_tool_multi "ffuf" "ffuf" \
    "go:github.com/ffuf/ffuf/v2@latest" \
    "pkg:ffuf"

  # feroxbuster — cargo or brew
  if [[ "$OS" == "macos" ]]; then
    install_tool_multi "feroxbuster" "feroxbuster" \
      "pkg:feroxbuster" \
      "cargo:feroxbuster"
  else
    install_tool_multi "feroxbuster" "feroxbuster" \
      "cargo:feroxbuster" \
      "pkg:feroxbuster"
  fi

  # dirsearch — pip
  install_tool_multi "dirsearch" "dirsearch" \
    "pip:dirsearch" \
    "pkg:dirsearch"

  # dirb — apt/brew
  install_tool_multi "dirb" "dirb" \
    "pkg:dirb"

  # httpx — go install
  install_tool_multi "httpx" "httpx" \
    "go:github.com/projectdiscovery/httpx/cmd/httpx@latest"

  # katana — go install
  install_tool_multi "katana" "katana" \
    "go:github.com/projectdiscovery/katana/cmd/katana@latest"

  # hakrawler — go install
  install_tool_multi "hakrawler" "hakrawler" \
    "go:github.com/hakluke/hakrawler@latest"

  # gau (Get All URLs) — go install
  install_tool_multi "gau" "gau" \
    "go:github.com/lc/gau/v2/cmd/gau@latest"

  # waybackurls — go install
  install_tool_multi "waybackurls" "waybackurls" \
    "go:github.com/tomnomnom/waybackurls@latest"

  # nikto — apt/brew
  install_tool_multi "nikto" "nikto" \
    "pkg:nikto"

  # sqlmap — pip or apt
  install_tool_multi "sqlmap" "sqlmap" \
    "pip:sqlmap" \
    "pkg:sqlmap"

  if [[ "$OS" == "macos" ]]; then
    _install_verified_macos_web_tool "wpscan" "_install_macos_wpscan" \
      "official wpscanteam/tap/wpscan Homebrew formula" --version true
  else
    install_tool_multi "wpscan" "wpscan" "gem:wpscan" "pkg:wpscan"
  fi

  # arjun — pip
  install_tool_multi "arjun" "arjun" \
    "pip:arjun"

  # paramspider — not on PyPI; git clone
  if ! tool_exists paramspider; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "paramspider (via git clone)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}paramspider${RESET} via git clone ... "
      if _git_install "https://github.com/devanshbatham/ParamSpider.git" "$HOME/.local/share/paramspider"; then
        _pip_install "$HOME/.local/share/paramspider" || true
        if tool_exists paramspider; then
          echo -e "${GREEN}done${RESET}"
          success "paramspider installed via git clone"
          (( COUNT_INSTALLED++ )) || true
        else
          _make_wrapper "paramspider" "python3 -m paramspider"
          echo -e "${GREEN}done${RESET}"
          success "paramspider installed via git clone"
          (( COUNT_INSTALLED++ )) || true
        fi
      else
        echo -e "${RED}failed${RESET}"
        FAILED_TOOLS+=("paramspider")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="git clone failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "paramspider — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # dalfox — go install
  install_tool_multi "dalfox" "dalfox" \
    "go:github.com/hahwul/dalfox/v2@latest"

  if [[ "$OS" == "macos" ]]; then
    _install_verified_macos_web_tool "wafw00f" "_install_macos_wafw00f" \
      "official Git source with isolated Python 3.12" --help true
  else
    install_tool_multi "wafw00f" "wafw00f" "pip:wafw00f"
  fi

  if [[ "$OS" == "macos" ]]; then
    _install_verified_macos_web_tool "whatweb" "_install_macos_whatweb" \
      "official WhatWeb v0.6.4 with isolated Homebrew Ruby gems"
    _install_verified_macos_web_tool "wfuzz" "_install_macos_wfuzz" \
      "official Wfuzz source with isolated Python 3.11 and binary PycURL"
  else
    install_tool_multi "whatweb" "whatweb" \
      "pkg:whatweb" \
      "gem:whatweb"
    install_tool_multi "wfuzz" "wfuzz" \
      "pip:wfuzz" \
      "pkg:wfuzz"
  fi

  # commix — git clone (not reliably on PyPI)
  if ! tool_exists commix; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "commix (via pkg or git clone)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}commix${RESET} ... "
      local cmx_ok=false
      _pkg_install commix &>/dev/null && tool_exists commix && cmx_ok=true
      if [[ "$cmx_ok" != true ]]; then
        if _git_install "https://github.com/commixproject/commix.git" "$HOME/.local/share/commix"; then
          _make_wrapper "commix" "python3 $HOME/.local/share/commix/commix.py"
          tool_exists commix && cmx_ok=true
        fi
      fi
      if [[ "$cmx_ok" == true ]]; then
        echo -e "${GREEN}done${RESET}"
        success "commix installed"
        (( COUNT_INSTALLED++ )) || true
      else
        echo -e "${RED}failed${RESET}"
        FAILED_TOOLS+=("commix")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="git clone failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "commix — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # testssl.sh — git clone (not in Ubuntu repos). On macOS the catalog owns the
  # pinned, validated source recipe, so this legacy fallback must not run twice.
  if ! _macos_catalog_contains testssl && ! tool_exists testssl.sh && ! tool_exists testssl; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "testssl.sh (via git clone)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}testssl.sh${RESET} via git clone ... "
      if _git_install "https://github.com/drwetter/testssl.sh.git" "$HOME/.local/share/testssl.sh"; then
        ln -sf "$HOME/.local/share/testssl.sh/testssl.sh" "$HOME/.local/bin/testssl.sh"
        chmod +x "$HOME/.local/bin/testssl.sh"
        echo -e "${GREEN}done${RESET}"
        success "testssl.sh installed via git clone"
        (( COUNT_INSTALLED++ )) || true
      else
        echo -e "${RED}failed${RESET}"
        FAILED_TOOLS+=("testssl")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="git clone failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  elif ! _macos_catalog_contains testssl; then
    skip "testssl.sh — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # sslscan
  install_tool_multi "sslscan" "sslscan" \
    "pkg:sslscan"

  # sslyze
  install_tool_multi "sslyze" "sslyze" \
    "pip:sslyze"
}

# ─── Category: Authentication & Password ─────────────────────────────────────
install_auth() {
  section "🔐 Authentication & Password Security Tools"

  # hydra
  install_tool_multi "hydra" "hydra" \
    "pkg:hydra"

  # john the ripper
  install_tool_multi "john" "john" \
    "pkg:john"

  # hashcat
  install_tool_multi "hashcat" "hashcat" \
    "pkg:hashcat"

  # medusa
  install_tool_multi "medusa" "medusa" \
    "pkg:medusa"

  # patator
  install_tool_multi "patator" "patator" \
    "pip:patator"

  # evil-winrm
  install_tool_multi "evil-winrm" "evil-winrm" \
    "gem:evil-winrm"

  # hashid (replaces legacy hash-identifier)
  install_tool_multi "hashid" "hashid" \
    "pip:hashid" \
    "pkg:hashid"
}

# ─── Category: Binary Analysis & Reverse Engineering ─────────────────────────
install_binary() {
  section "🔬 Binary Analysis & Reverse Engineering Tools"

  if [[ "$OS" != "macos" ]]; then
    install_tool_multi "gdb" "gdb" "pkg:gdb"
  fi

  # radare2
  install_tool_multi "radare2" "radare2" \
    "pkg:radare2"

  # binwalk — try pkg first, pip fallback
  install_tool_multi "binwalk" "binwalk" \
    "pkg:binwalk" \
    "pip:binwalk"

  # ropgadget
  install_tool_multi "ropgadget" "ROPgadget" \
    "pip:ROPGadget"

  # ropper — pip
  install_tool_multi "ropper" "ropper" \
    "pip:ropper"

  # checksec — pip or apt
  install_tool_multi "checksec" "checksec" \
    "pip:checksec" \
    "pkg:checksec"

  # binutils (strings, objdump, readelf, xxd)
  if ! command -v readelf &>/dev/null; then
    install_tool_multi "binutils (strings/objdump/readelf)" "readelf" \
      "pkg:binutils"
  else
    skip "binutils (strings/objdump/readelf) — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # exiftool
  install_tool_multi "exiftool" "exiftool" \
    "pkg:libimage-exiftool-perl" \
    "pkg:exiftool"

  # volatility3 — pip
  install_tool_multi "volatility3" "vol" \
    "pip:volatility3"

  # foremost — apt/brew
  install_tool_multi "foremost" "foremost" \
    "pkg:foremost"

  # steghide — apt/brew
  install_tool_multi "steghide" "steghide" \
    "pkg:steghide"

  # one-gadget — gem
  install_tool_multi "one-gadget" "one_gadget" \
    "gem:one_gadget"

  # upx — apt/brew
  install_tool_multi "upx" "upx" \
    "pkg:upx"

  # pwntools and angr: note they are in the pyproject.toml "tools" extra
  info "pwntools & angr — managed via pyproject.toml (uv sync --extra tools)"

  # GUI / manual-only tools
  [[ "$OS" == macos ]] || skip_manual_install "Ghidra" "https://ghidra-sre.org/"
  skip_manual_install "IDA Free"     "https://hex-rays.com/ida-free/"
  skip_manual_install "Binary Ninja" "https://binary.ninja/free/"
}

# ─── Category: Cloud & Container Security ────────────────────────────────────
install_cloud() {
  section "☁️  Cloud & Container Security Tools"

  # trivy — brew or apt (Aqua Security repo on Linux)
  if [[ "$OS" == "macos" ]]; then
    install_tool_multi "trivy" "trivy" \
      "pkg:trivy"
  elif [[ "$PKG_MGR" == "apt" ]]; then
    if ! tool_exists trivy; then
      if [[ "$DRY_RUN" != true ]]; then
        info "Adding Aqua Security apt repo for trivy..."
        $SUDO apt-get install -y apt-transport-https &>/dev/null
        # Use curl (already bootstrapped) instead of wget; read codename from /etc/os-release
        local trivy_codename
        trivy_codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-${UBUNTU_CODENAME:-focal}}")"
        curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key \
          | $SUDO gpg --dearmor -o /usr/share/keyrings/trivy.gpg &>/dev/null
        echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb ${trivy_codename} main" \
          | $SUDO tee /etc/apt/sources.list.d/trivy.list &>/dev/null
        $SUDO apt-get update -qq &>/dev/null
        _pkg_install "trivy"
        if tool_exists trivy; then
          success "trivy installed via apt"
          (( COUNT_INSTALLED++ )) || true
        else
          error "trivy apt install failed"
          FAILED_TOOLS+=("trivy")
          (( COUNT_FAILED++ )) || true
        fi
      else
        dry "trivy (via Aqua Security apt repo)"
      fi
    else
      skip "trivy — already installed"
      (( COUNT_ALREADY++ )) || true
    fi
  else
    install_tool_multi "trivy" "trivy" \
      "pkg:trivy"
  fi

  # kube-hunter — deprecated; use kube-bench instead
  if [[ "$OS" == macos ]]; then
    : # The catalog installs the portable Python CLI.
  elif ! tool_exists kube-hunter; then
    info "kube-hunter — deprecated upstream; use kube-bench instead"
  else
    skip "kube-hunter — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # kube-bench — download binary
  if [[ "$OS" == "macos" ]]; then
    : # Native formula is handled by the catalog; audits still target a node.
  elif ! tool_exists kube-bench; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "kube-bench (via GitHub release binary → ~/.local/bin)"
    else
      info "Downloading kube-bench binary to ~/.local/bin ..."
      mkdir -p "$HOME/.local/bin"
      local kb_arch
      kb_arch=$(uname -m); [[ "$kb_arch" == "x86_64" ]] && kb_arch="amd64" || kb_arch="arm64"
      local kb_ver
      kb_ver=$(curl -sL https://api.github.com/repos/aquasecurity/kube-bench/releases/latest \
               | grep '"tag_name"' | sed 's/.*"v\([^"]*\)".*/\1/')
      local kb_url="https://github.com/aquasecurity/kube-bench/releases/download/v${kb_ver}/kube-bench_${kb_ver}_linux_${kb_arch}.tar.gz"
      if curl -sL "$kb_url" | tar -xz -C "$HOME/.local/bin" kube-bench 2>/dev/null; then
        chmod +x "$HOME/.local/bin/kube-bench"
        success "kube-bench v${kb_ver} installed to ~/.local/bin"
        (( COUNT_INSTALLED++ )) || true
      else
        error "kube-bench download failed"
        FAILED_TOOLS+=("kube-bench")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="binary download failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "kube-bench — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # checkov
  FAIL_HINT="pip install requires many deps; try: pip3 install checkov"
  install_tool_multi "checkov" "checkov" \
    "pip:checkov"

  # aws-cli
  install_tool_multi "aws-cli" "aws" \
    "pip:awscli" \
    "pkg:awscli"

  # kubectl — direct binary download
  if ! tool_exists kubectl; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "kubectl (via pkg or binary download)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}kubectl${RESET} ... "
      local kc_ok=false
      _pkg_install kubectl &>/dev/null && tool_exists kubectl && kc_ok=true
      if [[ "$kc_ok" != true ]]; then
        local kc_arch
        kc_arch=$(uname -m); [[ "$kc_arch" == "x86_64" ]] && kc_arch="amd64" || kc_arch="arm64"
        local kc_os; kc_os=$(uname -s | tr '[:upper:]' '[:lower:]')
        local kc_ver
        kc_ver=$(curl -sL https://dl.k8s.io/release/stable.txt 2>/dev/null)
        if [[ -n "$kc_ver" ]]; then
          mkdir -p "$HOME/.local/bin"
          if curl -sL "https://dl.k8s.io/release/${kc_ver}/bin/${kc_os}/${kc_arch}/kubectl" -o "$HOME/.local/bin/kubectl" 2>/dev/null; then
            chmod +x "$HOME/.local/bin/kubectl"
            tool_exists kubectl && kc_ok=true
          fi
        fi
      fi
      if [[ "$kc_ok" == true ]]; then
        echo -e "${GREEN}done${RESET}"
        success "kubectl installed"
        (( COUNT_INSTALLED++ )) || true
      else
        echo -e "${RED}failed${RESET}"
        FAILED_TOOLS+=("kubectl")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="binary download failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "kubectl — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # helm — official install script
  if ! tool_exists helm; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "helm (via pkg or install script)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}helm${RESET} ... "
      local helm_ok=false
      _pkg_install helm &>/dev/null && tool_exists helm && helm_ok=true
      if [[ "$helm_ok" != true ]]; then
        if curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | HELM_INSTALL_DIR="$HOME/.local/bin" USE_SUDO=false bash &>/dev/null; then
          tool_exists helm && helm_ok=true
        fi
      fi
      if [[ "$helm_ok" == true ]]; then
        echo -e "${GREEN}done${RESET}"
        success "helm installed"
        (( COUNT_INSTALLED++ )) || true
      else
        echo -e "${RED}failed${RESET}"
        FAILED_TOOLS+=("helm")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="install script failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "helm — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # docker-bench-security note (scripts, not a binary)
  if [[ "$OS" == "macos" ]]; then
    : # The catalog reports the Linux host requirement once.
  elif ! tool_exists docker-bench-security; then
    info "docker-bench-security — clone from: https://github.com/docker/docker-bench-security"
    info "  Run with: sudo sh docker-bench-security.sh"
  fi
}

# ─── Category: CTF & Forensics ───────────────────────────────────────────────
install_ctf() {
  section "🏆 CTF & Digital Forensics Tools"

  # volatility3 — pip
  install_tool_multi "volatility3" "vol" \
    "pip:volatility3"

  # foremost
  install_tool_multi "foremost" "foremost" \
    "pkg:foremost"

  # steghide
  install_tool_multi "steghide" "steghide" \
    "pkg:steghide"

  # zsteg — gem
  install_tool_multi "zsteg" "zsteg" \
    "gem:zsteg"

  # outguess
  install_tool_multi "outguess" "outguess" \
    "pkg:outguess"

  # exiftool
  install_tool_multi "exiftool" "exiftool" \
    "pkg:libimage-exiftool-perl" \
    "pkg:exiftool"

  # testdisk / photorec
  install_tool_multi "testdisk/photorec" "testdisk" \
    "pkg:testdisk"

  # scalpel
  install_tool_multi "scalpel" "scalpel" \
    "pkg:scalpel"

  # bulk-extractor
  FAIL_HINT="package install failed; inspect the log or build github.com/simsong/bulk_extractor"
  install_tool_multi "bulk-extractor" "bulk_extractor" \
    "pkg:bulk-extractor"

  # autopsy note (GUI)
  [[ "$OS" == macos ]] || skip_manual_install "Autopsy (GUI)" "https://www.autopsy.com/download/"

  # sleuthkit
  install_tool_multi "sleuthkit" "fls" \
    "pkg:sleuthkit"

  # john (often needed in CTF)
  install_tool_multi "john" "john" \
    "pkg:john"

  # hashcat
  install_tool_multi "hashcat" "hashcat" \
    "pkg:hashcat"

  # binwalk
  install_tool_multi "binwalk" "binwalk" \
    "pip:binwalk" \
    "pkg:binwalk"

  # pwntools — managed by pyproject.toml "tools" extra
  info "pwntools — managed via pyproject.toml (uv sync --extra tools)"

  # stegsolve note (Java GUI jar)
  if ! tool_exists stegsolve; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "stegsolve (~/.local/bin/stegsolve)"
    else
      mkdir -p "$HOME/.local/bin"
      if curl -sL "https://github.com/eugenekolo/sec-tools/raw/master/stego/stegsolve/stegsolve/stegsolve.jar" \
          -o "$HOME/.local/bin/stegsolve.jar" 2>/dev/null; then
        # Create a wrapper script
        cat > "$HOME/.local/bin/stegsolve" <<'WRAPPER'
#!/usr/bin/env sh
java -jar "$HOME/.local/bin/stegsolve.jar" "$@"
WRAPPER
        chmod +x "$HOME/.local/bin/stegsolve"
        success "stegsolve jar installed to ~/.local/bin"
        (( COUNT_INSTALLED++ )) || true
      else
        error "stegsolve download failed — requires a JRE and manual download"
        FAILED_TOOLS+=("stegsolve")
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "stegsolve — already installed"
    (( COUNT_ALREADY++ )) || true
  fi
}

# ─── Category: OSINT ─────────────────────────────────────────────────────────
install_osint() {
  section "🕵️  OSINT & Intelligence Gathering Tools"

  # sherlock
  install_tool_multi "sherlock" "sherlock" \
    "pip:sherlock-project"

  # recon-ng — git clone (complex app, not a simple pip package)
  if ! tool_exists recon-ng; then
    if [[ "$DRY_RUN" == true ]]; then
      dry "recon-ng (via git clone)"
    else
      echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}recon-ng${RESET} via git clone ... "
      if _git_install "https://github.com/lanmaster53/recon-ng.git" "$HOME/.local/share/recon-ng"; then
        _pip_install -r "$HOME/.local/share/recon-ng/REQUIREMENTS" || true
        _make_wrapper "recon-ng" "python3 $HOME/.local/share/recon-ng/recon-ng"
        echo -e "${GREEN}done${RESET}"
        success "recon-ng installed via git clone"
        (( COUNT_INSTALLED++ )) || true
      else
        echo -e "${RED}failed${RESET}"
        FAILED_TOOLS+=("recon-ng")
        FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="git clone failed"
        (( COUNT_FAILED++ )) || true
      fi
    fi
  else
    skip "recon-ng — already installed"
    (( COUNT_ALREADY++ )) || true
  fi

  # spiderfoot
  FAIL_HINT="complex web app; clone github.com/smicallef/spiderfoot"
  install_tool_multi "spiderfoot" "spiderfoot" \
    "pip:spiderfoot"

  # theharvester (may already be installed from network category)
  install_tool_multi "theharvester" "theHarvester" \
    "pip:theHarvester" \
    "pkg:theharvester"

  # social-analyzer
  install_tool_multi "social-analyzer" "social-analyzer" \
    "pip:social-analyzer"

  # Maltego — GUI, skip
  [[ "$OS" == macos ]] || skip_manual_install "Maltego (GUI)" "https://www.maltego.com/downloads/"

  # Shodan CLI — needs API key
  info "shodan CLI — install with: pip3 install --user shodan  (requires API key at https://account.shodan.io/)"

  # Censys — needs API key
  info "censys CLI — install with: pip3 install --user censys  (requires API key at https://censys.io/)"
}

# Verify Selenium's bundled manager without resolving or downloading a driver.
_macos_selenium_manager_check() {
  local root python
  root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || return 1
  python="${VIRTUAL_ENV:-$root/nyxstrike-env}/bin/python"
  [[ -x "$python" ]] || return 1
  "$python" - <<'PY'
import os
import subprocess

from selenium.webdriver.common.selenium_manager import SeleniumManager

binary = SeleniumManager._get_binary()
if not binary.is_file() or not os.access(binary, os.X_OK):
    raise SystemExit(1)
subprocess.run(
    [str(binary), "--version"],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    timeout=15,
)
PY
}

# ─── Category: Browser Agent ─────────────────────────────────────────────────
_macos_browser_installed() {
  tool_exists chromium || tool_exists google-chrome ||
    [[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ||
       -x "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ||
       -x "/Applications/Chromium.app/Contents/MacOS/Chromium" ||
       -x "$HOME/Applications/Chromium.app/Contents/MacOS/Chromium" ]]
}

install_browser() {
  section "🌍 Browser Agent Dependencies (Chromium + ChromeDriver)"

  if [[ "$OS" == "macos" ]]; then
    # macOS: brew --cask
    if ! _macos_browser_installed; then
      if [[ "$DRY_RUN" == true ]]; then
        dry "Google Chrome (brew install --cask google-chrome)"
      else
        echo -ne "  ${CYAN}↳${RESET} Installing ${BOLD}Google Chrome${RESET} via brew cask ... "
        if brew install --cask google-chrome &>/dev/null; then
          echo -e "${GREEN}done${RESET}"
          success "Google Chrome installed"
          (( COUNT_INSTALLED++ )) || true
        else
          echo -e "${RED}failed${RESET}"
          error "Google Chrome cask install failed"
          FAILED_TOOLS+=("google-chrome")
          FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="Homebrew cask installation failed"
          (( COUNT_FAILED++ )) || true
        fi
      fi
    else
      skip "chromium/chrome — already installed"
      (( COUNT_ALREADY++ )) || true
    fi

    # Selenium 4 resolves the matching signed driver when a browser session
    # starts. Homebrew disabled its chromedriver cask for failing Gatekeeper.
    if [[ "$DRY_RUN" == true ]]; then
      dry "chromedriver (managed automatically by Selenium Manager)"
    elif _macos_selenium_manager_check >> "$LOG_FILE" 2>&1; then
      skip "chromedriver — Selenium Manager runtime verified"
      (( COUNT_ALREADY++ )) || true
    else
      error "chromedriver — Selenium Manager is missing or incompatible"
      FAILED_TOOLS+=("chromedriver")
      FAILED_REASONS[${#FAILED_TOOLS[@]}-1]="Selenium Manager runtime check failed"
      (( COUNT_FAILED++ )) || true
    fi

  else
    # Linux
    if ! tool_exists chromium-browser && ! tool_exists chromium && ! tool_exists google-chrome; then
      install_tool_multi "chromium-browser" "chromium-browser" \
        "pkg:chromium-browser" \
        "pkg:chromium"
    else
      skip "chromium/chrome — already installed"
      (( COUNT_ALREADY++ )) || true
    fi

    install_tool_multi "chromium-chromedriver" "chromedriver" \
      "pkg:chromium-chromedriver" \
      "pkg:chromium-driver"
  fi
}

# ─── Summary ──────────────────────────────────────────────────────────────────
print_summary() {
  echo ""
  echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${BOLD}  📊 Installation Summary${RESET}"
  echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
  echo -e "  ${GREEN}✔  Installed:         $COUNT_INSTALLED${RESET}"
  echo -e "  ${DIM}~  Already present:   $COUNT_ALREADY${RESET}"
  echo -e "  ${DIM}~  Not applicable:    $COUNT_SKIPPED${RESET}"
  echo -e "  ${MAGENTA}⊕  Manual required:   $COUNT_MANUAL${RESET}"
  echo -e "  ${RED}✘  Failed:            $COUNT_FAILED${RESET}"
  echo ""

  if [[ ${#MANUAL_TOOLS[@]} -gt 0 ]]; then
    echo -e "  ${MAGENTA}${BOLD}Manual Install Required:${RESET}"
    for t in "${MANUAL_TOOLS[@]}"; do
      echo -e "    ${MAGENTA}⊕${RESET} $t"
    done
    echo ""
  fi

  if [[ ${#FAILED_TOOLS[@]} -gt 0 ]]; then
    echo -e "  ${RED}${BOLD}Failed Tools:${RESET}"
    local i
    for i in "${!FAILED_TOOLS[@]}"; do
      local t="${FAILED_TOOLS[$i]}"
      local reason="${FAILED_REASONS[$i]:-unknown}"
      printf "    ${RED}✘${RESET} %-20s ${DIM}— %s${RESET}\n" "$t" "$reason"
    done
    echo ""
  fi

  if [[ "$SHOW_LOG" == true ]]; then
    echo -e "  ${DIM}Full log: $LOG_FILE${RESET}"
    echo ""
    echo -e "  ${CYAN}${BOLD}── Install Log ──${RESET}"
    cat "$LOG_FILE" 2>/dev/null || true
    echo ""
  fi

  echo -e "  ${DIM}Installation log: $LOG_FILE${RESET}"
  echo ""
  echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

# ─── Argument Parsing ─────────────────────────────────────────────────────────
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --show-log)
        SHOW_LOG=true
        shift
        ;;
      --only)
        if [[ -z "${2:-}" ]]; then
          error "--only requires a category name"
          echo "Valid categories: network, web, auth, binary, cloud, ctf, osint, browser"
          exit 1
        fi
        ONLY_CATEGORY="$2"
        shift 2
        ;;
      --list)
        print_list
        exit 0
        ;;
      --help|-h)
        print_help
        exit 0
        ;;
      *)
        error "Unknown argument: $1"
        echo "Run with --help for usage."
        exit 1
        ;;
    esac
  done

  # Validate --only value
  if [[ -n "$ONLY_CATEGORY" ]]; then
    case "$ONLY_CATEGORY" in
      network|web|auth|binary|cloud|ctf|osint|browser) ;;
      *)
        error "Unknown category: '$ONLY_CATEGORY'"
        echo "Valid categories: network, web, auth, binary, cloud, ctf, osint, browser"
        exit 1
        ;;
    esac
  fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────
main() {
  parse_args "$@"

  if [[ "$DRY_RUN" == true ]]; then
    echo -e "  ${BLUE}${BOLD}DRY-RUN MODE — no packages will be installed${RESET}"
    echo ""
  fi

  # Initialize log
  echo "# nyxstrike Tool Installer — $(date)" > "$LOG_FILE"
  log "DRY_RUN=$DRY_RUN ONLY_CATEGORY=${ONLY_CATEGORY:-all}"

  detect_os

  # Bootstrap curl + ca-certs BEFORE prerequisites so Go/Rust/Trivy downloaders can run
  if [[ "$DRY_RUN" != true ]]; then
    bootstrap_essentials
  fi

  check_prerequisites

  # Add Go/pip/gem/cargo bin dirs to PATH (critical: must run before tool installs)
  if [[ "$DRY_RUN" != true ]]; then
    setup_paths
  fi

  if [[ "$DRY_RUN" != true ]]; then
    check_paths
  fi

  # Refresh package lists once (Linux only, non-dry-run)
  if [[ "$DRY_RUN" != true && "$PKG_MGR" == "apt" ]]; then
    section "Updating Package Lists"
    echo -ne "  ${CYAN}↳${RESET} Running apt-get update ... "
    if $SUDO apt-get update -qq 2>/dev/null; then
      echo -e "${GREEN}done${RESET}"
    else
      echo -e "${YELLOW}skipped${RESET}"
      warn "apt-get update failed — some installs may fail"
    fi
  elif [[ "$DRY_RUN" != true && "$PKG_MGR" == "brew" ]]; then
    section "Updating Homebrew"
    echo -ne "  ${CYAN}↳${RESET} Running brew update ... "
    if brew update --quiet 2>/dev/null; then
      echo -e "${GREEN}done${RESET}"
    else
      echo -e "${YELLOW}skipped${RESET}"
    fi
  fi

  if [[ "$OS" == macos ]]; then
    _install_macos_catalog || return 1
  fi

  # Run selected categories
  if [[ -n "$ONLY_CATEGORY" ]]; then
    case "$ONLY_CATEGORY" in
      network) install_network ;;
      web)     install_web     ;;
      auth)    install_auth    ;;
      binary)  install_binary  ;;
      cloud)   install_cloud   ;;
      ctf)     install_ctf     ;;
      osint)   install_osint   ;;
      browser) install_browser ;;
    esac
  else
    install_network
    install_web
    install_auth
    install_binary
    install_cloud
    install_ctf
    install_osint
    install_browser
  fi

  print_summary
  [[ "$COUNT_FAILED" -eq 0 ]]
}

main "$@"
