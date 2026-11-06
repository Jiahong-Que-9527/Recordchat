#!/usr/bin/env bash
# [房玄龄·2026-11-03] WSL local hot-reload; only local .env is loaded.
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source ops/env.sh
set -a
source .env
set +a
export INTERNAL_API_BASE_URL=http://127.0.0.1:8000
cd frontend
exec npm run dev -- --hostname 127.0.0.1
