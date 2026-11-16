#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r backend/requirements.txt
if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install)
fi
cd "$ROOT/backend"
uvicorn app.main:app --host 0.0.0.0 --port 8010 &
BACK_PID=$!
trap 'kill $BACK_PID 2>/dev/null || true' EXIT
cd "$ROOT/frontend"
npm run dev
