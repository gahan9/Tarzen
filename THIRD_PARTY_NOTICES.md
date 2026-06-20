<!-- SPDX-License-Identifier: MIT -->

# Third-Party Notices

This project's own source is MIT-licensed. It additionally vendors third-party
skills under `.ai/skills/`. Those skills retain their original licenses; this
file records their provenance and any modifications, per their license terms.

## Vendored AI skills

The following skills were imported from
[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
and are licensed under the **Apache License 2.0**.

| Skill (`.ai/skills/<dir>`) | Upstream path | License | License file |
|----------------------------|---------------|---------|--------------|
| `changelog-generator`       | `changelog-generator`       | Apache-2.0 | repo root (Apache-2.0) |
| `content-research-writer`   | `content-research-writer`   | Apache-2.0 | repo root (Apache-2.0) |
| `developer-growth-analysis` | `developer-growth-analysis` | Apache-2.0 | repo root (Apache-2.0) |
| `file-organizer`            | `file-organizer`            | Apache-2.0 | repo root (Apache-2.0) |
| `lead-research-assistant`   | `lead-research-assistant`   | Apache-2.0 | repo root (Apache-2.0) |
| `meeting-insights-analyzer` | `meeting-insights-analyzer` | Apache-2.0 | repo root (Apache-2.0) |
| `mcp-builder`               | `mcp-builder`               | Apache-2.0 | `.ai/skills/mcp-builder/LICENSE.txt` |
| `theme-factory`             | `theme-factory`             | Apache-2.0 | `.ai/skills/theme-factory/LICENSE.txt` |
| `webapp-testing`            | `webapp-testing`            | Apache-2.0 | `.ai/skills/webapp-testing/LICENSE.txt` |

Upstream repository license: Apache-2.0
(https://www.apache.org/licenses/LICENSE-2.0).

### Modifications

The `SKILL.md` frontmatter of each vendored skill was rewritten to conform to
this project's universal skill format (`.ai/SKILL-FORMAT.md`) — adding
`aliases`, `version`, `platforms`, `scope`, `triggers`, `source`, and `license`
fields. Skill body content is unmodified. The original `name` and `description`
are preserved.

## License-incompatible upstreams — replaced with original content

The following requested skills were **not** vendored because their upstream
licenses violate `.ai/rules/security.md`. Instead, license-clean replacements
were authored in-repo (MIT) — no upstream code or text was copied:

| Skill | Upstream license | Replacement in this repo |
|-------|------------------|--------------------------|
| `document-skills` (docx, pdf, pptx, xlsx) | Proprietary (© Anthropic, all rights reserved) — forbids copying, retaining copies outside Anthropic services, and derivative works | `.ai/skills/document-skills/SKILL.md` — a **pointer-only** skill (MIT) that defers to the platform's native document skill at runtime or to permissively licensed libraries; no proprietary content vendored. |
| `twitter-algorithm-optimizer` | AGPL-3.0 (blocked copyleft) | `.ai/skills/twitter-algorithm-optimizer/SKILL.md` — a **clean-room** skill (MIT) restating publicly known ranking principles in original prose; no AGPL source reproduced. |
