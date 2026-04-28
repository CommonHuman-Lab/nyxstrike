#!/usr/bin/env bash
# =============================================================================
# Lab: OWASP WebGoat
# Lesson-based deliberately insecure Java web app — covers the same vuln
# classes as PortSwigger Web Academy (SQLi, XSS, SSRF, JWT, XXE, etc.)
# Image: webgoat/webgoat
# =============================================================================

LAB_NAME="WebGoat"
CONTAINER_NAME="nyxstrike-webgoat"
HOST_PORT=8888

source "$(dirname "$0")/_common.sh"
require_action "${1:-}"

case "$1" in
  start)
    header "Starting..."
    ensure_container_gone "$CONTAINER_NAME"
    info "Pulling image webgoat/webgoat (latest)..."
    docker pull webgoat/webgoat:latest

    docker run -d \
      --name "$CONTAINER_NAME" \
      -p "${HOST_PORT}:8080" \
      -e TZ=UTC \
      --restart unless-stopped \
      webgoat/webgoat:latest

    wait_for_port 127.0.0.1 "$HOST_PORT" 90

    INFO_LINES=(
      "WebGoat URL|http://127.0.0.1:${HOST_PORT}/WebGoat"
      "WebWolf URL|http://127.0.0.1:${HOST_PORT}/WebWolf"
      "Register|Create account on first visit"
      "Coverage|SQLi / XSS / XXE / JWT / IDOR / SSRF"
      "Coverage 2|Path traversal / Crypto / Auth bypass"
      "Stop|./webgoat.sh stop"
    )
    access_card INFO_LINES
    good "WebGoat is up!"
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
