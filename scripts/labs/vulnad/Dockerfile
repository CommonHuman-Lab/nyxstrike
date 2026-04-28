# =============================================================================
# NyxStrike VulnAD — Samba4 Active Directory Domain Controller
# Builds a lightweight Samba4 AD DC image ready for VulnAD population.
# =============================================================================
FROM ubuntu:22.04

LABEL maintainer="NyxStrike"
LABEL description="Samba4 AD DC for VulnAD lab"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        samba \
        samba-ad-dc \
        krb5-user \
        winbind \
        dnsutils \
        python3 \
        python3-pip \
        python3-samba \
        net-tools \
        iputils-ping \
        curl \
        ldap-utils \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Remove default Samba config so we can provision fresh
RUN rm -f /etc/samba/smb.conf && \
    rm -rf /var/lib/samba/* && \
    mkdir -p /var/lib/samba/private

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Kerberos, LDAP, LDAPS, SMB, Global Catalog
EXPOSE 88 389 636 445 3268

ENTRYPOINT ["/entrypoint.sh"]
