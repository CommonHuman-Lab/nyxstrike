#!/usr/bin/env bash
# =============================================================================
# Shared helpers for NyxStrike lab scripts
# Source this file at the top of each lab script:
#   source "$(dirname "$0")/_common.sh"
# =============================================================================

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
header(){ echo -e "\n${GREEN}${BOLD}  [$LAB_NAME]${RESET} $*"; }

# Print a nicely boxed access card after lab start
access_card() {
  local -n _lines=$1          # nameref to an array of "KEY|VALUE" strings
  echo ""
  echo -e "  ${GREEN}${BOLD}┌─────────────────────────────────────────┐${RESET}"
  printf   "  ${GREEN}${BOLD}│${RESET}  %-41s${GREEN}${BOLD}│${RESET}\n" "ACCESS INFO — ${LAB_NAME}"
  echo -e  "  ${GREEN}${BOLD}├─────────────────────────────────────────┤${RESET}"
  for line in "${_lines[@]}"; do
    IFS='|' read -r k v <<< "$line"
    printf  "  ${GREEN}${BOLD}│${RESET}  ${BOLD}%-14s${RESET} %-26s${GREEN}${BOLD}│${RESET}\n" "$k" "$v"
  done
  echo -e  "  ${GREEN}${BOLD}└─────────────────────────────────────────┘${RESET}"
  echo ""
}

# Wait until a container port is accepting connections (max 60s)
wait_for_port() {
  local host="${1:-127.0.0.1}"
  local port="$2"
  local timeout="${3:-60}"
  info "Waiting for ${host}:${port} to be ready..."
  local i=0
  while ! nc -z "$host" "$port" 2>/dev/null; do
    sleep 1
    i=$((i+1))
    if [[ $i -ge $timeout ]]; then
      warn "Timed out waiting for ${host}:${port}"
      return 1
    fi
  done
  good "Port ${port} is open"
}

# Ensure the container name doesn't already exist (running or stopped)
ensure_container_gone() {
  local name="$1"
  if docker ps -a --format '{{.Names}}' | grep -qx "$name" 2>/dev/null; then
    info "Removing existing container: $name"
    docker rm -f "$name" &>/dev/null || true
  fi
}

# Print status of a named container
container_status() {
  local name="$1"
  local state
  state=$(docker inspect --format '{{.State.Status}}' "$name" 2>/dev/null || echo "not found")
  case "$state" in
    running) good "Container ${name} is ${GREEN}running${RESET}" ;;
    exited)  warn "Container ${name} is stopped (exited)" ;;
    *)       info "Container ${name}: ${state}" ;;
  esac
}

# Enforce that we're called with start|stop|status
require_action() {
  local action="${1:-}"
  case "$action" in
    start|stop|status) ;;
    *)
      echo "Usage: $(basename "$0") {start|stop|status}"
      exit 1 ;;
  esac
}
