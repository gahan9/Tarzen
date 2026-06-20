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

## Backend Python dependencies

The backend (`backend/`) depends on the following packages. All are under
permissive or weak-copyleft licenses on the allow-list in
`.ai/rules/security.md`; **no GPL/AGPL/SSPL** dependency is present (verified via
`pip-licenses` on 2026-06-20).

### Runtime dependencies

| Package | License |
|---------|---------|
| `fastapi`, `pydantic`, `pydantic-settings`, `pydantic_core`, `PyJWT`, `anyio`, `h11`, `urllib3` | MIT |
| `starlette`, `uvicorn`, `httpx`/`httpcore`, `click`, `idna`, `python-dotenv`, `websockets` | BSD-3-Clause |
| `firebase-admin`, `google-cloud-aiplatform`, `google-cloud-firestore`, `google-cloud-bigquery`, `google-cloud-pubsub`, `google-api-core`, `google-auth`, `googleapis-common-protos`, `grpcio`, `proto-plus`, `protobuf`, `requests`, `cryptography` | Apache-2.0 (or BSD-3-Clause for protobuf) |
| `certifi` | MPL-2.0 (weak, file-level copyleft; used unmodified) |
| `typing_extensions` | PSF-2.0 |
| `defusedxml` | PSF (Python Software Foundation) |
| `google-crc32c` | Apache-2.0 (upstream; PyPI metadata reports `UNKNOWN`) |

### Development / CI tooling

| Package | License |
|---------|---------|
| `ruff`, `mypy`, `pytest`, `pytest-cov`, `coverage`, `pytest-asyncio`, `bandit`, `pip-audit` | MIT or Apache-2.0 |
| `pip-licenses`, `pip-system-certs` | MIT / BSD-3-Clause |
| `pathspec` | MPL-2.0 (weak, file-level copyleft; used unmodified) |

> `pip-system-certs` is a developer convenience to route `requests` through the
> OS trust store behind a TLS-intercepting proxy; it is not a runtime dependency.

## Emission-factor datasets

The deterministic footprint engine uses public emission factors. Full
per-dataset detail is in [`docs/data-sources.md`](docs/data-sources.md).

| Dataset | Use | Version | License / terms |
|---------|-----|---------|-----------------|
| UK DEFRA / DESNZ — GHG reporting conversion factors 2024 | Transport factors (`backend/src/carbon/data/emission_factors.json`) | 2024.1 | Open Government Licence v3.0 (attribution) |
| Benchmark reference magnitudes (`backend/src/carbon/domain/benchmarks.py`) | Relatable equivalences | — | Public reference values |
| US EPA — Emission Factors for GHG Inventories *(roadmap)* | Energy/waste factors (Phase 6) | — | US Government work — public domain |
| GHG Protocol emission-factor datasets *(roadmap)* | Cross-domain reference/methodology (Phase 6) | — | Free use (attribution) |
