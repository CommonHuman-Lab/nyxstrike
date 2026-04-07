#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/run.sh --server
#   bash scripts/run.sh --mcp
#   bash scripts/run.sh --server --mcp

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/hexstrike-env"
RUN_SERVER=false
RUN_MCP=false
SERVER_URL="http://127.0.0.1:8888"
PROFILE="full"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server)
      RUN_SERVER=true
      shift
      ;;
    --mcp)
      RUN_MCP=true
      shift
      ;;
    --server-url)
      SERVER_URL="$2"
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    -h|--help)
      echo "HexStrike run"
      echo ""
      echo "Options:"
      echo "  --server             Start hexstrike_server.py"
      echo "  --mcp                Start hexstrike_mcp.py"
      echo "  --server-url <url>   MCP target server URL (default: ${SERVER_URL})"
      echo "  --profile <name>     MCP profile (default: ${PROFILE})"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage."
      exit 1
      ;;
  esac
done

if [[ ! -x "${VENV_DIR}/bin/python3" ]]; then
  echo "Missing virtualenv at ${VENV_DIR}."
  echo "Run: bash scripts/install.sh"
  exit 1
fi

# Ensure venv-installed binaries are preferred for subprocess checks/tools.
export PATH="${VENV_DIR}/bin:${PATH}"

if [[ "${RUN_SERVER}" == false && "${RUN_MCP}" == false ]]; then
  echo "Nothing selected to run."
  echo "Use --server and/or --mcp"
  exit 1
fi

if [[ "${RUN_SERVER}" == true && "${RUN_MCP}" == true ]]; then
  echo "Starting API server in background..."
  "${VENV_DIR}/bin/python3" "${ROOT_DIR}/hexstrike_server.py" &
  server_pid=$!

  cleanup() {
    kill "${server_pid}" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT

  echo "Starting MCP client..."
  "${VENV_DIR}/bin/python3" "${ROOT_DIR}/hexstrike_mcp.py" --server "${SERVER_URL}" --profile "${PROFILE}"
  exit 0
fi

if [[ "${RUN_SERVER}" == true ]]; then
  exec "${VENV_DIR}/bin/python3" "${ROOT_DIR}/hexstrike_server.py"
fi

exec "${VENV_DIR}/bin/python3" "${ROOT_DIR}/hexstrike_mcp.py" --server "${SERVER_URL}" --profile "${PROFILE}"
