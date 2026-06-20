# Universal AI Skill Format Specification

> **Version**: 1.0
> **Compatibility**: Claude Code, GitHub Copilot, Cursor, OpenAI Codex, Google Antigravity

## Overview

This specification defines a platform-agnostic skill format that can be consumed
by any AI coding assistant. Skills are authored once in `.ai/skills/` and
platform-specific adapters are generated from them.

## File Structure

Each skill lives in its own directory under `.ai/skills/`:

```
.ai/skills/<skill-name>/
├── SKILL.md          # Canonical skill definition (this is the source of truth)
├── *.md              # Supporting reference docs (optional)
└── examples/         # Worked examples (optional)
```

## SKILL.md Format

Every SKILL.md follows this structure:

```markdown
---
name: <kebab-case-identifier>
aliases: [<optional-trigger-aliases>]
version: "1.0"
description: >-
  <One-paragraph description. Include trigger phrases that should activate
  this skill. Keep under 300 chars for compatibility with all platforms.>
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - <file-glob-patterns this skill applies to>
triggers:
  - <natural-language phrases that activate this skill>
delegates_to:
  - <other-skill-names this skill calls>
---

# <Skill Title>

## Purpose
<1-3 sentences: what this skill does and why it exists>

## When to Use
<Bullet list of activation conditions>

## When NOT to Use
<Bullet list of exclusions / delegations to other skills>

## Instructions
<The actual skill content — platform-agnostic directives>

## Output Format
<How the skill should structure its response>

## References
<Links to supporting docs, both internal and external>
```

Multi-line `description: >-` folded blocks are supported; adapter generation uses
PyYAML (`yaml.safe_load`) to parse frontmatter.

## Platform Adapter Mapping

| Platform           | Reads from                            | Format notes                          |
|--------------------|---------------------------------------|---------------------------------------|
| Cursor             | `.cursor/rules/*.mdc` + skills dir    | YAML frontmatter + markdown body      |
| Claude Code        | `CLAUDE.md` + `.claude/settings.json` | Markdown instructions                 |
| GitHub Copilot     | `.github/copilot-instructions.md`     | Single markdown file, <8000 tokens    |
| OpenAI Codex       | `AGENTS.md` at repo root              | Markdown with section headers         |
| Google Antigravity | `AGENTS.md` + project config          | Markdown + slash-command integration  |

## Conventions

1. **No platform-specific syntax** in the canonical SKILL.md body.
   Platform adapters handle translation.
2. **Self-contained**: Each skill must be understandable without reading
   other skills (cross-references use `delegates_to` in frontmatter).
3. **Imperative voice**: "Do X" not "You should X" or "Consider X".
4. **Quantified criteria**: "Functions <= 50 lines" not "keep functions short".
5. **Examples over rules**: Show good/bad examples inline.
6. **No tool-specific jargon**: Say "run linter" not "use Cursor's lint hook".
7. **No proprietary names**: Keep company, product, and customer names out of
   canonical skills so the template stays portable and publicly shareable.
