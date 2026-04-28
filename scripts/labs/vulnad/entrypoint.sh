#!/usr/bin/env bash
# =============================================================================
# Samba4 AD DC entrypoint — provisions the domain on first run, then starts
# the samba daemon in the foreground.
# =============================================================================
set -e

DOMAIN="${DOMAIN:-vulnad.local}"
REALM="${REALM:-VULNAD.LOCAL}"
DOMAIN_UPPER="${DOMAIN_UPPER:-VULNAD}"
ADMIN_PASS="${ADMIN_PASS:-P@ssw0rd123!}"
DC_HOSTNAME="dc1"

echo "[*] Configuring hostname..."
hostname "${DC_HOSTNAME}.${DOMAIN}"

# Only provision if smb.conf doesn't exist yet (first boot)
if [ ! -f /etc/samba/smb.conf ]; then
    echo "[*] Provisioning Samba4 AD DC for domain: ${DOMAIN}"

    samba-tool domain provision \
        --use-rfc2307 \
        --realm="${REALM}" \
        --domain="${DOMAIN_UPPER}" \
        --server-role=dc \
        --dns-backend=SAMBA_INTERNAL \
        --adminpass="${ADMIN_PASS}" \
        --host-name="${DC_HOSTNAME}" \
        --option="interfaces=lo eth0" \
        --option="bind interfaces only=yes"

    echo "[+] Samba4 AD domain provisioned."

    # Configure Kerberos
    cp /var/lib/samba/private/krb5.conf /etc/krb5.conf

    # Ensure LDAP is accessible on all interfaces
    sed -i 's/\[global\]/[global]\n\tldap server require strong auth = no/' /etc/samba/smb.conf
fi

echo "[*] Starting Samba AD DC..."
exec samba --foreground --no-process-group
