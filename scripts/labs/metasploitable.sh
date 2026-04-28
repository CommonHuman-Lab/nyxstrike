#!/usr/bin/env bash
# =============================================================================
# Lab: Metasploitable2
# Linux VM image with intentionally vulnerable services
# Image: tleemcjr/metasploitable2
# Services: FTP(21) SSH(22) Telnet(23) SMTP(25) HTTP(80) SMB(445) MySQL(3306)
#           PostgreSQL(5432) VNC(5900) and many more
# =============================================================================

LAB_NAME="Metasploitable2"
CONTAINER_NAME="nyxstrike-metasploitable"

# Port mappings: host_port:container_port
declare -A PORTS=(
  [21]=21     # FTP  (vsftpd 2.3.4 backdoor)
  [2222]=22   # SSH  (use 2222 to avoid conflict with host SSH)
  [23]=23     # Telnet
  [25]=25     # SMTP
  [8081]=80   # HTTP (use 8081 to avoid conflict)
  [139]=139   # NetBIOS
  [445]=445   # SMB  (Samba usermap_script)
  [3306]=3306 # MySQL (no auth root)
  [5432]=5432 # PostgreSQL
  [5900]=5900 # VNC  (no auth)
  [6667]=6667 # IRC  (UnrealIRCd backdoor)
)

source "$(dirname "$0")/_common.sh"
require_action "${1:-}"

case "$1" in
  start)
    header "Starting..."
    ensure_container_gone "$CONTAINER_NAME"
    info "Pulling image tleemcjr/metasploitable2..."
    docker pull tleemcjr/metasploitable2:latest

    # Build port flags
    PORT_FLAGS=""
    for h in "${!PORTS[@]}"; do
      PORT_FLAGS="$PORT_FLAGS -p ${h}:${PORTS[$h]}"
    done

    # shellcheck disable=SC2086
    docker run -d \
      --name "$CONTAINER_NAME" \
      $PORT_FLAGS \
      --restart unless-stopped \
      tleemcjr/metasploitable2:latest \
      sh -c "/bin/services.sh && sleep infinity"

    wait_for_port 127.0.0.1 8081 90

    INFO_LINES=(
      "HTTP|http://127.0.0.1:8081"
      "SSH|ssh msfadmin@127.0.0.1 -p 2222"
      "SSH creds|msfadmin / msfadmin"
      "FTP|ftp 127.0.0.1 21 (anonymous OK)"
      "MySQL|mysql -h 127.0.0.1 -u root (no pass)"
      "SMB|smbclient -L //127.0.0.1"
      "VNC|vncviewer 127.0.0.1:5900 (no pass)"
      "Stop|./metasploitable.sh stop"
    )
    access_card INFO_LINES
    warn "This container is INTENTIONALLY vulnerable. Isolate your network!"
    good "Metasploitable2 is up!"
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
