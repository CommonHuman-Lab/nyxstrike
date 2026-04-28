#!/usr/bin/env bash
# =============================================================================
# Lab: VulnAD — Vulnerable Active Directory (Samba4 on Linux)
#
# Spins up a Samba4 Active Directory Domain Controller inside Docker and
# then runs a Python script to populate it with the same attack paths as
# the original VulnAD PowerShell script by @safebuffer:
#
#   Attack paths seeded:
#     - Kerberoastable service accounts (weak passwords)
#     - AS-REP Roastable users (pre-auth disabled)
#     - DCSync-capable users
#     - Password in AD object description
#     - Password spraying (shared passwords)
#     - Bad ACLs (GenericAll / WriteDACL / WriteOwner etc.)
#     - DnsAdmins group abuse
#     - Default/weak passwords (Changeme123!)
#
# Ports:
#   88   — Kerberos
#   389  — LDAP
#   636  — LDAPS
#   445  — SMB
#   3268 — Global Catalog LDAP
#
# Domain: vulnad.local
# Admin:  Administrator / P@ssw0rd123!
# =============================================================================

LAB_NAME="VulnAD"
CONTAINER_NAME="nyxstrike-vulnad"
DOMAIN="vulnad.local"
DOMAIN_UPPER="VULNAD"
ADMIN_PASS="P@ssw0rd123!"
REALM="VULNAD.LOCAL"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VULNAD_DIR="${SCRIPT_DIR}/vulnad"

source "${SCRIPT_DIR}/_common.sh"
require_action "${1:-}"

# ---------------------------------------------------------------------------
# Build the Samba AD Docker image if not cached
# ---------------------------------------------------------------------------
_build_image() {
  local image_tag="nyxstrike-samba-ad:latest"
  if docker image inspect "$image_tag" &>/dev/null; then
    info "Samba AD image already built — skipping build."
  else
    info "Building Samba AD Docker image (first run, ~2 min)..."
    docker build -t "$image_tag" "${VULNAD_DIR}" --file "${VULNAD_DIR}/Dockerfile"
  fi
  echo "$image_tag"
}

# ---------------------------------------------------------------------------
# Populate AD via Python script running inside the container
# ---------------------------------------------------------------------------
_populate_ad() {
  info "Waiting for Samba AD DC to fully initialise..."
  sleep 8

  info "Copying VulnAD population script into container..."
  docker cp "${VULNAD_DIR}/populate_vulnad.py" "${CONTAINER_NAME}:/tmp/populate_vulnad.py"

  info "Running population script inside container..."
  docker exec "$CONTAINER_NAME" bash -c \
    "pip install ldap3 --quiet && python3 /tmp/populate_vulnad.py \
      --domain ${DOMAIN} \
      --admin-pass '${ADMIN_PASS}' \
      --ldap-server 127.0.0.1" \
    && good "VulnAD populated successfully." \
    || warn "Population script encountered errors (partial population may exist)."
}

# ---------------------------------------------------------------------------
case "$1" in
  start)
    header "Starting..."
    ensure_container_gone "$CONTAINER_NAME"

    IMAGE=$(_build_image)

    info "Starting Samba4 AD DC container..."
    docker run -d \
      --name "$CONTAINER_NAME" \
      --hostname "dc1.${DOMAIN}" \
      -p 88:88 \
      -p 389:389 \
      -p 636:636 \
      -p 4445:445 \
      -p 3268:3268 \
      -e DOMAIN="$DOMAIN" \
      -e DOMAIN_UPPER="$DOMAIN_UPPER" \
      -e REALM="$REALM" \
      -e ADMIN_PASS="$ADMIN_PASS" \
      --restart unless-stopped \
      "$IMAGE"

    wait_for_port 127.0.0.1 389 120

    _populate_ad

    INFO_LINES=(
      "Domain|${DOMAIN}"
      "DC hostname|dc1.${DOMAIN}"
      "Admin user|Administrator"
      "Admin pass|${ADMIN_PASS}"
      "LDAP|ldap://127.0.0.1:389"
      "Kerberos|127.0.0.1:88"
      "SMB|127.0.0.1:4445"
      "Attack paths|Kerb / ASREP / DCSync / BadACL"
      "Impacket|secretsdump / GetUserSPNs etc."
      "Stop|./vulnad.sh stop"
    )
    access_card INFO_LINES

    echo ""
    info "Quick-start attack examples:"
    info "  GetUserSPNs.py ${DOMAIN}/Administrator:'${ADMIN_PASS}' -dc-ip 127.0.0.1 -request"
    info "  GetNPUsers.py ${DOMAIN}/ -usersfile users.txt -dc-ip 127.0.0.1 -no-pass"
    info "  secretsdump.py ${DOMAIN}/dcsync_user@127.0.0.1"
    info "  bloodhound-python -u Administrator -p '${ADMIN_PASS}' -d ${DOMAIN} -ns 127.0.0.1 -c All"
    echo ""

    good "VulnAD is up!"
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
    if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
      info "Domain: ${DOMAIN}"
      info "LDAP:   ldap://127.0.0.1:389"
    fi
    ;;
esac
