# syntax=docker/dockerfile:1

# ── Stage 1: Build frontend ──────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --frozen-lockfile 2>/dev/null || npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Final image (s6-overlay + Python + built frontend) ──
FROM python:3.12-alpine

ARG S6_OVERLAY_VERSION=3.2.0.2
ARG TARGETARCH

# Install s6-overlay (map Docker arch names → s6 asset names)
RUN case "${TARGETARCH}" in \
      amd64) S6_ARCH=x86_64  ;; \
      arm64) S6_ARCH=aarch64 ;; \
      arm)   S6_ARCH=armhf   ;; \
      *)     S6_ARCH="${TARGETARCH}" ;; \
    esac && \
    wget -q -O /tmp/s6-noarch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-noarch.tar.xz && rm /tmp/s6-noarch.tar.xz && \
    wget -q -O /tmp/s6-arch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-arch.tar.xz && rm /tmp/s6-arch.tar.xz

# System deps
RUN apk add --no-cache shadow bash curl

# Create abc user (linuxserver convention)
RUN groupadd -g 1000 abc && \
    useradd -u 1000 -g abc -d /config -s /bin/false abc

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies
WORKDIR /app
COPY pyproject.toml .
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy backend app code
COPY app ./app

# Copy built frontend (Vite outputs to static/ at the project root)
COPY --from=frontend-build /static ./static

# ── s6 service definitions ───────────────────────────────

# Init script: set PUID/PGID
RUN mkdir -p /etc/s6-overlay/s6-rc.d/init-perms/dependencies.d
COPY <<'EOF' /etc/s6-overlay/s6-rc.d/init-perms/type
oneshot
EOF
COPY <<'SCRIPT' /etc/s6-overlay/s6-rc.d/init-perms/up
#!/command/execlineb -P
foreground {
  if { s6-test -n ${PUID} }
  foreground { usermod -o -u ${PUID} abc }
  foreground { groupmod -o -g ${PGID} abc }
}
foreground { chown -R abc:abc /config }
SCRIPT
RUN touch /etc/s6-overlay/s6-rc.d/init-perms/dependencies.d/base

# Printarr service
RUN mkdir -p /etc/s6-overlay/s6-rc.d/printarr/dependencies.d
COPY <<'EOF' /etc/s6-overlay/s6-rc.d/printarr/type
longrun
EOF
COPY <<'SCRIPT' /etc/s6-overlay/s6-rc.d/printarr/run
#!/command/execlineb -P
s6-setuidgid abc
cd /app
/usr/local/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level info
SCRIPT
RUN touch /etc/s6-overlay/s6-rc.d/printarr/dependencies.d/init-perms

# Wire up to s6 bundle
RUN mkdir -p /etc/s6-overlay/s6-rc.d/user/contents.d && \
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/init-perms && \
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/printarr

# Create directories
RUN mkdir -p /config && chown -R abc:abc /config

ENV PUID=1000
ENV PGID=1000
ENV TZ=America/New_York
ENV DATA_DIR=/config
ENV PORT=6969

EXPOSE 6969
VOLUME ["/config"]

ENTRYPOINT ["/init"]
