#!/usr/bin/env bash
set -euo pipefail

# Local dev helper: build frontend, start backend
# Requires: Python 3.11+, Node 18+

HERE="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$HERE/frontend"
BACKEND_DIR="$HERE/backend"
DIST_DIR="$FRONTEND_DIR/dist"

echo "[1/3] Installing backend deps"
python -m venv "$HERE/.venv"
source "$HERE/.venv/bin/activate"
pip install -U pip
pip install -r "$BACKEND_DIR/requirements.txt"

echo "[2/3] Building frontend"
pushd "$FRONTEND_DIR" >/dev/null
npm install
npm run build
popd >/dev/null

export APP_FRONTEND_DIST_DIR="$DIST_DIR"
export APP_OUTPUT_DIR_BASE="$HERE/data"
mkdir -p "$APP_OUTPUT_DIR_BASE"

echo "[3/3] Starting backend on http://localhost:8080"
python -m uvicorn app.main:app --app-dir "$BACKEND_DIR" --host 0.0.0.0 --port 8080 --reload
