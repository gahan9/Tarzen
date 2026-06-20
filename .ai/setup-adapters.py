#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate platform-specific adapter files from canonical .ai/ definitions.

Reads the four primitives from `.ai/` (rules, hooks, skills, subagents) and
emits adapters for: Cursor, Claude Code, GitHub Copilot, OpenAI Codex, and
Google Antigravity.

Usage:
    python .ai/setup-adapters.py [--dry-run] [--platform PLATFORM]

Platforms: cursor, claude, copilot, codex, antigravity, all (default)

PyYAML is used when available for robust frontmatter parsing; a minimal
stdlib-only fallback parser handles the common cases otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - fallback path
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_DIR = REPO_ROOT / ".ai"
SKILLS_DIR = AI_DIR / "skills"
SUBAGENTS_DIR = AI_DIR / "subagents"
RULES_DIR = AI_DIR / "rules"

HOOK_CMD = "uv run python -u .ai/hooks/run-hook.py"


# --------------------------------------------------------------------------- #
# Frontmatter parsing
# --------------------------------------------------------------------------- #

def _fallback_parse(block: str) -> dict[str, Any]:
    """Minimal YAML-ish parser for our well-structured frontmatter.

    Handles scalars, folded scalars (`>-` / `>`), block lists, inline lists,
    and one level of nested scalar maps. Not a general YAML implementation.
    """
    data: dict[str, Any] = {}
    lines = block.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\s*)([\w.-]+):\s*(.*)$", raw)
        if not m:
            i += 1
            continue
        indent, key, value = len(m.group(1)), m.group(2), m.group(3).strip()
        if indent != 0:
            i += 1
            continue

        if value in (">-", ">", "|", "|-"):
            collected: list[str] = []
            i += 1
            while i < n and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                if lines[i].strip():
                    collected.append(lines[i].strip())
                i += 1
            data[key] = " ".join(collected)
            continue

        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
            i += 1
            continue

        if value == "":
            # Look ahead: block list or nested map.
            items: list[str] = []
            nested: dict[str, Any] = {}
            j = i + 1
            while j < n and (lines[j].startswith((" ", "\t")) or not lines[j].strip()):
                ln = lines[j]
                if not ln.strip():
                    j += 1
                    continue
                lm = re.match(r"^\s*-\s*(.*)$", ln)
                if lm:
                    items.append(lm.group(1).strip().strip("'\""))
                else:
                    nm = re.match(r"^\s*([\w.-]+):\s*(.*)$", ln)
                    if nm:
                        nested[nm.group(1)] = nm.group(2).strip().strip("'\"")
                j += 1
            if items:
                data[key] = items
            elif nested:
                data[key] = nested
            else:
                data[key] = ""
            i = j
            continue

        data[key] = value.strip("'\"")
        i += 1
    return data


def parse_frontmatter(md_path: Path) -> dict[str, Any]:
    """Extract YAML frontmatter from a markdown file."""
    content = md_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    if yaml is not None:
        try:
            parsed = yaml.safe_load(block)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return _fallback_parse(block)


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #

def discover_skills() -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    if not SKILLS_DIR.exists():
        return skills
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            meta = parse_frontmatter(skill_file)
            meta["_path"] = str(skill_file.relative_to(REPO_ROOT)).replace("\\", "/")
            meta["_dir"] = skill_dir.name
            skills.append(meta)
    return skills


def discover_subagents() -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    if not SUBAGENTS_DIR.exists():
        return agents
    for f in sorted(SUBAGENTS_DIR.glob("*.md")):
        meta = parse_frontmatter(f)
        meta["_path"] = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
        meta["_name"] = meta.get("name", f.stem)
        agents.append(meta)
    return agents


def discover_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    if not RULES_DIR.exists():
        return rules
    for f in sorted(RULES_DIR.glob("*.md")):
        rules.append({
            "_path": str(f.relative_to(REPO_ROOT)).replace("\\", "/"),
            "_name": f.stem,
        })
    return rules


def _desc(meta: dict[str, Any], limit: int = 200) -> str:
    desc = meta.get("description", "")
    if isinstance(desc, list):
        desc = " ".join(desc)
    return " ".join(str(desc).split())[:limit]


