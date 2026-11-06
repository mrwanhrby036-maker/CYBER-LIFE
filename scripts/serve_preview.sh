#!/usr/bin/env bash
# Sandbox preview only. Starts the API + static frontend on 0.0.0.0:8000.
#
# Production does NOT use this script: production requires
# CYBERLIFE_ENV=production + Firebase auth/storage (see docs/DEPLOYMENT.md).
#
# The preview needs a way to sign in before Firebase is configured, so it uses
# an isolated local store with EPHEMERAL random credentials generated on first
# run and kept in .data/ (git-ignored). Credentials are never shown in the UI
# and are never committed. Delete .data/preview-credentials.json to rotate.
set -euo pipefail
cd "$(dirname "$0")/../backend"

mkdir -p .data
CRED_FILE=.data/preview-credentials.json

if [ ! -f "$CRED_FILE" ]; then
  python - <<'PY'
import json, secrets, pathlib
creds = {
    "student_email": "student@cyberlife.local",
    "student_password": secrets.token_urlsafe(18),
    "admin_email": "admin@cyberlife.local",
    "admin_password": secrets.token_urlsafe(18),
}
pathlib.Path(".data/preview-credentials.json").write_text(json.dumps(creds, indent=2), encoding="utf-8")
PY
  echo "Generated fresh ephemeral preview credentials in backend/.data/preview-credentials.json"
fi

read -r STUDENT_PW ADMIN_PW LOCAL_SECRET <<<"$(python - <<'PY'
import json, secrets
c = json.load(open(".data/preview-credentials.json", encoding="utf-8"))
print(c["student_password"], c["admin_password"], secrets.token_urlsafe(32))
PY
)"

export CYBERLIFE_ENV=development
export CYBERLIFE_AUTH_MODE=local
export CYBERLIFE_STORAGE_MODE=local
export CYBERLIFE_SERVE_FRONTEND=true
export CYBERLIFE_ENABLE_LOCAL_DEV=true
export CYBERLIFE_DEV_STUDENT_PASSWORD="$STUDENT_PW"
export CYBERLIFE_DEV_ADMIN_PASSWORD="$ADMIN_PW"
export CYBERLIFE_LOCAL_SECRET="$LOCAL_SECRET"
export CYBERLIFE_CORS_ORIGIN_REGEX='https://[a-z0-9-]+\.e2b\.app'

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
