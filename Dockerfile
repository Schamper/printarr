# syntax=docker/dockerfile:1

# ── Stage 1: Build frontend ──────────────────────────────
FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --frozen-lockfile 2>/dev/null || npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Final image ─────────────────────────────────
FROM python:3.13-alpine

# System deps
RUN apk add --no-cache shadow bash

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

# Entrypoint script: handle PUID/PGID then exec as abc
RUN printf '#!/bin/bash\nset -e\n\nPUID="${PUID:-1000}"\nPGID="${PGID:-1000}"\n\nusermod -o -u "$PUID" abc 2>/dev/null\ngroupmod -o -g "$PGID" abc 2>/dev/null\nchown -R abc:abc /config\n\ncd /app\nexec su-exec abc python -m uvicorn app.main:app \\\n  --host 0.0.0.0 --port 6969 --log-level info\n' \
    > /entrypoint.sh && chmod +x /entrypoint.sh

RUN apk add --no-cache su-exec

# Create directories
RUN mkdir -p /config && chown -R abc:abc /config

ENV DATA_DIR=/config
ENV TZ=UTC

EXPOSE 6969
VOLUME ["/config"]

ENTRYPOINT ["/entrypoint.sh"]
