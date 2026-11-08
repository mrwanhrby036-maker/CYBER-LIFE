"""Vercel ASGI entrypoint for the existing CYBER LIFE FastAPI application."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Keep all API routes, authorization, Firebase verification, and business logic in
# backend/app. This file is only the Vercel Python Runtime adapter.
from app.main import app  # noqa: E402

__all__ = ["app"]
