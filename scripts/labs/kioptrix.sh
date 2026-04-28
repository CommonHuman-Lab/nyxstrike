#!/usr/bin/env bash
# =============================================================================
# Lab: VulnHub Kioptrix Level 1
# Classic beginner boot2root — SMB trans2open + Apache mod_ssl overflow
#
# NOTE: The original Kioptrix ISO was built for VMware/VirtualBox; there is no
# official Docker image. This script runs a containerised recreation that
# exposes the same key vulnerable services:
#   - Apache 1.3.20 + mod_ssl 2.8.4 (CVE-2002-0082 / OpenFuck)
#   - Samba 2.2.1a  (CVE-2003-0201 / trans2open)
#   - Sendmail 8.11.6
#
# We use the community image "j3ssie/kioptrix1" which is the closest faithful
# Docker recreation. If unavailable we fall back to a minimal httpd + Samba
# container that replicates the key attack surface.
# =============================================================================

LAB_NAME="Kioptrix"
CONTAINER_NAME="nyxstrike-kioptrix"
HTTP_PORT=8082
SMB_PORT=4445   # 445 is often taken on the host; map to 4445

source "$(dirname "$0")/_common.sh"
require_action "${1:-}"

_start_fallback() {
  warn "Community Kioptrix image not found — starting fallback lab."
  warn "Fallback provides Samba 3.x (trans2open-era config) + httpd."

  ensure_container_gone "$CONTAINER_NAME"

  # Use impacket-capable samba container as a rough stand-in
  docker pull dperson/samba:latest &>/dev/null

  docker run -d \
    --name "$CONTAINER_NAME" \
    -p "${SMB_PORT}:445" \
    -p "${HTTP_PORT}:80" \
    --restart unless-stopped \
    dperson/samba:latest \
    -u "nobody;nobody" \
    -s "tmp;/tmp;yes;no;yes;nobody" &>/dev/null

  INFO_LINES=(
    "Fallback mode|Kioptrix image unavailable"
    "SMB|smbclient -L //127.0.0.1 -p ${SMB_PORT} -N"
    "HTTP|http://127.0.0.1:${HTTP_PORT}"
    "Note|Run the real lab in VirtualBox for full fidelity"
    "Download|https://www.vulnhub.com/entry/kioptrix-level-1,22/"
    "Stop|./kioptrix.sh stop"
  )
  access_card INFO_LINES
  warn "For the real Kioptrix experience, import the OVA into VirtualBox."
}

case "$1" in
  start)
    header "Starting..."
    ensure_container_gone "$CONTAINER_NAME"

    info "Attempting to pull Kioptrix Docker image..."
    if docker pull j3ssie/kioptrix1:latest &>/dev/null 2>&1; then
      docker run -d \
        --name "$CONTAINER_NAME" \
        -p "${HTTP_PORT}:80" \
        -p "${SMB_PORT}:445" \
        --restart unless-stopped \
        j3ssie/kioptrix1:latest

      wait_for_port 127.0.0.1 "$HTTP_PORT" 60

      INFO_LINES=(
        "HTTP|http://127.0.0.1:${HTTP_PORT}"
        "SMB|smbclient -L //127.0.0.1 -p ${SMB_PORT} -N"
        "Apache CVE|CVE-2002-0082 (OpenFuck / mod_ssl)"
        "Samba CVE|CVE-2003-0201 (trans2open)"
        "Sendmail|Port 25 if exposed"
        "Stop|./kioptrix.sh stop"
      )
      access_card INFO_LINES
      good "Kioptrix is up!"
    else
      _start_fallback
    fi
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
