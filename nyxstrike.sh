#!/usr/bin/env bash
set -euo pipefail

# NyxStrike — main entrypoint
#
# Usage:
#   ./nyxstrike.sh                        # MCP launcher mode (default, used by 5ire)
#   ./nyxstrike.sh -a                     # Update + start server  (recommended)
#   ./nyxstrike.sh -a -ai                 # Same + AI model (~8.4 GB RAM)
#   ./nyxstrike.sh -a -ai-small           # Same + smaller AI model (~2.5 GB RAM)
#
#   ./nyxstrike.sh --server               # Start server only (no update/install)
#   ./nyxstrike.sh --mcp                  # Start MCP client only
#   ./nyxstrike.sh --server --mcp         # Start server in background + MCP client
#
#   ./nyxstrike.sh -s                     # Update repo only
#   ./nyxstrike.sh -t                     # Install external tools only
#   ./nyxstrike.sh -t -b                  # Install tools + heavy Python extras
#   ./nyxstrike.sh -y                     # Force reinstall Python requirements
#   ./nyxstrike.sh -ai                    # Install Ollama + 9b model
#   ./nyxstrike.sh -ai-small              # Install Ollama + 4b model

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/nyxstrike-env"
PYTHON_BIN="python3"
GIT_TOOLS_DIR="${ROOT_DIR}/git_tools"
OCTORIG_DIR="${ROOT_DIR}/scripts/octorig"

# --- install flags ---
INSTALL_TOOLS=false
INSTALL_BIG_PACKAGES=false
UPDATE_SELF=false
UPDATE_PYTHON_PACKAGES=false
PIP_BOOTSTRAPPED=false
INSTALL_AI_MODEL=false
AI_SMALL_MODE=false
AI_LARGE_MODE=false

OLLAMA_MODEL_BASE="huihui_ai/gemma-4-abliterated:e4b"
OLLAMA_MODEL_NAME="nyxstrike-ai"
OLLAMA_MODELFILE=""

# --- run flags ---
RUN_SERVER=false
RUN_MCP=false
SERVER_URL="http://127.0.0.1:8888"
PROFILE="default"

# --- do any setup at all? ---
DO_SETUP=false

# ---------------------------------------------------------------------------
# Setup functions (formerly install.sh)
# ---------------------------------------------------------------------------


update_self_repo() {
  if [[ "${UPDATE_SELF}" != true ]]; then
    return
  fi

  if ! command -v git >/dev/null 2>&1; then
    echo "Skipping self update: git is not installed."
    return
  fi

  if [[ ! -d "${ROOT_DIR}/.git" ]]; then
    echo "Skipping self update: repository metadata not found."
    return
  fi

  if ! git -C "${ROOT_DIR}" diff --quiet || \
     ! git -C "${ROOT_DIR}" diff --cached --quiet || \
     [[ -n "$(git -C "${ROOT_DIR}" ls-files --others --exclude-standard)" ]]; then
    echo "Skipping self update: local changes detected in project repo."
    return
  fi

  echo "Updating project repository..."
  if ! git -C "${ROOT_DIR}" pull --ff-only --quiet; then
    echo "Self update failed (non-fast-forward or remote issue). Continuing."
  fi
}

update_octorig() {
  if [[ ! -d "${OCTORIG_DIR}/.git" ]]; then
    git clone --quiet https://github.com/CommonHuman-Lab/OctoRig "${OCTORIG_DIR}" 2>/dev/null
    return
  fi
}


ensure_pip_ready() {
  if [[ "${PIP_BOOTSTRAPPED}" == true ]]; then
    return
  fi
  "${VENV_DIR}/bin/python3" -m pip --disable-pip-version-check install --quiet --upgrade pip
  PIP_BOOTSTRAPPED=true
}

install_requirements_file() {
  local requirements_file="$1"
  local requirements_name
  requirements_name="$(basename "${requirements_file}")"
  local stamp_file="${VENV_DIR}/.app_python_deps_${requirements_name}.stamp"

  if [[ "${UPDATE_PYTHON_PACKAGES}" != true && -f "${stamp_file}" && "${stamp_file}" -nt "${requirements_file}" ]]; then
    return
  fi

  ensure_pip_ready
  echo "Installing Python deps from: ${requirements_name}"
  "${VENV_DIR}/bin/python3" -m pip --disable-pip-version-check install --quiet --progress-bar off -r "${requirements_file}"
  touch "${stamp_file}"
}

