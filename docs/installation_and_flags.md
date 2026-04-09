# Installation and Install Script Flags

Quick guide for setting up HexStrike AI Community Edition and using all installer flags.

## Prerequisites

- Linux environment with `python3` (3.8+)
- `venv` support (usually from `python3-venv`)
- `git` (required for `--update-self`, git tool sync/update)
- `sudo` + `apt` only if you plan to install external tools with `--install-tools`

## Basic Installation

From the repository root:

```bash
bash scripts/install.sh
```

This will:

1. Create `hexstrike-env` if missing
2. Install Python dependencies from `requirements.txt`
3. Skip external tool installation by default
4. Skip git tool repository sync by default

## Dependency Caching Behavior

Python requirement installs are stamp-based for speed:

- First run installs dependencies
- Later runs skip install if requirements file has not changed
- Force reinstall with `--update-python-packages`

Stamp files are stored in the venv, e.g.:

- `hexstrike-env/.hexstrike_python_deps_requirements.txt.stamp`

## Flags (All Options)

| Short | Long | What it does |
|---|---|---|
| `-a` | `--all` | Shortcut for `-s -t -r` |
| `-t` | `--install-tools` | Install external apt/go/cargo tools and sync `git_tools` repos |
| `-b` | `--install-big-packages` | Install heavy optional Python deps from `requirements-big.txt` (implies `-t`) |
| `-u` | `--update-git-tools` | Pull latest changes for already-cloned repos in `git_tools` (implies `-t`) |
| `-y` | `--update-python-packages` | Force reinstall of Python requirements (ignores dependency stamps) |
| `-p` | `--python <bin>` | Choose Python binary (default: `python3`) |
| `-s` | `--update-self` | Run `git pull --ff-only` on this repo (skips when local changes exist) |
| `-r` | `--run` | Start server after install (`./scripts/run.sh --server`) |
| `-h` | `--help` | Show install script help |

## Common Command Examples

### Fast normal install (cached)

```bash
bash scripts/install.sh
```

### Force Python dependency refresh

```bash
bash scripts/install.sh --update-python-packages
```

### Install optional tools + git tool repos

```bash
bash scripts/install.sh --install-tools
```

### Install heavy optional Python packages too

```bash
bash scripts/install.sh -t -b
```

### Update cloned git tools and run server

```bash
bash scripts/install.sh -u -r
```

### Full workflow (self update + tools + run)

```bash
bash scripts/install.sh --all
```

## After Install

If you did not use `--run`, start server manually:

```bash
./scripts/run.sh --server
```
