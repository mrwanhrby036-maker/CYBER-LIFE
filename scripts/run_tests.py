#!/usr/bin/env python3
"""Run the backend, frontend, JavaScript syntax, and line-count checks."""
from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, command: list[str], cwd: Path) -> None:
    print(f"== {label} ==", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    run("Backend tests", [sys.executable, "-m", "pytest", "tests", "-q"], ROOT / "backend")
    npm = shutil.which("npm")
    if not npm:
        raise SystemExit("npm is required to run the frontend tests")
    frontend_tests = ROOT / "tests-frontend"
    if not (frontend_tests / "node_modules").exists():
        run("Install frontend test dependencies", [npm, "install", "--no-package-lock"], frontend_tests)
    run("Frontend tests", [npm, "test"], frontend_tests)

    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js is required for JavaScript syntax checks")
    print("== JavaScript syntax check ==", flush=True)
    files = sorted((ROOT / "frontend").rglob("*.js"))
    for source in files:
        subprocess.run([node, "--check", str(source)], cwd=ROOT, check=True)
    run("Line count", [sys.executable, "scripts/count_lines.py"], ROOT)


if __name__ == "__main__":
    main()
