#!/usr/bin/env bash
# =============================================================================
# Lab: HTB-Style — CTFd platform + a vulnerable challenge container
# Runs CTFd (the CTF management platform used by HackTheBox / many CTFs)
# alongside a Vulhub-based vulnerable challenge for realistic HTB feel.
#
# Challenge: Apache Struts2 CVE-2017-5638 RCE (classic HTB-style box)
# CTFd:      http://127.0.0.1:8000  (score tracking / flag submission)
# Target:    http://127.0.0.1:8090  (the vulnerable app)
# =============================================================================

LAB_NAME="HTB Style"
CTFD_CONTAINER="nyxstrike-ctfd"
CHALLENGE_CONTAINER="nyxstrike-htb-challenge"
CTFD_PORT=8000
CHALLENGE_PORT=8090

# CTFd requires a network so it can reach its DB
NETWORK_NAME="nyxstrike-htb-net"

source "$(dirname "$0")/_common.sh"
require_action "${1:-}"

case "$1" in
  start)
    header "Starting..."

    # ---- network ----
    if ! docker network ls --format '{{.Name}}' | grep -qx "$NETWORK_NAME"; then
      info "Creating Docker network $NETWORK_NAME"
      docker network create "$NETWORK_NAME" &>/dev/null
    fi

    # ---- CTFd stack (CTFd + Redis + MySQL) ----
    ensure_container_gone "nyxstrike-ctfd-db"
    ensure_container_gone "nyxstrike-ctfd-redis"
    ensure_container_gone "$CTFD_CONTAINER"

    info "Starting CTFd database..."
    docker run -d \
      --name nyxstrike-ctfd-db \
      --network "$NETWORK_NAME" \
      -e MYSQL_ROOT_PASSWORD=ctfd \
      -e MYSQL_DATABASE=ctfd \
      -e MYSQL_USER=ctfd \
      -e MYSQL_PASSWORD=ctfd \
      --restart unless-stopped \
      mariadb:10.11 \
      --character-set-server=utf8mb4 \
      --collation-server=utf8mb4_unicode_ci \
      --wait_timeout=28800 \
      --log-warnings=0 &>/dev/null

    info "Starting CTFd Redis..."
    docker run -d \
      --name nyxstrike-ctfd-redis \
      --network "$NETWORK_NAME" \
      --restart unless-stopped \
      redis:7-alpine &>/dev/null

    info "Pulling CTFd image..."
    docker pull ctfd/ctfd:latest &>/dev/null

    info "Starting CTFd..."
    docker run -d \
      --name "$CTFD_CONTAINER" \
      --network "$NETWORK_NAME" \
      -p "${CTFD_PORT}:8000" \
      -e DATABASE_URL="mysql+pymysql://ctfd:ctfd@nyxstrike-ctfd-db/ctfd" \
      -e REDIS_URL="redis://nyxstrike-ctfd-redis:6379" \
      -e SECRET_KEY="nyxstrike-htb-secret" \
      --restart unless-stopped \
      ctfd/ctfd:latest &>/dev/null

    # ---- Vulnerable challenge: Apache Struts2 S2-045 ----
    ensure_container_gone "$CHALLENGE_CONTAINER"
    info "Pulling Struts2 CVE-2017-5638 challenge image..."
    docker pull vulhub/struts2:2.3.30 2>/dev/null || \
      docker pull piesecurity/apache-struts2-cve-2017-5638:latest 2>/dev/null || \
      { warn "Struts2 image unavailable — using a generic Apache httpd placeholder"; \
        docker pull httpd:2.4; \
        docker run -d --name "$CHALLENGE_CONTAINER" -p "${CHALLENGE_PORT}:80" \
          --restart unless-stopped httpd:2.4 &>/dev/null; }

    # Try vulhub image first, fall back gracefully (already handled above)
    docker ps --format '{{.Names}}' | grep -qx "$CHALLENGE_CONTAINER" || \
      docker run -d \
        --name "$CHALLENGE_CONTAINER" \
        -p "${CHALLENGE_PORT}:8080" \
        --restart unless-stopped \
        vulhub/struts2:2.3.30 &>/dev/null 2>&1 || true

    wait_for_port 127.0.0.1 "$CTFD_PORT" 90

    INFO_LINES=(
      "CTFd (scoreboard)|http://127.0.0.1:${CTFD_PORT}"
      "CTFd setup|Complete setup wizard on first visit"
      "Challenge target|http://127.0.0.1:${CHALLENGE_PORT}"
      "Vuln|Apache Struts2 CVE-2017-5638 RCE"
      "CVSSv3|10.0 (Critical)"
      "Stop|./htb_style.sh stop"
    )
    access_card INFO_LINES
    info "Tip: set the flag manually in CTFd after you get RCE on the challenge box."
    good "HTB-Style lab is up!"
    ;;

  stop)
    header "Stopping..."
    for c in "$CTFD_CONTAINER" "nyxstrike-ctfd-db" "nyxstrike-ctfd-redis" "$CHALLENGE_CONTAINER"; do
      if docker rm -f "$c" &>/dev/null; then
        good "Removed $c"
      else
        info "$c was not running"
      fi
    done
    docker network rm "$NETWORK_NAME" &>/dev/null && info "Network $NETWORK_NAME removed" || true
    ;;

  status)
    for c in "$CTFD_CONTAINER" "nyxstrike-ctfd-db" "nyxstrike-ctfd-redis" "$CHALLENGE_CONTAINER"; do
      container_status "$c"
    done
    ;;
esac
