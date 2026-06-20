#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Create tool-specific adapter links from .ai/ (canonical) to tool directories.

Cursor auto-discovers skills at .cursor/skills/*/SKILL.md. Since canonical
skills live in .ai/skills/, this script creates directory junctions (Windows)
or symlinks (Unix) so Cursor sees them without file duplication.

Run once after clone, or after adding a new skill to .ai/skills/:
    python .ai/setup-links.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    ai_skills = repo_root / ".ai" / "skills"
    cursor_skills = repo_root / ".cursor" / "skills"

    if not ai_skills.is_dir():
        print(f"No .ai/skills/ directory at {ai_skills}")
        sys.exit(1)

    cursor_skills.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(ai_skills.iterdir()):
        if not skill_dir.is_dir():
            continue
        link = cursor_skills / skill_dir.name
        if link.exists() or link.is_symlink():
            continue

        target = skill_dir.resolve()
        if sys.platform == "win32":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
            )
        else:
            link.symlink_to(target)

        print(f"  {link.name} -> {target}")

    print("Cursor skill links ready.")


if __name__ == "__main__":
    main()