def _write(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [DRY-RUN] Would write: {path.relative_to(REPO_ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  Written: {path.relative_to(REPO_ROOT)}")


# --------------------------------------------------------------------------- #
# Cursor
# --------------------------------------------------------------------------- #

def generate_cursor(
    skills: list[dict[str, Any]],
    subagents: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    agents_dir = REPO_ROOT / ".cursor" / "agents"
    for skill in skills:
        name = skill.get("name", skill["_dir"])
        content = (
            f"---\nname: {name}\ndescription: >-\n  {_desc(skill)}\n"
            f"skill_source: {skill['_path']}\n---\n\n"
            f"Load and follow the instructions in `{skill['_path']}`.\n\n"
            "This agent is a platform adapter — the canonical definition lives in `.ai/skills/`.\n"
        )
        _write(agents_dir / f"{name}.md", content, dry_run)

    for agent in subagents:
        name = agent["_name"]
        uses = agent.get("uses_skills", [])
        uses_line = ", ".join(uses) if isinstance(uses, list) else str(uses)
        content = (
            f"---\nname: {name}\ndescription: >-\n  {_desc(agent)}\n"
            f"subagent_source: {agent['_path']}\n---\n\n"
            f"Composite subagent. Follow `{agent['_path']}`.\n\n"
            f"Delegates to skills: {uses_line}.\n"
        )
        _write(agents_dir / f"{name}.md", content, dry_run)

    rules_dir = REPO_ROOT / ".cursor" / "rules"
    for rule in rules:
        name = rule["_name"]
        content = (
            f"---\ndescription: Project rule — {name}\nglobs:\nalwaysApply: true\n---\n\n"
            f"Follow the rule defined in `{rule['_path']}`.\n"
        )
        _write(rules_dir / f"{name}.mdc", content, dry_run)

    hooks = {
        "version": 1,
        "hooks": {
            "beforeReadFile": [{"command": f"{HOOK_CMD} guard-env-files"}],
            "beforeShellExecution": [{"command": f"{HOOK_CMD} ensure-uv-env"}],
            "afterShellExecution": [{"command": f"{HOOK_CMD} post-test-review"}],
            "afterFileEdit": [{"command": f"{HOOK_CMD} lint-changed-files"}],
            "beforeSubmitPrompt": [{"command": f"{HOOK_CMD} pre-agentic-estimate"}],
        },
    }
    _write(REPO_ROOT / ".cursor" / "hooks.json", json.dumps(hooks, indent=2) + "\n", dry_run)


# --------------------------------------------------------------------------- #
# Claude Code
# --------------------------------------------------------------------------- #

def generate_claude(
    skills: list[dict[str, Any]],
    subagents: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    lines = [
        "<!-- SPDX-License-Identifier: MIT -->",
        "",
        "# Project — Claude Code Instructions",
        "",
        "> Auto-generated from `.ai/`. Run `python .ai/setup-adapters.py` to regenerate.",
        "",
        "Read `.ai/AGENTS.md` for the full configuration and `.ai/rules/` for project rules.",
        "",
        "## Skills",
        "",
        "| Skill | Description | Source |",
        "|-------|-------------|--------|",
    ]
    for s in skills:
        lines.append(f"| `{s.get('name', s['_dir'])}` | {_desc(s, 100)} | `{s['_path']}` |")
    lines += ["", "## Subagents", "", "| Subagent | Description | Source |", "|----------|-------------|--------|"]
    for a in subagents:
        lines.append(f"| `{a['_name']}` | {_desc(a, 100)} | `{a['_path']}` |")
    lines += ["", "To use a skill or subagent, read its source file and follow the instructions.", ""]
    _write(REPO_ROOT / ".claude" / "CLAUDE.md", "\n".join(lines), dry_run)

    for a in subagents:
        name = a["_name"]
        content = (
            f"---\nname: {name}\ndescription: {_desc(a, 200)}\n---\n\n"
            f"Composite subagent. Follow `{a['_path']}`.\n"
        )
        _write(REPO_ROOT / ".claude" / "agents" / f"{name}.md", content, dry_run)

    settings_path = REPO_ROOT / ".claude" / "settings.json"
    if settings_path.exists():
        print(f"  Exists (not overwriting): {settings_path.relative_to(REPO_ROOT)}")
        return
    settings = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "", "hooks": [{"type": "command", "command": f"{HOOK_CMD} pre-agentic-estimate"}]},
                {"matcher": "Read|Write", "hooks": [{"type": "command", "command": f"{HOOK_CMD} guard-env-files"}]},
                {"matcher": "Bash|Shell", "hooks": [{"type": "command", "command": f"{HOOK_CMD} ensure-uv-env"}]},
            ],
            "PostToolUse": [
                {"matcher": "Bash|Shell", "hooks": [{"type": "command", "command": f"{HOOK_CMD} post-test-review"}]},
                {"matcher": "Write", "hooks": [{"type": "command", "command": f"{HOOK_CMD} lint-changed-files"}]},
            ],
        }
    }
    _write(settings_path, json.dumps(settings, indent=2) + "\n", dry_run)


# --------------------------------------------------------------------------- #
# GitHub Copilot
# --------------------------------------------------------------------------- #

def generate_copilot(skills: list[dict[str, Any]], dry_run: bool) -> None:
    lines = [
        "<!-- SPDX-License-Identifier: MIT -->",
        "",
        "# Project — Copilot Instructions",
        "",
        "> Auto-generated from `.ai/skills/`. Do not edit manually.",
        "> Run `python .ai/setup-adapters.py --platform copilot` to regenerate.",
        "",
        "## Skills Reference",
        "",
        "| Skill | Description |",
        "|-------|-------------|",
    ]
    for s in skills:
        lines.append(f"| `{s.get('name', s['_dir'])}` | {_desc(s, 100).replace('|', chr(92) + '|')} |")
    lines += [
        "",
        "For full instructions, read `.ai/skills/<name>/SKILL.md`.",
        "",
        "## Core Rules",
        "",
        "See `AGENTS.md` at the repository root and `.ai/rules/` for mandatory conventions.",
        "",
    ]
    _write(REPO_ROOT / ".github" / "copilot-instructions.md", "\n".join(lines), dry_run)


# --------------------------------------------------------------------------- #
# OpenAI Codex (root AGENTS.md) + Google Antigravity
# --------------------------------------------------------------------------- #

def generate_codex(
    skills: list[dict[str, Any]],
    subagents: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    lines = [
        "<!-- SPDX-License-Identifier: MIT -->",
        "",
        "# AGENTS",
        "",
        "> Auto-generated adapter from `.ai/`. The canonical source of truth is",
        "> `.ai/AGENTS.md`. Run `python .ai/setup-adapters.py` to regenerate.",
        "",
        "## Project Rules",
        "",
    ]
    for r in rules:
        lines.append(f"- `{r['_path']}` — {r['_name']}")
    lines += ["", "## Skills", "", "| Skill | Description | Source |", "|-------|-------------|--------|"]
    for s in skills:
        lines.append(f"| `{s.get('name', s['_dir'])}` | {_desc(s, 100)} | `{s['_path']}` |")
    lines += ["", "## Subagents", "", "| Subagent | Description | Source |", "|----------|-------------|--------|"]
    for a in subagents:
        lines.append(f"| `{a['_name']}` | {_desc(a, 100)} | `{a['_path']}` |")
    lines += ["", "Read the relevant source file under `.ai/` and follow its instructions.", ""]
    _write(REPO_ROOT / "AGENTS.md", "\n".join(lines), dry_run)


def generate_antigravity(
    skills: list[dict[str, Any]],
    subagents: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    lines = [
        "# Project — Google Antigravity Agent Instructions",
        "",
        "> Auto-generated from `.ai/`. Run `python .ai/setup-adapters.py` to regenerate.",
        "",
        "## Agent Specializations",
        "",
        "| Agent Role | Skill Source |",
        "|-----------|--------------|",
    ]
    for s in skills:
        lines.append(f"| {s.get('name', s['_dir'])} | `{s['_path']}` |")
    lines += ["", "## Composite Subagents", "", "| Subagent | Source |", "|----------|--------|"]
    for a in subagents:
        lines.append(f"| {a['_name']} | `{a['_path']}` |")
    lines += [
        "",
        "## Instructions",
        "",
        "Read the relevant source file for full agent instructions.",
        "See `AGENTS.md` at the repository root and `.ai/rules/` for project conventions.",
        "",
    ]
    _write(REPO_ROOT / ".antigravity" / "instructions.md", "\n".join(lines), dry_run)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate platform adapters from .ai/")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument(
        "--platform",
        choices=["cursor", "claude", "copilot", "codex", "antigravity", "all"],
        default="all",
    )
    args = parser.parse_args()

    os.chdir(REPO_ROOT)
    print(f"Repo root: {REPO_ROOT}")

    skills = discover_skills()
    subagents = discover_subagents()
    rules = discover_rules()

    if not skills:
        print("ERROR: No skills found. Ensure .ai/skills/*/SKILL.md files exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Discovered {len(skills)} skill(s), {len(subagents)} subagent(s), {len(rules)} rule(s).")
    for s in skills:
        print(f"  skill: {s.get('name', s['_dir'])}")
    for a in subagents:
        print(f"  subagent: {a['_name']}")
    print()

    p = args.platform
    if p in ("cursor", "all"):
        print("=== Cursor (.cursor/) ===")
        generate_cursor(skills, subagents, rules, args.dry_run)
        print()
    if p in ("claude", "all"):
        print("=== Claude Code (.claude/) ===")
        generate_claude(skills, subagents, args.dry_run)
        print()
    if p in ("copilot", "all"):
        print("=== GitHub Copilot (.github/) ===")
        generate_copilot(skills, args.dry_run)
        print()
    if p in ("codex", "all"):
        print("=== OpenAI Codex (AGENTS.md) ===")
        generate_codex(skills, subagents, rules, args.dry_run)
        print()
    if p in ("antigravity", "all"):
        print("=== Google Antigravity (.antigravity/) ===")
        generate_antigravity(skills, subagents, args.dry_run)
        print()

    print("Done." if not args.dry_run else "Done (dry-run). No files were modified.")


if __name__ == "__main__":
    main()
