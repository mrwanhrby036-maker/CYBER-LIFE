#!/usr/bin/env python3
"""Start an isolated local preview with randomly generated development credentials."""
from __future__ import annotations
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DATA = BACKEND / ".data"
CREDENTIALS = DATA / "preview-credentials.json"


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    if not CREDENTIALS.exists():
        values = {
            "student_email": "student@cyberlife.local",
            "student_password": secrets.token_urlsafe(18),
            "admin_email": "admin@cyberlife.local",
            "admin_password": secrets.token_urlsafe(18),
        }
        CREDENTIALS.write_text(json.dumps(values, indent=2), encoding="utf-8")
        CREDENTIALS.chmod(0o600)
        print("Generated ephemeral preview credentials in backend/.data/preview-credentials.json")

    credentials = json.loads(CREDENTIALS.read_text(encoding="utf-8"))
    environment = os.environ.copy()
    environment.update({
        "CYBERLIFE_ENV": "development",
        "CYBERLIFE_AUTH_MODE": "local",
        "CYBERLIFE_STORAGE_MODE": "local",
        "CYBERLIFE_SERVE_FRONTEND": "true",
        "CYBERLIFE_ENABLE_LOCAL_DEV": "true",
        "CYBERLIFE_DEV_STUDENT_PASSWORD": credentials["student_password"],
        "CYBERLIFE_DEV_ADMIN_PASSWORD": credentials["admin_password"],
        "CYBERLIFE_LOCAL_SECRET": secrets.token_urlsafe(32),
        "CYBERLIFE_CORS_ORIGIN_REGEX": r"https://[a-z0-9-]+\.e2b\.app",
    })
    print("Starting the isolated preview API and frontend on 0.0.0.0:8000", flush=True)
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND, env=environment, check=True,
    )


if __name__ == "__main__":
    main()
