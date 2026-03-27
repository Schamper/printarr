# Printarr development tasks
# Requires: just (https://github.com/casey/just), uv, node/npm

default: help

help:
    @just --list

# ── Install ──────────────────────────────────────────────

# Install all dependencies (backend + frontend)
install:
    uv sync
    cd frontend && npm install

# ── Dev ──────────────────────────────────────────────────

# Run the backend dev server (with reload)
dev:
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 6969

# Run the Vite frontend dev server (proxies API to :6969)
dev-frontend:
    cd frontend && npm run dev

# Build frontend assets into static/
build-frontend:
    cd frontend && npm run build

# Build everything (frontend + ready to run)
build: build-frontend
    uv sync

run: build dev

# ── Lint / Format ────────────────────────────────────────

# Check Python linting + formatting
lint:
    uv run ruff check app/
    uv run ruff format --check app/

# Fix Python lint issues and format
format:
    uv run ruff check --fix app/
    uv run ruff format app/

# Type-check frontend
typecheck:
    cd frontend && npm run tsc -- --noEmit 2>/dev/null || npx tsc --noEmit

# ── Test ─────────────────────────────────────────────────

# Run backend tests (if any)
test:
    uv run pytest -q

# ── Docker ───────────────────────────────────────────────

# Build the Docker image
docker-build tag="printarr:latest":
    docker build -t {{tag}} .

# Run with Docker Compose
up:
    docker compose up

# Rebuild frontend and restart local dev server
dev-rebuild: build-frontend dev

# Run in background
up-detached:
    docker compose up -d

# Stop Docker Compose
down:
    docker compose down

# ── DB ───────────────────────────────────────────────────

# Inspect the live SQLite database
db:
    sqlite3 config/printarr.db

# Show all library models
db-library:
    sqlite3 config/printarr.db "SELECT id, source, name, tags FROM library_models ORDER BY added_at DESC"

# Show all tags in use
db-tags:
    sqlite3 config/printarr.db "SELECT DISTINCT value FROM library_models, json_each(library_models.tags) ORDER BY value"

# Show queue
db-queue:
    sqlite3 config/printarr.db "SELECT q.id, l.name, q.copies, q.filament_type FROM queue_items q JOIN library_models l ON l.id = q.library_model_id ORDER BY q.sort_order"
