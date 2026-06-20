# SPDX-License-Identifier: MIT
"""Shared loader for .ai/hooks-config.json.

Hooks import this sibling module to read user preferences for verbosity,
review scope, lint toggles, and budget gates.  Config file is optional:
missing or malformed -> deterministic defaults apply.

Search order for hooks-config.json: .ai/ (canonical) then .cursor/ (fallback).

Environment overrides let engineers switch modes per-session without
editing JSON:
    AI_HOOK_REVIEW_MODE      -> review.mode
    AI_HOOK_REVIEW_VERBOSITY -> review.verbosity
    AI_HOOK_LINT_ENABLED     -> lint.enabled (0/1)
    AI_HOOK_BUDGET_MAX       -> budget.maxSingleRequestUsd (float)
    AI_HOOK_BILLING_MODE     -> budget.billingMode

Cross-platform.  Python stdlib only.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "hooks-config.json"

_REVIEW_MODES = {"security-legal", "full", "off"}
_VERBOSITY = {"terse", "verbose"}
_REASONING = {"minimal", "default"}

# Pricing per 1M tokens (input, output).  Update as provider pricing changes.
# These are best-effort defaults for the budget-estimate hook only.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "opus":             (15.00, 75.00),
    "sonnet":           (3.00,  15.00),
    "haiku":            (0.25,  1.25),
    "gpt-4o":           (2.50,  10.00),
    "gpt-4.1":          (2.00,  8.00),
    "gpt-4.1-mini":     (0.40,  1.60),
    "gpt-4.1-nano":     (0.10,  0.40),
    "o3":               (10.00, 40.00),
    "o3-mini":          (1.10,  4.40),
    "o4-mini":          (1.10,  4.40),
    "gemini-2.5-pro":   (1.25,  10.00),
    "gemini-2.5-flash": (0.15,  0.60),
    "default":          (3.00,  15.00),
}

DEFAULTS: dict[str, dict[str, Any]] = {
    "budget": {
        "maxSingleRequestUsd": 5.0,
        "approvalTimeoutSec": 20,
        "autoApproveBelow": 1.0,
        "defaultModel": "sonnet",
        "billingMode": "auto",
        "outputInputRatio": 1.5,
        "showEstimate": True,
    },
    "review": {
        "mode": "security-legal",
        "verbosity": "terse",
        "reasoningHint": "minimal",
        "askBeforeProceeding": True,
        "maxIssues": 5,
    },
    "lint": {
        "enabled": True,
        "verbosity": "terse",
        "reasoningHint": "minimal",
        "maxIssues": 5,
    },
}


def _find_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for parent in [here] + list(here.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return here.parent.parent


def get_changed_py_files(repo_root: Path) -> list[Path]:
    """Return sorted list of changed .py files visible to git.

    Includes unstaged changes, staged changes, and untracked files so
    that hooks which run after edits or after tests both see the full set.
    """
    files: set[str] = set()
    for cmd in [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]:
        try:
            out = subprocess.check_output(
                cmd, cwd=str(repo_root), text=True, timeout=10,
            )
            files.update(line.strip() for line in out.splitlines() if line.strip())
        except Exception:
            pass
    return sorted(
        repo_root / f for f in files
        if f.endswith(".py") and (repo_root / f).exists()
    )


def _coerce(section: str, raw: dict[str, Any]) -> dict[str, Any]:
    merged = dict(DEFAULTS[section])
    for k, v in raw.items():
        if k in merged:
            merged[k] = v

    if section == "review":
        if merged["mode"] not in _REVIEW_MODES:
            merged["mode"] = DEFAULTS["review"]["mode"]
        if merged["verbosity"] not in _VERBOSITY:
            merged["verbosity"] = DEFAULTS["review"]["verbosity"]
        if merged["reasoningHint"] not in _REASONING:
            merged["reasoningHint"] = DEFAULTS["review"]["reasoningHint"]
        if not isinstance(merged["askBeforeProceeding"], bool):
            merged["askBeforeProceeding"] = True
    elif section == "lint":
        if not isinstance(merged["enabled"], bool):
            merged["enabled"] = True
        if merged["verbosity"] not in _VERBOSITY:
            merged["verbosity"] = DEFAULTS["lint"]["verbosity"]
        if merged["reasoningHint"] not in _REASONING:
            merged["reasoningHint"] = DEFAULTS["lint"]["reasoningHint"]
    elif section == "budget":
        for fkey in ("maxSingleRequestUsd", "autoApproveBelow", "outputInputRatio"):
            try:
                merged[fkey] = float(merged[fkey])
            except (TypeError, ValueError):
                merged[fkey] = DEFAULTS["budget"][fkey]
        if merged["billingMode"] not in {"auto", "metered", "enterprise"}:
            merged["billingMode"] = DEFAULTS["budget"]["billingMode"]
        try:
            merged["approvalTimeoutSec"] = int(merged["approvalTimeoutSec"])
        except (TypeError, ValueError):
            merged["approvalTimeoutSec"] = DEFAULTS["budget"]["approvalTimeoutSec"]
        if not isinstance(merged["showEstimate"], bool):
            merged["showEstimate"] = True

    if "maxIssues" in merged:
        try:
            merged["maxIssues"] = max(1, int(merged["maxIssues"]))
        except (TypeError, ValueError):
            merged["maxIssues"] = DEFAULTS[section]["maxIssues"]

    return merged


def load(section: str) -> dict[str, Any]:
    """Return resolved config for *section* ('review', 'lint', or 'budget')."""
    if section not in DEFAULTS:
        raise ValueError(f"Unknown hooks-config section: {section}")

    repo_root = _find_repo_root()
    candidates = [
        repo_root / ".ai" / CONFIG_FILENAME,
        repo_root / ".cursor" / CONFIG_FILENAME,
    ]

    raw: dict[str, Any] = {}
    for cfg_path in candidates:
        if cfg_path.exists():
            try:
                with cfg_path.open("r", encoding="utf-8-sig") as fh:
                    doc = json.load(fh)
                if isinstance(doc, dict) and isinstance(doc.get(section), dict):
                    raw = doc[section]
                break
            except (OSError, json.JSONDecodeError):
                continue

    resolved = _coerce(section, raw)

    if section == "review":
        env_mode = os.environ.get("AI_HOOK_REVIEW_MODE")
        if env_mode in _REVIEW_MODES:
            resolved["mode"] = env_mode
        env_verb = os.environ.get("AI_HOOK_REVIEW_VERBOSITY")
        if env_verb in _VERBOSITY:
            resolved["verbosity"] = env_verb
    elif section == "lint":
        env_en = os.environ.get("AI_HOOK_LINT_ENABLED")
        if env_en in ("0", "false", "no"):
            resolved["enabled"] = False
        elif env_en in ("1", "true", "yes"):
            resolved["enabled"] = True
    elif section == "budget":
        env_max = os.environ.get("AI_HOOK_BUDGET_MAX")
        if env_max:
            try:
                resolved["maxSingleRequestUsd"] = float(env_max)
            except ValueError:
                pass
        env_billing = os.environ.get("AI_HOOK_BILLING_MODE")
        if env_billing in {"auto", "metered", "enterprise"}:
            resolved["billingMode"] = env_billing

    return resolved


def resolve_model(hint: str | None = None) -> str:
    """Best-effort model slug from env vars, hint, or config default."""
    candidates = [
        hint,
        os.environ.get("CURSOR_MODEL"),
        os.environ.get("ANTHROPIC_MODEL"),
        os.environ.get("OPENAI_MODEL"),
    ]
    for c in candidates:
        if c:
            low = c.lower()
            for key in MODEL_PRICING:
                if key in low:
                    return key
            return low
    cfg = load("budget")
    return str(cfg.get("defaultModel", "sonnet"))


def price_per_million(model: str) -> tuple[float, float]:
    """Return (input_cost, output_cost) per 1M tokens for *model*."""
    low = model.lower()
    for key, val in MODEL_PRICING.items():
        if key in low:
            return val
    return MODEL_PRICING["default"]


def directive(cfg: dict[str, Any], kind: str) -> str:
    """Compact machine-parseable header for agent context.

    Example: [AI-HOOK kind=review mode=security-legal verbosity=terse reasoning=minimal ask=true]
    """
    bits = [f"kind={kind}"]
    label_map = {
        "mode": "mode",
        "verbosity": "verbosity",
        "reasoningHint": "reasoning",
        "askBeforeProceeding": "ask",
        "enabled": "enabled",
    }
    for key, label in label_map.items():
        if key in cfg:
            val = cfg[key]
            if isinstance(val, bool):
                val = "true" if val else "false"
            bits.append(f"{label}={val}")
    return "[AI-HOOK " + " ".join(bits) + "]"
