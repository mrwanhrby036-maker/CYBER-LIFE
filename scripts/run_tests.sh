#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== Backend tests =="
(cd backend && python -m pytest tests -q)
echo "== Frontend tests =="
(cd tests-frontend && npm test)
echo "== JS syntax check =="
find frontend -name '*.js' -not -path '*/node_modules/*' -print0 | xargs -0 -n1 node --check
echo "== Line count =="
python scripts/count_lines.py
