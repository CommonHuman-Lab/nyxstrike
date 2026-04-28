#!/usr/bin/env bash
# =============================================================================
# Lab: OWASP Juice Shop
# Official Docker image — covers all OWASP Top 10 + many more vulns
# Image: bkimminich/juice-shop
# =============================================================================

LAB_NAME="Juice Shop"
CONTAINER_NAME="nyxstrike-juiceshop"
HOST_PORT=3000

source "$(dirname "$0")/_common.sh"
require_action "${1:-}"

case "$1" in
  start)
    header "Starting..."
    ensure_container_gone "$CONTAINER_NAME"
    info "Pulling image bkimminich/juice-shop (latest)..."
    docker pull bkimminich/juice-shop:latest

    docker run -d \
      --name "$CONTAINER_NAME" \
      -p "${HOST_PORT}:3000" \
      --restart unless-stopped \
      bkimminich/juice-shop:latest

    wait_for_port 127.0.0.1 "$HOST_PORT" 60

    INFO_LINES=(
      "URL|http://127.0.0.1:${HOST_PORT}"
      "Credentials|none (register on first visit)"
      "Admin email|admin@juice-sh.op"
      "Admin pass|admin123"
      "Challenges|82 OWASP Top 10 tasks"
      "Stop|./juiceshop.sh stop"
    )
    access_card INFO_LINES
    good "Juice Shop is up!"
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
