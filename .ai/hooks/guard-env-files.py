# SPDX-License-Identifier: MIT
"""Guard hook: block all agent access to .env files.

Prevents reading, writing, or displaying .env file contents.
Protects API keys, tokens, and secrets from accidental exposure.

Cross-platform (Windows + Linux/macOS).  Python stdlib only.

Triggered by:
  Cursor  -> beforeReadFile, preToolUse (Read|Write)
  Claude  -> PreToolUse (Read|Write matcher)
"""
from __future__ import annotations

import json
import re
import sys

_ENV_PATTERNS = [
    re.compile(r"^\.env$", re.IGNORECASE),
    re.compile(r"^\.env\..+$", re.IGNORECASE),
    re.compile(r"^env$", re.IGNORECASE),
]


def _extract_path(data: dict) -> str:
    for key_path in [
        ("path",),
        ("filePath",),
        ("input", "path"),
        ("arguments", "path"),
        ("input", "filePath"),
    ]:
        obj = data
        for k in key_path:
            if isinstance(obj, dict):
                obj = obj.get(k, "")
            else:
                obj = ""
                break
        if obj:
            return str(obj)
    return ""


def _is_env_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1] if "/" in normalized else normalized
    if basename.lower() == ".env.example":
        return False
    return any(p.match(basename) for p in _ENV_PATTERNS)


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    path = _extract_path(data)

    if _is_env_file(path):
        json.dump({
            "permission": "deny",
            "user_message": (
                f"BLOCKED: Agent attempted to access '{path}'. "
                ".env files contain secrets and are strictly off-limits."
            ),
            "agent_message": (
                "Access to .env files is prohibited by repository security policy. "
                "Use environment variables or a settings loader for configuration. "
                "Never read, write, display, or reference .env file contents."
            ),
        }, sys.stdout)
        sys.exit(0)

    json.dump({"permission": "allow"}, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
