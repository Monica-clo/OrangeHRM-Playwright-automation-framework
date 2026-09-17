#!/usr/bin/env bash
# Usage: ./run_tests.sh [api|ui|hybrid] [extra pytest options]
set -euo pipefail
cd "$(dirname "$0")"
[ -f .venv/bin/activate ] && source .venv/bin/activate
case "${1:-}" in
  api|ui|hybrid) suite="$1"; shift; python -m pytest -m "$suite" "$@" ;;
  *) python -m pytest "$@" ;;
esac
