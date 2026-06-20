#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Cross-platform hook runner for both Cursor and Claude Code.

Allows hooks.json / settings.json to use a single command format:
  "command": "uv run python -u .ai/hooks/run-hook.py <hook-name>"

This avoids platform-specific python3/python issues and provides a
uniform entry point for both toolchains.  Hooks loaded via this runner
can use `import _hook_config` without extra setup because this module
inserts the hooks directory into sys.path before loading the hook.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: run-hook.py <hook-name>\n")
        return 1

    hook_name = sys.argv[1]
    if not hook_name.replace("-", "_").replace("_", "").isalnum() or ".." in hook_name:
        sys.stderr.write(f"Invalid hook name: {hook_name}\n")
        return 1

    hooks_dir = Path(__file__).resolve().parent
    hook_path = hooks_dir / f"{hook_name}.py"

    if not hook_path.exists():
        sys.stderr.write(f"Hook not found: {hook_path}\n")
        return 1

    # Ensure _hook_config (and other sibling modules) are importable.
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))

    spec = importlib.util.spec_from_file_location(hook_name, hook_path)
    if spec is None or spec.loader is None:
        sys.stderr.write(f"Cannot load hook: {hook_path}\n")
        return 1

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "main"):
        module.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
