#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/run.sh              # MCP only (default — works as a 5ire MCP launcher)
#   bash scripts/run.sh --server
#   bash scripts/run.sh --mcp
#   bash scripts/run.sh --server --mcp

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_URL="http://127.0.0.1:8888"
PROFILE="default"

# Resolve venv — support both local dev name and production install name.
if [[ -x "${ROOT_DIR}/nyxstrike-env/bin/python3" ]]; then
  VENV_DIR="${ROOT_DIR}/nyxstrike-env"
elif [[ -x "${ROOT_DIR}/nyxstrike-env/bin/python3" ]]; then
  VENV_DIR="${ROOT_DIR}/nyxstrike-env"
else
  echo "No virtualenv found. Run: bash scripts/install.sh"
  exit 1
fi

RUN_SERVER=false
RUN_MCP=false

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
      echo "NyxStrike run"
      echo ""
      echo "Options:"
      echo "  --server             Start nyxstrike_server.py"
      echo "  --mcp                Start nyxstrike_mcp.py (default when no flags given)"
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

# When called with no arguments (e.g. by 5ire as an MCP launcher), default to MCP mode.
if [[ "${RUN_SERVER}" == false && "${RUN_MCP}" == false ]]; then
  RUN_MCP=true
fi

# Ensure venv-installed binaries are preferred for subprocess checks/tools.
export PATH="${VENV_DIR}/bin:${PATH}"

cd "${ROOT_DIR}"

if [[ "${RUN_SERVER}" == true && "${RUN_MCP}" == true ]]; then
  echo "Starting API server in background..."
  "${VENV_DIR}/bin/python3" "${ROOT_DIR}/nyxstrike_server.py" &
  server_pid=$!

  cleanup() {
    kill "${server_pid}" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT

  echo "Starting MCP client..."
  exec "${VENV_DIR}/bin/python3" "${ROOT_DIR}/nyxstrike_mcp.py" --server "${SERVER_URL}" --profile "${PROFILE}"
fi

if [[ "${RUN_SERVER}" == true ]]; then
  exec "${VENV_DIR}/bin/python3" "${ROOT_DIR}/nyxstrike_server.py"
fi

exec "${VENV_DIR}/bin/python3" "${ROOT_DIR}/nyxstrike_mcp.py" --server "${SERVER_URL}" --profile "${PROFILE}"

