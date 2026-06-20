# SPDX-License-Identifier: MIT
"""Background lint hook: ruff + mypy on changed lines, configurable.

Runs after Python file edits.  Reports only NEW lint/type issues on
modified lines.  Non-blocking: always exits 0.

Honors .ai/hooks-config.json:
  lint.enabled    -> false to skip (zero token cost)
  lint.verbosity  -> terse caps output
  lint.maxIssues  -> per-tool truncation

Cross-platform.  Requires uv on PATH.

Triggered by:
  Cursor  -> afterFileEdit (.py matcher)
  Claude  -> PostToolUse (Write matcher on .py files)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import _hook_config


def _normalize(path: str) -> str:
    return path.replace("\\", "/")


def _get_changed_lines(repo_root: Path) -> dict[str, set[int]]:
    result: dict[str, set[int]] = {}
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--unified=0"],
            cwd=str(repo_root), text=True, timeout=10,
        )
    except Exception:
        return result
    current_file = None
    for line in diff.splitlines():
        m = re.match(r"^\+\+\+ b/(.*)", line)
        if m:
            current_file = _normalize(m.group(1))
            result.setdefault(current_file, set())
            continue
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m and current_file:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) else 1
            result[current_file].update(range(start, start + count))
    return result


def _run_tool(
    tool_args: list[str], files: list[str], repo_root: Path,
    changed_lines: dict[str, set[int]], timeout: int = 30,
) -> list[str]:
    uv = shutil.which("uv")
    if not uv:
        return []
    issues: list[str] = []
    for f in files:
        try:
            proc = subprocess.run(
                [uv, "run"] + tool_args + [f],
                cwd=str(repo_root), text=True, timeout=timeout, capture_output=True,
            )
            out = proc.stdout or ""
        except Exception:
            continue
        if "Success" in out:
            continue
        file_lines = changed_lines.get(f, set())
        for line in out.splitlines():
            if not line.strip():
                continue
            parts = line.split(":")
            if len(parts) >= 2:
                try:
                    lineno = int(parts[1])
                    if not file_lines or lineno in file_lines:
                        issues.append(line.strip())
                except ValueError:
                    pass
    return issues


def _emit(context: str) -> NoReturn:
    json.dump({"additional_context": context}, sys.stdout)
    sys.exit(0)


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    edited_file = ""
    for key in ("path", "filePath"):
        if key in data:
            edited_file = data[key]
            break
    if not edited_file:
        inp = data.get("input", {})
        if isinstance(inp, dict):
            edited_file = inp.get("path", "")

    if not edited_file.endswith(".py"):
        _emit("")

    repo_root = _hook_config._find_repo_root()
    os.chdir(str(repo_root))

    cfg = _hook_config.load("lint")
    header = _hook_config.directive(cfg, "lint")
    if not cfg["enabled"]:
        _emit("")

    changed_lines = _get_changed_lines(repo_root)
    changed_paths = _hook_config.get_changed_py_files(repo_root)
    changed_files = [_normalize(str(p.relative_to(repo_root))) for p in changed_paths]

    if edited_file:
        try:
            rel = _normalize(str(Path(edited_file).resolve().relative_to(repo_root)))
        except ValueError:
            rel = _normalize(edited_file)
        if rel not in changed_files and (repo_root / rel).exists():
            changed_files.append(rel)
            changed_files.sort()

    if not changed_files:
        _emit("")

    ruff = _run_tool(["ruff", "check", "--output-format=text"], changed_files, repo_root, changed_lines)
    src_files = [f for f in changed_files if f.startswith("src/")]
    mypy = _run_tool(["mypy", "--no-error-summary"], src_files, repo_root, changed_lines, timeout=60)
    mx = int(cfg["maxIssues"])

    parts: list[str] = []
    for label, items in [("RUFF", ruff), ("MYPY", mypy)]:
        if items:
            t = items[:mx]
            sfx = f" (+{len(items) - len(t)})" if len(items) > mx else ""
            parts.append(f"{label}{sfx}:\n" + "\n".join(f"  {i}" for i in t))

    if not parts:
        _emit(f"{header} PASS ({len(changed_files)}f).")

    body = "\n\n".join(parts)
    _emit(f"{header} ({len(changed_files)}f):\n{body}\nFix on affected lines.")


if __name__ == "__main__":
    main()
