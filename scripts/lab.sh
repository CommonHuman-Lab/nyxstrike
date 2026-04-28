#!/usr/bin/env bash
# =============================================================================
# NyxStrike Lab Manager
# Spin up / tear down vulnerable security lab environments via Docker
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABS_DIR="${SCRIPT_DIR}/labs"

# ---------------- colours / output helpers -----------------------------------
RED='\033[0;31m'
GREEN='\033[38;5;46m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
BOLD='\033[1m'
RESET='\033[0m'

good()  { echo -e "\t${GREEN}[+]${RESET} $*"; }
bad()   { echo -e "\t${RED}[-]${RESET} $*"; }
info()  { echo -e "\t${GRAY}[*]${RESET} $*"; }
warn()  { echo -e "\t${YELLOW}[!]${RESET} $*"; }
header(){ echo -e "\n${GREEN}${BOLD}$*${RESET}"; }

# ---------------- lab registry -----------------------------------------------
# Format: "ID|NAME|SCRIPT|DESCRIPTION"
LABS=(
  "1|Juice Shop|juiceshop.sh|OWASP Juice Shop - OWASP Top 10 web vulnerabilities"
  "2|DVWA|dvwa.sh|Damn Vulnerable Web App - PHP/MySQL classic"
  "3|Metasploitable2|metasploitable.sh|Linux VM with intentionally vulnerable services"
  "4|WebGoat|webgoat.sh|OWASP WebGoat - PortSwigger-style lesson-based labs"
  "5|HTB Style|htb_style.sh|HackTheBox-style CTFd platform + vulnerable challenge"
  "6|Kioptrix|kioptrix.sh|VulnHub Kioptrix Level 1 - classic beginner boot2root"
  "7|VulnAD|vulnad.sh|Vulnerable Active Directory - Samba4 AD with AD attack paths"
)

# ---------------- dependency checks ------------------------------------------
check_docker() {
  if ! command -v docker &>/dev/null; then
    bad "Docker is not installed. Install it from https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker info &>/dev/null 2>&1; then
    bad "Docker daemon is not running. Start it and try again."
    exit 1
  fi
  good "Docker is running"
}

# ---------------- banner ------------------------------------------------------
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
  echo -e "  ${BOLD}Security Lab Manager${RESET} — Docker-based vulnerable environment launcher"
  echo ""
}

# ---------------- list labs ---------------------------------------------------
list_labs() {
  header "Available Labs"
  echo ""
  printf "  ${BOLD}%-4s %-20s %s${RESET}\n" "ID" "NAME" "DESCRIPTION"
  echo "  ─────────────────────────────────────────────────────────────────────"
  for entry in "${LABS[@]}"; do
    IFS='|' read -r id name _script desc <<< "$entry"
    printf "  ${GREEN}%-4s${RESET} ${BOLD}%-20s${RESET} ${GRAY}%s${RESET}\n" "$id" "$name" "$desc"
  done
  echo ""
}

# ---------------- status of all running labs ----------------------------------
status_all() {
  header "Running Lab Containers"
  echo ""
  local running
  running=$(docker ps --filter "name=nyxstrike-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true)
  if [[ -z "$running" ]] || [[ "$running" == *"NAMES"$'\n' ]]; then
    info "No NyxStrike lab containers are currently running."
  else
    echo "$running" | sed 's/^/  /'
  fi
  echo ""
}

# ---------------- dispatch to a lab script ------------------------------------
dispatch() {
  local action="$1"
  local id="$2"

  local matched=""
  for entry in "${LABS[@]}"; do
    IFS='|' read -r lid _name lscript _desc <<< "$entry"
    if [[ "$lid" == "$id" ]]; then
      matched="$lscript"
      break
    fi
  done

  if [[ -z "$matched" ]]; then
    bad "Unknown lab ID: $id"
    echo ""
    list_labs
    exit 1
  fi

  local script_path="${LABS_DIR}/${matched}"
  if [[ ! -f "$script_path" ]]; then
    bad "Lab script not found: $script_path"
    exit 1
  fi

  bash "$script_path" "$action"
}

# ---------------- start all / stop all ----------------------------------------
all_action() {
  local action="$1"
  for entry in "${LABS[@]}"; do
    IFS='|' read -r id name lscript _desc <<< "$entry"
    header "${action^}: $name"
    bash "${LABS_DIR}/${lscript}" "$action" || warn "Failed to $action $name (continuing)"
  done
}

# ---------------- interactive menu --------------------------------------------
interactive_menu() {
  list_labs
  echo -e "  ${BOLD}Commands:${RESET}"
  echo -e "  ${GREEN}start <id>${RESET}   — Start a lab by ID (e.g. start 1)"
  echo -e "  ${GREEN}stop <id>${RESET}    — Stop a lab by ID"
  echo -e "  ${GREEN}status${RESET}       — Show running lab containers"
  echo -e "  ${GREEN}start all${RESET}    — Start all labs"
  echo -e "  ${GREEN}stop all${RESET}     — Stop all labs"
  echo -e "  ${GREEN}list${RESET}         — List available labs"
  echo -e "  ${GREEN}quit${RESET}         — Exit"
  echo ""

  while true; do
    echo -ne "  ${BOLD}lab>${RESET} "
    read -r cmd arg1 || break
    case "$cmd" in
      start)
        check_docker
        if [[ "${arg1:-}" == "all" ]]; then all_action start
        else dispatch start "${arg1:-}"; fi ;;
      stop)
        if [[ "${arg1:-}" == "all" ]]; then all_action stop
        else dispatch stop "${arg1:-}"; fi ;;
      status) status_all ;;
      list)   list_labs ;;
      quit|exit|q) info "Bye!"; exit 0 ;;
      "") ;;
      *) warn "Unknown command: $cmd — type 'quit' to exit" ;;
    esac
    echo ""
  done
}

# ---------------- main --------------------------------------------------------
banner

case "${1:-menu}" in
  menu)
    check_docker
    interactive_menu ;;
  list)
    list_labs ;;
  status)
    status_all ;;
  start)
    check_docker
    if [[ "${2:-}" == "all" ]]; then all_action start
    else dispatch start "${2:-}"; fi ;;
  stop)
    if [[ "${2:-}" == "all" ]]; then all_action stop
    else dispatch stop "${2:-}"; fi ;;
  help|-h|--help)
    list_labs
    echo "Usage: $0 [menu|list|status|start <id|all>|stop <id|all>]"
    echo "" ;;
  *)
    bad "Unknown command: ${1}"
    echo "Usage: $0 [menu|list|status|start <id|all>|stop <id|all>]"
    exit 1 ;;
esac
