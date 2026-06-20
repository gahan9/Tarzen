# SPDX-License-Identifier: MIT
"""Pre-agentic estimation hook: cost forecast before execution begins.

Scans the workspace to measure what will be loaded into context:
  - Skills (.ai/skills/*/SKILL.md + user-level skills)
  - MCP server tool definitions (mcps/<server>/tools/*.json)
  - Rules (.ai/AGENTS.md, CLAUDE.md, .cursor/rules/, .ai/rules/)
  - Hooks context overhead

Estimates input+output token cost using model-specific pricing.
If estimated cost exceeds budget.maxSingleRequestUsd ($5 default),
emits a BUDGET_GATE directive telling the agent to ask the user
for explicit approval before proceeding.

Consumable by both Cursor (sessionStart) and Claude Code (PreToolUse
with first-run guard).  See .ai/AGENTS.md and README.md.

Cross-platform (Windows + Linux/macOS).  Python stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, NoReturn

import _hook_config

CHARS_PER_TOKEN = 4
HOOK_OVERHEAD_TOKENS = 500
BASE_SYSTEM_PROMPT_TOKENS = 4_000
AGENT_RESPONSE_FLOOR_TOKENS = 2_000

_SESSION_FLAG = ".ai/.pre-agentic-ran"
_ENTERPRISE_MODEL_PRICE = (0.0, 0.0)


def _file_tokens(path: Path) -> int:
    """Estimate tokens from file size (chars / CHARS_PER_TOKEN)."""
    try:
        return path.stat().st_size // CHARS_PER_TOKEN
    except OSError:
        return 0


def _scan_skills(repo_root: Path) -> tuple[int, list[str]]:
    """Count project-level skills and estimate their token weight."""
    total_tokens = 0
    names: list[str] = []
    for project_skills in [repo_root / ".ai" / "skills", repo_root / ".cursor" / "skills"]:
        if project_skills.is_dir():
            for skill_dir in sorted(project_skills.iterdir()):
                skill_file = skill_dir / "SKILL.md"
                if skill_file.is_file() and skill_dir.name not in names:
                    total_tokens += _file_tokens(skill_file)
                    names.append(skill_dir.name)

    # User/plugin skills are exposed as selectable metadata. Their full SKILL.md
    # bodies load only when an agent explicitly reads them, so charging every
    # installed skill to every request grossly overestimates.
    user_skill_dirs = [
        Path.home() / ".cursor" / "skills",
        Path.home() / ".cursor" / "skills-cursor",
    ]
    for udir in user_skill_dirs:
        if udir.is_dir():
            for item in udir.iterdir():
                skill_file = item / "SKILL.md" if item.is_dir() else item
                if skill_file.is_file() and skill_file.suffix == ".md":
                    total_tokens += 50
                    names.append(f"~/{item.name}")

    return total_tokens, names


def _scan_mcps(repo_root: Path) -> tuple[int, list[str]]:
    """Count MCP server tool definitions and estimate token weight.

    Note: if the project-specific mcps/ directory is not found, the fallback
    iterates all projects under ~/.cursor/projects/ and picks the first one
    with an mcps/ subdirectory.  This may match a different project when
    multiple workspaces exist.
    """
    mcps_root = Path.home() / ".cursor" / "projects"
    project_key = str(repo_root).replace("\\", "-").replace("/", "-").replace(":", "")
    mcps_dir = mcps_root / project_key / "mcps"

    total_tokens = 0
    names: list[str] = []

    if not mcps_dir.is_dir():
        for candidate in mcps_root.iterdir() if mcps_root.is_dir() else []:
            test = candidate / "mcps"
            if test.is_dir():
                mcps_dir = test
                break

    if mcps_dir.is_dir():
        for server_dir in sorted(mcps_dir.iterdir()):
            if not server_dir.is_dir():
                continue
            tools_dir = server_dir / "tools"
            if tools_dir.is_dir():
                server_tokens = sum(
                    _file_tokens(f)
                    for f in tools_dir.iterdir()
                    if f.suffix == ".json"
                )
                total_tokens += server_tokens
                names.append(server_dir.name)
            else:
                total_tokens += 200
                names.append(server_dir.name)

    return total_tokens, names


def _scan_rules(repo_root: Path) -> int:
    """Estimate tokens from AGENTS.md, CLAUDE.md, and rules directories."""
    total = 0
    for name in (".ai/AGENTS.md", "CLAUDE.md", "AGENTS.md", ".cursorrules"):
        total += _file_tokens(repo_root / name)

    for rules_dir in [repo_root / ".ai" / "rules", repo_root / ".cursor" / "rules"]:
        if rules_dir.is_dir():
            for f in rules_dir.rglob("*.md"):
                total += _file_tokens(f)
            for f in rules_dir.rglob("*.mdc"):
                total += _file_tokens(f)

    return total


def _scan_agents(repo_root: Path) -> int:
    total = 0
    for agents_dir in [
        repo_root / ".ai" / "subagents",
        repo_root / ".cursor" / "agents",
        repo_root / ".claude" / "agents",
    ]:
        if agents_dir.is_dir():
            total += sum(_file_tokens(f) for f in agents_dir.iterdir() if f.suffix == ".md")
    return total


def _is_first_run(repo_root: Path) -> bool:
    """Guard for Claude Code PreToolUse: only run full scan once per session."""
    flag = repo_root / _SESSION_FLAG
    if flag.exists():
        try:
            age = time.time() - flag.stat().st_mtime
            if age < 3600:
                return False
        except OSError:
            pass
    try:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass
    return True


def _aggregate_workspace(repo_root: Path) -> dict[str, Any]:
    """Scan all context sources and return raw token counts + names."""
    skill_tokens, skill_names = _scan_skills(repo_root)
    mcp_tokens, mcp_names = _scan_mcps(repo_root)
    rules_tokens = _scan_rules(repo_root)
    agents_tokens = _scan_agents(repo_root)
    return {
        "skill_tokens": skill_tokens,
        "skill_names": skill_names,
        "mcp_tokens": mcp_tokens,
        "mcp_names": mcp_names,
        "rules_tokens": rules_tokens,
        "agents_tokens": agents_tokens,
    }


def _compute_cost(
    workspace: dict[str, Any], cfg: dict[str, Any],
) -> dict[str, Any]:
    """Translate workspace token counts into cost estimates."""
    model = _hook_config.resolve_model()
    billing_mode = str(cfg.get("billingMode", "auto"))
    if billing_mode == "auto" and os.environ.get("CURSOR_AGENT") == "1":
        billing_mode = "enterprise"

    if billing_mode == "enterprise":
        input_price, output_price = _ENTERPRISE_MODEL_PRICE
    else:
        billing_mode = "metered"
        input_price, output_price = _hook_config.price_per_million(model)
    output_ratio = float(cfg["outputInputRatio"])

    input_tokens = (
        BASE_SYSTEM_PROMPT_TOKENS
        + workspace["rules_tokens"]
        + workspace["skill_tokens"]
        + workspace["mcp_tokens"]
        + workspace["agents_tokens"]
        + HOOK_OVERHEAD_TOKENS
    )
    output_tokens = max(AGENT_RESPONSE_FLOOR_TOKENS, int(input_tokens * output_ratio))

    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    return {
        "model": model,
        "input_price": input_price,
        "output_price": output_price,
        "billing_mode": billing_mode,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
    }


def _build_emit_payload(
    workspace: dict[str, Any], costs: dict[str, Any], cfg: dict[str, Any],
) -> dict[str, Any]:
    """Format workspace + cost data into the hook emit payload."""
    total_cost = costs["total_cost"]
    model = costs["model"]
    input_tokens = costs["input_tokens"]
    output_tokens = costs["output_tokens"]
    input_cost = costs["input_cost"]
    output_cost = costs["output_cost"]
    billing_mode = costs["billing_mode"]
    max_budget = float(cfg["maxSingleRequestUsd"])
    timeout = int(cfg["approvalTimeoutSec"])
    over_budget = billing_mode == "metered" and total_cost >= max_budget
    price_text = (
        "Enterprise seat; public API pricing not applied"
        if billing_mode == "enterprise"
        else f"${costs['input_price']}/{costs['output_price']} per 1M in/out"
    )

    breakdown_lines = [
        f"model={model} ({price_text})",
        f"skills={len(workspace['skill_names'])} ({workspace['skill_tokens']:,}tok)",
        f"mcps={len(workspace['mcp_names'])} ({workspace['mcp_tokens']:,}tok)",
        f"rules={workspace['rules_tokens']:,}tok agents={workspace['agents_tokens']:,}tok",
        f"base+hooks={BASE_SYSTEM_PROMPT_TOKENS + HOOK_OVERHEAD_TOKENS:,}tok",
        f"total_input={input_tokens:,}tok est_output={output_tokens:,}tok",
        f"billing_mode={billing_mode}",
        f"est_cost=${total_cost:.4f} (in=${input_cost:.4f} out=${output_cost:.4f})",
        f"budget=${max_budget:.2f} status={'OVER' if over_budget else 'OK'}",
    ]

    if over_budget:
        header = (
            f"[AI-HOOK kind=budget status=OVER "
            f"est=${total_cost:.4f} max=${max_budget:.2f} "
            f"timeout={timeout}s model={model}]"
        )
        detail = " | ".join(breakdown_lines)
        return {
            "additional_context": (
                f"{header}\n"
                f"BUDGET GATE: Estimated ${total_cost:.4f} exceeds "
                f"${max_budget:.2f} limit.\n"
                f"  {detail}\n"
                f"ACTION REQUIRED: Use AskQuestion to get explicit user "
                f"approval before proceeding. If no denial within "
                f"{timeout}s, auto-continue."
            ),
            "user_message": (
                f"Estimated cost for this request: ${total_cost:.4f} "
                f"(model={model}, {input_tokens:,} input + "
                f"{output_tokens:,} output tokens). "
                f"Budget limit is ${max_budget:.2f}. "
                f"The agent will ask for your approval before proceeding."
            ),
        }
    header = (
        f"[AI-HOOK kind=budget status=OK "
        f"est=${total_cost:.4f} max=${max_budget:.2f} "
        f"model={model} billing={billing_mode}]"
    )
    summary = (
        f"skills={len(workspace['skill_names'])} mcps={len(workspace['mcp_names'])} "
        f"input={input_tokens:,}tok output~{output_tokens:,}tok "
        f"cost~${total_cost:.4f} billing={billing_mode}"
    )
    return {"additional_context": f"{header} {summary}"}


def _emit(payload: dict[str, Any]) -> NoReturn:
    json.dump(payload, sys.stdout)
    sys.exit(0)


def main() -> None:
    repo_root = _hook_config._find_repo_root()
    os.chdir(str(repo_root))

    is_claude_retrigger = os.environ.get("CLAUDE_CODE") == "1"
    if is_claude_retrigger and not _is_first_run(repo_root):
        _emit({"additional_context": ""})

    cfg = _hook_config.load("budget")
    if not cfg["showEstimate"]:
        _emit({"additional_context": ""})

    workspace = _aggregate_workspace(repo_root)
    costs = _compute_cost(workspace, cfg)
    _emit(_build_emit_payload(workspace, costs, cfg))


if __name__ == "__main__":
    main()
