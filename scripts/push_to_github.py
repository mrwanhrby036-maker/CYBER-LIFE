#!/usr/bin/env python3
"""Safely push the current work branch without renaming or replacing the default branch."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TRACKED = (".env", "service-account", ".data/", "credentials", "signing-key")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("github_user", nargs="?", help="used only if no origin remote exists")
    args = parser.parse_args()
    branch = git("branch", "--show-current")
    if not branch or branch in {"main", "master"}:
        raise SystemExit("Refusing to push the default branch. Switch to a work branch first.")

    tracked = git("ls-files").splitlines()
    leaks = [path for path in tracked if any(mark in path.lower() for mark in FORBIDDEN_TRACKED)]
    if leaks:
        print("رفض الرفع — ملفات حساسة متتبعة:", file=sys.stderr)
        print("\n".join(leaks), file=sys.stderr)
        raise SystemExit(1)

    remote = git("remote", "get-url", "origin", check=False)
    if not remote:
        if not args.github_user:
            raise SystemExit("No origin remote. Supply a GitHub username or configure origin first.")
        git("remote", "add", "origin", f"https://github.com/{args.github_user}/CYBER-LIFE.git")
    print(f"Pushing current branch {branch!r} to origin; no branch rename or default-branch push.")
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=ROOT, check=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
