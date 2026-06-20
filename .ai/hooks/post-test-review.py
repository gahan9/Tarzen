# SPDX-License-Identifier: MIT
"""Post-test hook: scoped code review, configurable to save tokens.

Default mode is `security-legal` (2 checks) -- SPDX license identifier and
plaintext-secret scan.  Smaller agent context than the full standards pass.

Switch via .ai/hooks-config.json or env:
  AI_HOOK_REVIEW_MODE=full         -> all checks
  AI_HOOK_REVIEW_MODE=off          -> skip entirely
  AI_HOOK_REVIEW_VERBOSITY=verbose -> full boilerplate

Cross-platform (Windows + Linux/macOS).  Python stdlib only.

Triggered by:
  Cursor  -> afterShellExecution (pytest matcher)
  Claude  -> PostToolUse (Shell matcher)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Callable, NoReturn

import _hook_config

CheckFn = Callable[[Path, Path], "str | None"]


def _normalize(path: str) -> str:
    return path.replace("\\", "/")


def _rel(path: Path, repo_root: Path) -> str:
    return _normalize(str(path.relative_to(repo_root)))


def _check_spdx(path: Path, repo_root: Path) -> str | None:
    rel = _rel(path, repo_root)
    if not (rel.startswith("src") or rel.startswith("tests")):
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[:5]
        if any("SPDX-License-Identifier" in l for l in lines):
            return None
        return f"{rel}: Missing SPDX-License-Identifier"
    except Exception:
        return None


def _check_plaintext_secrets(path: Path, repo_root: Path) -> str | None:
    rel = _rel(path, repo_root)
    try:
        content = path.read_text(encoding="utf-8")
        pattern = re.compile(
            r"(api_key|secret|token|password)\s*=\s*['\"][^'\"]{8,}",
            re.IGNORECASE,
        )
        exclusions = {"SecretStr", "getenv", "environ", "example", "test", "mock", "fake", "dummy", "placeholder"}
        for match in pattern.finditer(content):
            ctx = content[max(0, match.start() - 50):match.end() + 50]
            if not any(exc in ctx for exc in exclusions):
                return f"{rel}: Possible plaintext secret detected"
        return None
    except Exception:
        return None


def _check_future_annotations(path: Path, repo_root: Path) -> str | None:
    rel = _rel(path, repo_root)
    if not rel.startswith("src"):
        return None
    try:
        content = path.read_text(encoding="utf-8")
        if "from __future__ import annotations" in content:
            return None
        return f"{rel}: Missing 'from __future__ import annotations'"
    except Exception:
        return None


def _check_bare_except(path: Path, repo_root: Path) -> str | None:
    rel = _rel(path, repo_root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        bare: list[str] = []
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if (s == "except:" or s.startswith("except: ")) and "noqa" not in line:
                bare.append(str(i))
        if bare:
            return f"{rel}:{','.join(bare[:3])}: Bare 'except:'"
        return None
    except Exception:
        return None


def _check_print_in_library(path: Path, repo_root: Path) -> str | None:
    rel = _rel(path, repo_root)
    if not rel.startswith("src") or path.name == "cli.py":
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        hits: list[str] = []
        for i, line in enumerate(lines, 1):
            if re.match(r"\s*print\(", line) and "noqa" not in line:
                hits.append(str(i))
        if hits:
            return f"{rel}:{','.join(hits[:3])}: print() in library code"
        return None
    except Exception:
        return None


TQ = chr(34) * 3
SQ = chr(39) * 3


def _count_non_docstring_lines(body: list[str]) -> int:
    count = 0
    docstring_delim: str | None = None
    for line in body:
        stripped = line.strip()
        if docstring_delim is None:
            if stripped.startswith(TQ) or stripped.startswith(SQ):
                delim = stripped[:3]
                # Single-line docstring: the same delimiter also closes it on
                # this line (e.g. '"""text"""').
                if len(stripped) > 3 and stripped[3:].find(delim) != -1:
                    continue
                docstring_delim = delim
                continue
            count += 1
        # Close only on the delimiter that opened the docstring; a different
        # triple quote nested in the body must not terminate it.
        elif docstring_delim in stripped:
            docstring_delim = None
    return count


def _check_function_length(path: Path, repo_root: Path) -> str | None:
    rel = _rel(path, repo_root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        violations: list[str] = []
        func_start: int | None = None
        func_name = ""
        for i, line in enumerate(lines):
            m = re.match(r"^(\s*)(async\s+)?def\s+(\w+)", line)
            if m:
                if func_start is not None:
                    body = lines[func_start + 1 : i]
                    if _count_non_docstring_lines(body) > 50:
                        violations.append(f"{func_name}()@{func_start + 1}")
                func_start = i
                func_name = m.group(3)
        # Check the final function in the file -- would be missed by the loop above.
        if func_start is not None:
            body = lines[func_start + 1 :]
            if _count_non_docstring_lines(body) > 50:
                violations.append(f"{func_name}()@{func_start + 1}")
        if violations:
            return f"{rel}: Long functions: {'; '.join(violations[:2])}"
        return None
    except Exception:
        return None


_SECURITY_LEGAL: list[CheckFn] = [_check_spdx, _check_plaintext_secrets]
_STANDARDS: list[CheckFn] = [
    _check_future_annotations, _check_bare_except,
    _check_print_in_library, _check_function_length,
]


def _emit(context: str) -> NoReturn:
    json.dump({"additional_context": context}, sys.stdout)
    sys.exit(0)


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    exit_code = data.get("exitCode", data.get("exit_code", 0))
    repo_root = _hook_config._find_repo_root()
    os.chdir(str(repo_root))

    cfg = _hook_config.load("review")
    header = _hook_config.directive(cfg, "review")

    if cfg["mode"] == "off":
        _emit("")

    checks: list[CheckFn] = list(_SECURITY_LEGAL)
    if cfg["mode"] == "full":
        checks += _STANDARDS

    changed = _hook_config.get_changed_py_files(repo_root)
    if not changed:
        _emit("" if cfg["verbosity"] == "terse" else f"{header} No files changed.")

    issues: list[str] = []
    for path in changed:
        for chk in checks:
            err = chk(path, repo_root)
            if err:
                issues.append(err)

    fc = len(changed)
    mx = int(cfg["maxIssues"])

    if not issues:
        _emit(f"{header} PASS ({fc}f, exit={exit_code}).")

    trunc = issues[:mx]
    overflow = len(issues) - len(trunc)
    bullets = "\n".join(f"  - {e}" for e in trunc)
    if overflow > 0:
        bullets += f"\n  - ... +{overflow} more"

    ask = " Ask the user before proposing fixes." if cfg["askBeforeProceeding"] else ""
    _emit(
        f"{header} CRITICAL ({len(issues)}/{fc}f, exit={exit_code}):\n"
        f"{bullets}\nFix before commit.{ask}"
    )


if __name__ == "__main__":
    main()