write_model_to_config_local() {
  local model="$1"
  local data_dir="${NYXSTRIKE_DATA_DIR:-${ROOT_DIR}/.nyxstrike_data}"
  local config_file="${NYXSTRIKE_CONFIG_FILE:-${data_dir}/config/config_local.json}"
  local config_dir
  config_dir="$(dirname "${config_file}")"

  if ! command -v python3 >/dev/null 2>&1; then
    echo "Warning: python3 not found; could not update config_local.json with model '${model}'."
    echo "Set NYXSTRIKE_LLM_MODEL=${model} manually in ${config_file}."
    return
  fi

  local existing="{}"
  if [[ -f "${config_file}" ]]; then
    existing="$(cat "${config_file}")"
  else
    mkdir -p "${config_dir}"
  fi

  python3 - "${config_file}" "${model}" "${existing}" <<'PYEOF'
import sys, json
config_file, model, existing_json = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    data = json.loads(existing_json)
except Exception:
    data = {}
data["NYXSTRIKE_LLM_MODEL"] = model
with open(config_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PYEOF
}

install_ollama_model() {
  if [[ "${INSTALL_AI_MODEL}" != true ]]; then
    return
  fi

  if ! command -v ollama >/dev/null 2>&1; then
    echo "Ollama not found. Installing via official install script..."
    if ! curl -fsSL https://ollama.com/install.sh | sh; then
      echo "Ollama install failed. Skipping AI model setup."
      return
    fi
  fi

  if ! ollama list 2>/dev/null | grep -qF "${OLLAMA_MODEL_BASE}"; then
    echo "Pulling base model: ${OLLAMA_MODEL_BASE} (this may take a while)..."
    if ! ollama pull "${OLLAMA_MODEL_BASE}"; then
      echo "Failed to pull base model. Skipping AI model creation."
      return
    fi
  fi

  if [[ -n "${OLLAMA_MODELFILE}" && -f "${OLLAMA_MODELFILE}" ]]; then
    if ollama list 2>/dev/null | grep -qF "${OLLAMA_MODEL_NAME}"; then
      write_model_to_config_local "${OLLAMA_MODEL_NAME}"
    else
      echo "Creating custom model '${OLLAMA_MODEL_NAME}' from ${OLLAMA_MODELFILE}..."
      if ! ollama create "${OLLAMA_MODEL_NAME}" -f "${OLLAMA_MODELFILE}"; then
        echo "Failed to create custom model. Falling back to base model."
        write_model_to_config_local "${OLLAMA_MODEL_BASE}"
        return
      fi
      write_model_to_config_local "${OLLAMA_MODEL_NAME}"
    fi
  elif [[ "${AI_SMALL_MODE}" == true || "${AI_LARGE_MODE}" == true ]]; then
    write_model_to_config_local "${OLLAMA_MODEL_BASE}"
  fi
}

run_setup() {
  update_self_repo

  echo "[1/4] Preparing virtual environment..."
  if [[ ! -d "${VENV_DIR}" ]]; then
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi

  echo "[2/4] Syncing Python dependencies... (may take a while on first run)"
  install_requirements_file "${ROOT_DIR}/dependencies/requirements.txt"

  if [[ "${INSTALL_TOOLS}" == true && -f "${ROOT_DIR}/dependencies/requirements-extra.txt" ]]; then
    install_requirements_file "${ROOT_DIR}/dependencies/requirements-extra.txt"
  fi

  if [[ "${INSTALL_TOOLS}" == true && "${INSTALL_BIG_PACKAGES}" == true && -f "${ROOT_DIR}/dependencies/requirements-big.txt" ]]; then
    echo "Installing big optional Python packages..."
    install_requirements_file "${ROOT_DIR}/dependencies/requirements-big.txt"
  fi

  if [[ "${INSTALL_TOOLS}" == true ]]; then
    update_octorig
    echo "[3/4] Installing external tools via scripts/install_tools.sh..."
    bash "${ROOT_DIR}/scripts/install_tools.sh"
  else
    echo "[3/4] Skipping external tools (use -t to enable)."
  fi

  if [[ "${INSTALL_AI_MODEL}" == true ]]; then
    echo "[4/4] Setting up AI model..."
    install_ollama_model
  else
    echo "[4/4] Skipping AI model setup (use -ai or -ai-small to enable)."
  fi

  echo "Setup complete."
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    -s|--update-self)
      UPDATE_SELF=true
      DO_SETUP=true
      shift
      ;;
    -t|--install-tools)
      INSTALL_TOOLS=true
      DO_SETUP=true
      shift
      ;;
    -b|--install-big-packages)
      INSTALL_BIG_PACKAGES=true
      INSTALL_TOOLS=true
      DO_SETUP=true
      shift
      ;;
    -y|--update-python-packages)
      UPDATE_PYTHON_PACKAGES=true
      DO_SETUP=true
      shift
      ;;
    -a|--all)
      UPDATE_SELF=true
      DO_SETUP=true
      RUN_SERVER=true
      shift
      ;;
    -ai)
      INSTALL_AI_MODEL=true
      AI_LARGE_MODE=true
      OLLAMA_MODEL_BASE="huihui_ai/gemma-4-abliterated:e4b"
      OLLAMA_MODELFILE="${ROOT_DIR}/Modelfiles/Modelfile.gemma4-e4b"
      export NYXSTRIKE_LLM_WARMUP=1
      DO_SETUP=true
      shift
      ;;
    -ai-small)
      INSTALL_AI_MODEL=true
      AI_SMALL_MODE=true
      OLLAMA_MODEL_BASE="huihui_ai/qwen3.5-abliterated:2B"
      OLLAMA_MODELFILE="${ROOT_DIR}/Modelfiles/Modelfile.qwen3-2b"
      export NYXSTRIKE_LLM_WARMUP=1
      DO_SETUP=true
      shift
      ;;
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
      echo "NyxStrike"
      echo ""
      echo "Setup:"
      echo "  -a, --all               Start here — update repo + start server"
      echo "  -s, --update-self       git pull this repo (skips if local changes present)"
      echo "  -t, --install-tools     Install security tools via scripts/install_tools.sh"
      echo "                          (run scripts/install_tools.sh --help for category/dry-run options)"
      echo "  -b, --install-big-packages  Install heavy optional Python extras (implies -t)"
      echo "  -u, --update-git-tools  Pull latest for already-cloned git_tools repos (implies -t)"
      echo "  -y, --update-python-packages  Force reinstall of Python requirements"
      echo "  -p, --python <bin>      Python binary to use (default: python3)"
      echo "  -ai                     Install Ollama + pull 9b model (~8.4 GB RAM)"
      echo "  -ai-small               Install Ollama + pull 4b model (~2.5 GB RAM)"
      echo ""
      echo "Run:"
      echo "  --server                Start the NyxStrike API server"
      echo "  --mcp                   Start the MCP client (default when no flags given)"
      echo "  --server --mcp          Start server in background + MCP client"
      echo "  --server-url <url>      MCP target server URL (default: ${SERVER_URL})"
      echo "  --profile <name>        MCP profile (default: ${PROFILE})"
      echo ""
      echo "Examples:"
      echo "  ./nyxstrike.sh -a               # start here (first run + daily driver)"
      echo "  ./nyxstrike.sh -a -ai-small     # with local AI model (low-spec)"
      echo "  ./nyxstrike.sh --server         # just start the server"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage."
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Default: no args → MCP launcher mode (preserves 5ire compatibility)
# ---------------------------------------------------------------------------

if [[ "${DO_SETUP}" == false && "${RUN_SERVER}" == false && "${RUN_MCP}" == false ]]; then
  RUN_MCP=true
fi

# ---------------------------------------------------------------------------
# Resolve venv (must exist before we can run anything)
# ---------------------------------------------------------------------------

if [[ ! -x "${VENV_DIR}/bin/python3" ]]; then
  if [[ "${DO_SETUP}" == true ]]; then
    # venv will be created inside run_setup
    true
  else
    echo "No virtualenv found. Run: ./nyxstrike.sh -a"
    exit 1
  fi
fi

export PATH="${VENV_DIR}/bin:${PATH}"
cd "${ROOT_DIR}"

# ---------------------------------------------------------------------------
# Run setup phase if requested
# ---------------------------------------------------------------------------

if [[ "${DO_SETUP}" == true ]]; then
  run_setup
fi

# ---------------------------------------------------------------------------
# Run phase
# ---------------------------------------------------------------------------

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

if [[ "${RUN_MCP}" == true ]]; then
  exec "${VENV_DIR}/bin/python3" "${ROOT_DIR}/nyxstrike_mcp.py" --server "${SERVER_URL}" --profile "${PROFILE}"
fi
