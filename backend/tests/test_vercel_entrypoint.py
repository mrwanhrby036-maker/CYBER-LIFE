import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_vercel_fastapi_entrypoint_uses_existing_backend_app():
    backend = str(ROOT / "backend")
    spec = importlib.util.spec_from_file_location("cyberlife_vercel_entry", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert backend in sys.path
    from app.main import app
    assert module.app is app
    paths = set(module.app.openapi()["paths"])
    assert "/api/health" in paths
    assert "/api/auth/me" in paths


def test_vercel_config_keeps_static_frontend_and_includes_runtime_dependencies():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert config["outputDirectory"] == "frontend"
    assert "main.py" in config["functions"]
    included = config["functions"]["main.py"]["includeFiles"]
    assert isinstance(included, str)
    assert "backend/app/**/*.py" in included
    assert "content/**/*.json" in included
    assert config["functions"]["main.py"]["maxDuration"] > 0
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "fastapi" in requirements
    assert "firebase-admin" in requirements
