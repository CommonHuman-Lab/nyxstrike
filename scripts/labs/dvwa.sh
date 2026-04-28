#!/usr/bin/env bash
# =============================================================================
# Lab: DVWA — Damn Vulnerable Web App
# PHP + MySQL, classic sqli/xss/csrf/rfi/lfi/command injection labs
# Image: vulnerables/web-dvwa
# =============================================================================

LAB_NAME="DVWA"
CONTAINER_NAME="nyxstrike-dvwa"
HOST_PORT=8080

source "$(dirname "$0")/_common.sh"
require_action "${1:-}"

case "$1" in
  start)
    header "Starting..."
    ensure_container_gone "$CONTAINER_NAME"
    info "Pulling image vulnerables/web-dvwa (latest)..."
    docker pull vulnerables/web-dvwa:latest

    docker run -d \
      --name "$CONTAINER_NAME" \
      -p "${HOST_PORT}:80" \
      --restart unless-stopped \
      vulnerables/web-dvwa:latest

    wait_for_port 127.0.0.1 "$HOST_PORT" 60

    INFO_LINES=(
      "URL|http://127.0.0.1:${HOST_PORT}"
      "Username|admin"
      "Password|password"
      "Setup DB|http://127.0.0.1:${HOST_PORT}/setup.php"
      "Difficulty|Low / Medium / High / Impossible"
      "Stop|./dvwa.sh stop"
    )
    access_card INFO_LINES
    warn "First visit: click 'Create / Reset Database' on the setup page."
    good "DVWA is up!"
    ;;

  stop)
    header "Stopping..."
    if docker rm -f "$CONTAINER_NAME" &>/dev/null; then
      good "Container $CONTAINER_NAME removed."
    else
      warn "Container $CONTAINER_NAME was not running."
    fi
    ;;

  status)
    container_status "$CONTAINER_NAME"
    ;;
esac
