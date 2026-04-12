#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/install.sh
#   bash scripts/install.sh -p python3
#   bash scripts/install.sh -s
#   bash scripts/install.sh -t
#   bash scripts/install.sh -t -b
#   bash scripts/install.sh -u
#   bash scripts/install.sh -r
#   bash scripts/install.sh -a
#   bash scripts/install.sh -y
#   bash scripts/install.sh -ai
#   bash scripts/install.sh -ai-small

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/nyxstrike-env"
PYTHON_BIN="python3"
GIT_TOOLS_DIR="${ROOT_DIR}/git_tools"
INSTALL_TOOLS=false
INSTALL_BIG_PACKAGES=false
UPDATE_GIT_TOOLS=false
RUN_AFTER_INSTALL=false
UPDATE_SELF=false
UPDATE_PYTHON_PACKAGES=false
PIP_BOOTSTRAPPED=false
INSTALL_AI_MODEL=false

OLLAMA_MODEL_BASE="huihui_ai/qwen3.5-abliterated:9b"
OLLAMA_MODEL_NAME="nyxstrike-qwen"

# External tools to install
# Format: "apt_package:expected_binary"
APT_PACKAGES=(
)

# Format: "go_module@version:expected_binary"
GO_PACKAGES=(
)

# Format: "cargo_package:expected_binary"
CARGO_PACKAGES=(
  "x8:x8"
)

# Git repos to clone into git_tools.
# Format: "repo_url|requirements_file_relpath"
# Leave requirements file empty when no extra setup is needed.
GIT_REPOS=(
#  "https://github.com/nsonaniya2010/SubDomainizer.git|requirements.txt"
  "https://github.com/rastating/dnmasscan.git|"
  "https://github.com/hannob/tlshelpers.git|"
)

is_apt_package_installed() {
  local package_name="$1"
  dpkg -s "${package_name}" >/dev/null 2>&1
}

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

  if ! git -C "${ROOT_DIR}" diff --quiet || ! git -C "${ROOT_DIR}" diff --cached --quiet || [[ -n "$(git -C "${ROOT_DIR}" ls-files --others --exclude-standard)" ]]; then
    echo "Skipping self update: local changes detected in project repo."
    return
  fi

  echo "Updating project repository..."
  if ! git -C "${ROOT_DIR}" pull --ff-only --quiet; then
    echo "Self update failed (non-fast-forward or remote issue). Continuing without blocking install."
  fi
}

