# SPDX-License-Identifier: MIT
"""Pre-session hook: verify uv environment is configured and active.

Ensures all agent work runs inside a uv-managed virtual environment.
Checks uv availability, creates .venv if missing, reports active Python.

Cross-platform (Windows + Linux/macOS).  Python stdlib only.

Triggered by:
  Cursor  -> sessionStart, beforeShellExecution (python/pytest commands)
  Claude  -> PreToolUse (first invocation guard via session flag)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import _hook_config


def main() -> None:
    try:
        sys.stdin.read()
    except Exception:
        pass

    repo_root = _hook_config._find_repo_root()
    os.chdir(str(repo_root))

    uv_path = shutil.which("uv")
    if not uv_path:
        json.dump({
            "decision": "block",
            "reason": (
                "uv is not installed or not on PATH. "
                "Install via: pip install uv (or pipx install uv)"
            ),
        }, sys.stdout)
        sys.exit(2)

    venv_dir = repo_root / ".venv"
    if not venv_dir.exists():
        try:
            subprocess.run(
                [uv_path, "sync", "--quiet"],
                cwd=str(repo_root), capture_output=True, timeout=120,
            )
        except Exception:
            try:
                subprocess.run(
                    [uv_path, "venv", ".venv", "--quiet"],
                    cwd=str(repo_root), capture_output=True, timeout=60,
                )
            except Exception:
                json.dump({
                    "decision": "block",
                    "reason": "Failed to create .venv. Run 'uv sync' manually.",
                }, sys.stdout)
                sys.exit(2)

    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if not venv_python.exists():
        json.dump({
            "decision": "block",
            "reason": (
                f"Cannot locate Python in .venv at {venv_python}. "
                "Run 'uv sync' to recreate the environment."
            ),
        }, sys.stdout)
        sys.exit(2)

    try:
        ver = subprocess.check_output(
            [str(venv_python), "--version"], timeout=10, text=True,
        ).strip()
    except Exception:
        ver = "unknown"

    json.dump({
        "decision": "allow",
        "additional_context": (
            f"Environment: uv-managed .venv active at {venv_dir}. "
            f"{ver}. Use 'uv run' prefix for all Python commands to ensure "
            "dependency isolation."
        ),
    }, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
