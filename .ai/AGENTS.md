<!-- SPDX-License-Identifier: MIT -->

# Universal AI Agent Configuration

> **Single source of truth**: all agent configuration lives in `.ai/`.
> **Platform compatibility**: Claude Code, GitHub Copilot, Cursor, OpenAI Codex, Google Antigravity.
> Tool-specific adapters reference `.ai/` and contain no business logic.

## Architecture

```
.ai/                              # Canonical source (platform-agnostic)
├── AGENTS.md                     # This file — central instructions + index
├── SKILL-FORMAT.md               # Universal skill format specification
├── rules/                        # Modular project rules (the "rules" primitive)
│   ├── python.md                 # Style, typing, async, packaging
│   ├── security.md               # Secrets, SPDX, dependency licensing
│   ├── git-commits.md            # Conventional Commits + sign-off
│   ├── pr-budget.md              # Reviewability budget
│   └── testing.md                # Test tiers, coverage, mocking
├── hooks/                        # Shared hook scripts (the "hooks" primitive)
│   ├── _hook_config.py           # Config loader, model pricing, utilities
│   ├── guard-env-files.py        # Blocks .env reads/writes (fail-closed)
│   ├── ensure-uv-env.py          # Verifies uv venv before Python commands
│   ├── lint-changed-files.py     # ruff + mypy on changed files after edits
│   ├── post-test-review.py       # SPDX, secret, and style checks
│   ├── pre-agentic-estimate.py   # Token cost forecast before expensive ops
│   └── run-hook.py               # Universal entry point
├── hooks-config.json             # Shared hook tunables (budget, review, lint)
├── skills/                       # Universal skill definitions (the "skills" primitive)
│   ├── principal-engineer/       # Architecture, security, ROI, GPU compute
│   ├── ai-engineer/              # Agent/graph pipelines, rule-based-first, LLM calls
│   ├── backend-architect/        # Service layout, connectors, config, state
│   ├── clean-code/               # Readability review (Robert C. Martin)
│   ├── devops-automator/         # CI/CD, Docker, deployment, secrets hygiene
│   ├── code-reviewer/            # 16-point PR review checklist
│   └── test-quality-evaluator/   # Test execution and quality scoring
├── subagents/                    # Composite delegatable agents (the "subagents" primitive)
│   ├── reviewer.md               # code-reviewer + clean-code
│   ├── architect.md              # backend-architect + principal-engineer
│   └── release-engineer.md       # devops-automator + test-quality-evaluator
├── setup-adapters.py             # Generates platform adapter files
└── setup-links.py                # Links .ai/skills into .cursor/skills

Platform Adapters (generated from .ai/):
├── AGENTS.md (root)              # OpenAI Codex + Google Antigravity
├── .cursor/hooks.json            # Cursor hook events → .ai/hooks/
├── .cursor/rules/*.mdc           # Cursor rules → .ai/rules/
├── .cursor/agents/*.md           # Cursor agent prompts → .ai/skills + .ai/subagents
├── .claude/CLAUDE.md             # Claude Code instructions
├── .claude/settings.json         # Claude Code hook events → .ai/hooks/
├── .claude/agents/*.md           # Claude Code subagents → .ai/subagents
├── .github/copilot-instructions.md  # GitHub Copilot guidance
└── .antigravity/instructions.md  # Google Antigravity agent config
```

## The Four Primitives

| Primitive | Lives in | Purpose |
|-----------|----------|---------|
| **Rules** | `.ai/rules/*.md` | Always-on project conventions that constrain every change |
| **Hooks** | `.ai/hooks/*.py` | Deterministic guardrails fired on tool/agent events |
| **Skills** | `.ai/skills/<name>/SKILL.md` | Reusable, trigger-activated capability modules |
| **Subagents** | `.ai/subagents/*.md` | Composite agents that delegate to one or more skills |

## Platform Adapter Mapping

| Platform           | Primary Config                      | Hook System             | Skill Loading            |
|--------------------|-------------------------------------|-------------------------|--------------------------|
| **Cursor**         | `.cursor/agents/*.md`               | `.cursor/hooks.json`    | Reads SKILL.md directly  |
| **Claude Code**    | `.claude/CLAUDE.md`                 | `.claude/settings.json` | Read tool on SKILL.md    |
| **GitHub Copilot** | `.github/copilot-instructions.md`   | N/A (no hooks)          | Inline summary           |
| **OpenAI Codex**   | `AGENTS.md` (root)                  | N/A (uses AGENTS.md)    | Section headers in root  |
| **Google Antigravity** | `.antigravity/instructions.md`  | Slash commands          | Multi-agent delegation   |

## Regenerating Adapters

After modifying any `.ai/skills/*/SKILL.md`, `.ai/rules/*.md`, or
`.ai/subagents/*.md`, regenerate all platform adapters:

