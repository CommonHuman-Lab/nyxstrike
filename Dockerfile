# NyxStrike — Kali Linux rolling base image
FROM kalilinux/kali-rolling:latest

# Avoid interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# ── System basics + build deps ─────────────────────────────────────────────────
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gcc \
    git \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    sudo \
    wget \
 && rm -rf /var/lib/apt/lists/*

# ── Install all NyxStrike tool dependencies via nyxstrike.sh -t ──────────────
WORKDIR /opt/nyxstrike

# Copy the repo into the image
COPY . .

# Run tool install (apt/cargo tools only).
RUN apt-get update -qq && \
    chmod +x nyxstrike.sh && \
    bash nyxstrike.sh -t && \
    rm -rf /var/lib/apt/lists/*

# ── Runtime config ─────────────────────────────────────────────────────────────
# Bind to 0.0.0.0 inside the container so the mapped port is reachable
ENV NYXSTRIKE_HOST=0.0.0.0
ENV NYXSTRIKE_PORT=8888

EXPOSE 8888

# ── Entrypoint ─────────────────────────────────────────────────────────────────
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["/opt/nyxstrike/docker-entrypoint.sh"]
