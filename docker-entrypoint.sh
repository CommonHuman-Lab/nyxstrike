#!/usr/bin/env bash
# docker-entrypoint.sh — NyxStrike container startup
#
# Environment variables (set via docker run -e or docker-compose environment:):
#
#   NYX_AI            — install + pull large AI model (~8.4 GB) before starting
#   NYX_AI_SMALL      — install + pull small AI model (~2.5 GB) before starting
#   NYX_EXTRA_FLAGS   — any other nyxstrike.sh flags, e.g. "-b" for big packages
#
# Examples:
#   docker run -e NYX_AI_SMALL=1 nyxstrike
#   docker run -e NYX_EXTRA_FLAGS="--profile pentest" nyxstrike

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SETUP_FLAGS=()

if [[ -n "${NYX_AI:-}" ]]; then
  echo "[entrypoint] NYX_AI set — will install large AI model before starting server"
  SETUP_FLAGS+=("-ai")
fi

if [[ -n "${NYX_AI_SMALL:-}" ]]; then
  echo "[entrypoint] NYX_AI_SMALL set — will install small AI model before starting server"
  SETUP_FLAGS+=("-ai-small")
fi

# Any extra setup flags the user passed (e.g. "-b", "-u")
if [[ -n "${NYX_EXTRA_FLAGS:-}" ]]; then
  # shellcheck disable=SC2206
  read -ra EXTRA <<< "${NYX_EXTRA_FLAGS}"
  SETUP_FLAGS+=("${EXTRA[@]}")
fi

# Run setup if there is anything to do
if [[ ${#SETUP_FLAGS[@]} -gt 0 ]]; then
  echo "[entrypoint] Running setup: nyxstrike.sh ${SETUP_FLAGS[*]}"
  bash "${ROOT_DIR}/nyxstrike.sh" "${SETUP_FLAGS[@]}"
fi

echo "[entrypoint] Starting NyxStrike server..."
exec "${ROOT_DIR}/nyxstrike-env/bin/python3" "${ROOT_DIR}/nyxstrike_server.py"