```bash
python .ai/setup-adapters.py            # Regenerate all platforms
python .ai/setup-adapters.py --dry-run  # Preview changes
python .ai/setup-adapters.py --platform cursor  # Single platform
```

To expose `.ai/skills/` to Cursor's native skill discovery:

```bash
python .ai/setup-links.py
```

## Project Conventions (summary)

Full detail lives in `.ai/rules/`. Highlights:

- **Python** — PEP 8, 88-char lines (Black/Ruff), Google-style docstrings,
  `from __future__ import annotations`, type hints on public APIs, async-first I/O.
  See `rules/python.md`.
- **Security** — no plaintext secrets; `.env` gitignored and blocked by
  `guard-env-files.py`; credentials via env/secret manager wrapped in a secret
  type. See `rules/security.md`.
- **Licensing** — every source file carries `SPDX-License-Identifier`; project
  `LICENSE` at repo root; no GPL/AGPL/SSPL dependencies. See `rules/security.md`.
- **Commits** — `type(scope): subject` (<= 80 chars, imperative); body explains
  *why*; `Signed-off-by:` trailer. See `rules/git-commits.md`.
- **PR budget** — bugfix <= 200 LOC, refactor <= 400 LOC, feature <= 600 LOC + tests.
  See `rules/pr-budget.md`.
- **Testing** — pytest; unit tests mock external clients; integration tests gated
  on credentials. See `rules/testing.md`.

## Skills Reference

| Skill | Trigger Phrases | Purpose |
|-------|-----------------|---------|
| `principal-engineer` | architecture, security, scalability, ROI, GPU | ROI gate, licensing, security, GPU compute, packaging |
| `ai-engineer` | pipeline node, agent graph, confidence threshold, LLM call | Rule-based-first routing, structured outputs, gateway client |
| `backend-architect` | service layout, connector, config, transport, state | Package layout, async connectors, settings management |
| `clean-code` | readability, clarity, simplicity, story flow | Function story-flow, abstraction value |
| `devops-automator` | CI/CD, Docker, deployment, secrets, pipeline | Container images, pipeline automation, secret hygiene |
| `code-reviewer` | code review, PR review, review this diff | 16-point checklist, commit hygiene, config↔docs parity |
| `test-quality-evaluator` | run tests, coverage, quality scoring, regression | Test execution, quality matrix, calibration |

### Vendored skills (Apache-2.0, see `THIRD_PARTY_NOTICES.md`)

| Skill | Trigger Phrases | Purpose |
|-------|-----------------|---------|
| `changelog-generator` | generate changelog, release notes | Turn git history into user-facing release notes |
| `content-research-writer` | write blog post, draft article, content outline | Research-backed long-form writing partner |
| `developer-growth-analysis` | coding patterns, growth report, skill gap | Analyze coding history, surface growth areas |
| `file-organizer` | organize files, clean up downloads, duplicates | Context-aware file/folder organization |
| `lead-research-assistant` | find leads, target companies, prospecting | Identify and qualify sales/BD leads |
| `meeting-insights-analyzer` | meeting transcript, communication feedback | Behavioral/communication insights from transcripts |
| `mcp-builder` | build MCP server, MCP tools, FastMCP, MCP SDK | Author high-quality MCP servers (Python/Node) |
| `theme-factory` | apply theme, style artifact, color palette | Apply/generate cohesive color+font themes |
| `webapp-testing` | test web app, playwright, browser screenshot | Playwright-based local web app testing |

### License-clean originals (MIT, authored in-repo)

| Skill | Trigger Phrases | Purpose |
|-------|-----------------|---------|
| `document-skills` | create docx, edit pdf, build pptx, xlsx | Pointer skill: defer to native/permissive doc tooling (no proprietary copy) |
| `twitter-algorithm-optimizer` | optimize this tweet, improve reach | Clean-room tweet/X optimization (no AGPL code) |

## Subagents Reference

| Subagent | Composes | Use for |
|----------|----------|---------|
| `reviewer` | code-reviewer, clean-code | End-to-end review of a diff or PR |
| `architect` | backend-architect, principal-engineer | Design and scalability decisions |
| `release-engineer` | devops-automator, test-quality-evaluator | Build, test, and ship readiness |

## Hook Configuration

Edit `.ai/hooks-config.json` to adjust hook behaviour without touching code.

Key env overrides for quick per-session changes:

| Variable                   | Effect                            |
|----------------------------|-----------------------------------|
| `AI_HOOK_REVIEW_MODE=off`  | Disable post-test review entirely |
| `AI_HOOK_LINT_ENABLED=0`   | Disable lint-on-edit              |
| `AI_HOOK_BUDGET_MAX=10`    | Raise cost approval threshold     |