install_external_tools() {
  if [[ ${#APT_PACKAGES[@]} -eq 0 && ${#GO_PACKAGES[@]} -eq 0 && ${#CARGO_PACKAGES[@]} -eq 0 ]]; then
    return
  fi

  if [[ ${#APT_PACKAGES[@]} -gt 0 ]]; then
    if ! command -v apt >/dev/null 2>&1; then
      echo "Skipping apt packages: apt is not available on this system."
    else
      local apt_to_install=()
      local apt_entry=""
      local apt_pkg=""
      local apt_bin=""

      for apt_entry in "${APT_PACKAGES[@]}"; do
        apt_pkg="${apt_entry%%:*}"
        apt_bin="${apt_entry##*:}"

        if command -v "${apt_bin}" >/dev/null 2>&1 || is_apt_package_installed "${apt_pkg}"; then
          continue
        fi

        apt_to_install+=("${apt_pkg}")
      done

      if [[ ${#apt_to_install[@]} -gt 0 ]]; then
        echo "Installing apt packages: ${apt_to_install[*]}"
        sudo apt install -y -qq "${apt_to_install[@]}"
      else
        echo "No missing apt packages to install."
      fi
    fi
  fi

  if [[ ${#GO_PACKAGES[@]} -gt 0 ]]; then
    if ! command -v go >/dev/null 2>&1; then
      echo "Skipping Go packages: go is not installed."
    else
      local go_entry=""
      local go_pkg=""
      local go_bin=""

      for go_entry in "${GO_PACKAGES[@]}"; do
        go_pkg="${go_entry%%:*}"
        go_bin="${go_entry##*:}"

        if command -v "${go_bin}" >/dev/null 2>&1; then
          continue
        fi

        echo "Installing Go package: ${go_pkg}"
        go install "${go_pkg}"
      done
    fi
  fi

  if [[ ${#CARGO_PACKAGES[@]} -gt 0 ]]; then
    if ! command -v cargo >/dev/null 2>&1; then
      echo "Skipping Cargo packages: cargo is not installed."
    else
      local cargo_entry=""
      local cargo_pkg=""
      local cargo_bin=""

      for cargo_entry in "${CARGO_PACKAGES[@]}"; do
        cargo_pkg="${cargo_entry%%:*}"
        cargo_bin="${cargo_entry##*:}"

        if command -v "${cargo_bin}" >/dev/null 2>&1; then
          continue
        fi

        cargo install --quiet "${cargo_pkg}"
      done
    fi
  fi
}

setup_git_repo() {
  local repo_dir="$1"
  local requirements_rel="$2"
  local repo_name=""
  local requirements_file=""
  local stamp_file=""
  local python_minor=""

  if [[ -z "${requirements_rel}" ]]; then
    return
  fi

  repo_name="$(basename "${repo_dir}")"

  requirements_file="${repo_dir}/${requirements_rel}"
  if [[ ! -f "${requirements_file}" ]]; then
    echo "Repo setup skipped (missing requirements): ${requirements_file}"
    return
  fi

  stamp_file="${repo_dir}/.app_setup_$(basename "${requirements_rel}").stamp"
  if [[ -f "${stamp_file}" && "${stamp_file}" -nt "${requirements_file}" ]]; then
    echo "Repo already prepared, skipping: ${repo_name}"
    return
  fi

  python_minor="$(${VENV_DIR}/bin/python3 -c 'import sys; print(sys.version_info.minor)')"
  if [[ "${repo_name}" == "SubDomainizer" && "${python_minor}" -ge 13 ]]; then
    echo "Repo setup skipped for ${repo_name}: dependency stack is not compatible with Python 3.13+ (htmlmin imports removed cgi module)."
    echo "Use a Python 3.12 or older venv inside ${repo_dir} if you want to run it locally."
    return
  fi

  echo "Preparing repo: ${repo_name}"
  if ! "${VENV_DIR}/bin/python3" -m pip --disable-pip-version-check install --quiet --progress-bar off -r "${requirements_file}"; then
    echo "Repo setup failed for ${repo_name}; continuing without blocking install."
    echo "You can run setup manually inside ${repo_dir}."
    return
  fi

  touch "${stamp_file}"
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
  local requirements_name=""
  local stamp_file=""

  requirements_name="$(basename "${requirements_file}")"
  stamp_file="${VENV_DIR}/.app_python_deps_${requirements_name}.stamp"

  if [[ "${UPDATE_PYTHON_PACKAGES}" != true && -f "${stamp_file}" && "${stamp_file}" -nt "${requirements_file}" ]]; then
    return
  fi

  ensure_pip_ready
  echo "Installing Python deps from: ${requirements_name}"
  "${VENV_DIR}/bin/python3" -m pip --disable-pip-version-check install --quiet --progress-bar off -r "${requirements_file}"
  touch "${stamp_file}"
}

install_ollama_model() {
  if [[ "${INSTALL_AI_MODEL}" != true ]]; then
    return
  fi

  local modelfile="${ROOT_DIR}/Modelfile"

  # Step 1: ensure ollama is installed
  if ! command -v ollama >/dev/null 2>&1; then
    echo "Ollama not found. Installing via official install script..."
    if ! curl -fsSL https://ollama.com/install.sh | sh; then
      echo "Ollama install failed. Skipping AI model setup."
      return
    fi
  fi

  # Step 2: ensure the base model is pulled
  if ! ollama list 2>/dev/null | grep -qF "${OLLAMA_MODEL_BASE}"; then
    echo "Pulling base model: ${OLLAMA_MODEL_BASE} (this may take a while)..."
    if ! ollama pull "${OLLAMA_MODEL_BASE}"; then
      echo "Failed to pull base model. Skipping AI model creation."
      return
    fi
  fi

  # # Step 3: check Modelfile exists
  # if [[ ! -f "${modelfile}" ]]; then
  #   echo "Modelfile not found at ${modelfile}. Skipping model creation."
  #   return
  # fi

  # # Step 4: create (or re-create) the named model
  # if ollama list 2>/dev/null | grep -qF "${OLLAMA_MODEL_NAME}"; then
  #   echo "Model '${OLLAMA_MODEL_NAME}' already exists. Recreating from Modelfile..."
  # else
  #   echo "Creating model '${OLLAMA_MODEL_NAME}' from Modelfile..."
  # fi

  # if ! ollama create "${OLLAMA_MODEL_NAME}" -f "${modelfile}"; then
  #   echo "Model creation failed. You can retry manually:"
  #   echo "  ollama create ${OLLAMA_MODEL_NAME} -f ${modelfile}"
  #   return
  # fi
}

clone_or_update_git_tools() {
  if [[ ${#GIT_REPOS[@]} -eq 0 ]]; then
    return
  fi

  if ! command -v git >/dev/null 2>&1; then
    echo "Skipping git repo sync: git is not installed."
    return
  fi

  mkdir -p "${GIT_TOOLS_DIR}"

  local repo_entry=""
  local repo_url=""
  local repo_requirements=""
  local repo_name=""
  local repo_dir=""

  for repo_entry in "${GIT_REPOS[@]}"; do
    IFS='|' read -r repo_url repo_requirements <<< "${repo_entry}"
    repo_name="$(basename "${repo_url}" .git)"
    repo_dir="${GIT_TOOLS_DIR}/${repo_name}"

    if [[ -d "${repo_dir}/.git" ]]; then
      if [[ "${UPDATE_GIT_TOOLS}" == true ]]; then
        echo "Updating git repo: ${repo_name}"
        git -C "${repo_dir}" pull --ff-only --quiet
      fi
    elif [[ -e "${repo_dir}" ]]; then
      echo "Path exists and is not a git repo, skipping: ${repo_dir}"
    else
      echo "Cloning git repo: ${repo_name}"
      git clone --quiet "${repo_url}" "${repo_dir}"
    fi

    if [[ -d "${repo_dir}/.git" ]]; then
      setup_git_repo "${repo_dir}" "${repo_requirements}"
    fi
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    -s|--update-self)
      UPDATE_SELF=true
      shift
      ;;
    -t|--install-tools)
      INSTALL_TOOLS=true
      shift
      ;;
    -b|--install-big-packages)
      INSTALL_BIG_PACKAGES=true
      INSTALL_TOOLS=true
      shift
      ;;
    -u|--update-git-tools)
      UPDATE_GIT_TOOLS=true
      INSTALL_TOOLS=true
      shift
      ;;
    -r|--run)
      RUN_AFTER_INSTALL=true
      shift
      ;;
    -y|--update-python-packages)
      UPDATE_PYTHON_PACKAGES=true
      shift
      ;;
    -a|--all)
      UPDATE_SELF=true
      INSTALL_TOOLS=true
      RUN_AFTER_INSTALL=true
      shift
      ;;
    -ai)
      INSTALL_AI_MODEL=true
      OLLAMA_MODEL_BASE="huihui_ai/qwen3.5-abliterated:9b"
      OLLAMA_MODEL_NAME="nyxstrike-qwen"
      shift
      ;;
    -ai-small)
      INSTALL_AI_MODEL=true
      OLLAMA_MODEL_BASE="huihui_ai/qwen3.5-abliterated:4b"
      OLLAMA_MODEL_NAME="nyxstrike-qwen"
      shift
      ;;
    -h|--help)
      echo "NyxStrike install"
      echo ""
      echo "Options:"
      echo "  -a, --all               Shortcut for -s -t -r"
      echo "  -t, --install-tools     Install external apt/go/cargo tools and clone git_tools repos"
      echo "  -b, --install-big-packages  Install heavy optional Python extras (implies -t)"
      echo "  -u, --update-git-tools  Pull latest for already-cloned repos (implies -t)"
      echo "  -y, --update-python-packages  Force reinstall of Python requirements"
      echo "  -p, --python <bin>      Python binary (default: python3)"
      echo "  -s, --update-self       git pull --ff-only this project repo (skips if local changes)"
      echo "  -r, --run               Start server after install (runs ./scripts/run.sh --server)"
      echo "  -ai                     Install Ollama + pull base model + create nyxstrike-qwen model (9b)"
      echo "  -ai-small               Install Ollama + pull base model + create nyxstrike-qwen-small model (4b)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage."
      exit 1
      ;;
  esac
done

update_self_repo

echo "[1/4] Preparing virtual environment..."
if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "[2/4] Syncing Python dependencies...(will take a while on first run)"
install_requirements_file "${ROOT_DIR}/requirements.txt"

if [[ "${INSTALL_TOOLS}" == true && -f "${ROOT_DIR}/requirements-extra.txt" ]]; then
  install_requirements_file "${ROOT_DIR}/requirements-extra.txt"
fi

if [[ "${INSTALL_TOOLS}" == true && "${INSTALL_BIG_PACKAGES}" == true && -f "${ROOT_DIR}/requirements-big.txt" ]]; then
  echo "Installing big optional Python packages..."
  install_requirements_file "${ROOT_DIR}/requirements-big.txt"
fi

if [[ "${INSTALL_TOOLS}" == true ]]; then
  echo "[3/4] Installing external tools..."
  install_external_tools
else
  echo "[3/4] Skipping external tools (use --install-tools to enable)."
fi

if [[ "${INSTALL_TOOLS}" == true ]]; then
  echo "[4/4] Syncing git tool repositories..."
  clone_or_update_git_tools
else
  echo "[4/4] Skipping git tool repositories (use --install-tools to enable)."
fi

if [[ "${INSTALL_AI_MODEL}" == true ]]; then
  echo "[5/5] Setting up AI model..."
  install_ollama_model
fi

echo "Install complete."

if [[ "${RUN_AFTER_INSTALL}" == false ]]; then
  echo ""
  echo "Next step:"
  echo "  ./scripts/run.sh --server"
fi

if [[ "${RUN_AFTER_INSTALL}" == true ]]; then
  echo "Starting server..."
  exec bash "${ROOT_DIR}/scripts/run.sh" --server
fi
