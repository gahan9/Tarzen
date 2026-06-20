<!-- SPDX-License-Identifier: MIT -->

# Contributing

Thanks for helping improve the Carbon Footprint Awareness Platform. This guide
covers local setup, the quality gates your change must pass, and how commits and
pull requests are expected to look. The canonical engineering rules live in
[`.ai/rules/`](./.ai/rules); this file summarises them for contributors.

## Repository layout

| Path | Stack | Notes |
|------|-------|-------|
| `backend/` | Python 3.11, FastAPI, hexagonal | Domain → application → adapters → api |
| `frontend/` | Vite + React + TypeScript | Firebase Hosting; Vitest + axe tests |
| `mobile/` | Expo + React Native | Offline-first queue; Jest tests |
| `packages/shared-types/` | TypeScript + zod | API contract shared by web + mobile |
| `infra/` | Terraform, Cloud Build | Least-privilege GCP infrastructure |
| `docs/` | Markdown | Architecture, threat model, governance |

## Prerequisites

- **Python**: [`uv`](https://docs.astral.sh/uv/) (manages the venv and lockfile)
- **Node**: Node 20+ and npm
- **Pre-commit**: `pipx install pre-commit` (or `pip install pre-commit`)

## Local setup

```bash
# Backend
cd backend && uv sync --all-extras

# Shared contract (build before the web/mobile apps consume it)
cd packages/shared-types && npm ci && npm run build

# Web
cd frontend && npm ci

# Mobile
cd mobile && npm ci

# Git hooks (run from the repo root)
pre-commit install
```

## Quality gates

Every change must pass the same checks CI runs. Run them before pushing.

### Backend (`backend/`)

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest            # enforces the >=90% coverage gate
```

### Web (`frontend/`)

```bash
npm run typecheck
npm run lint             # ESLint + jsx-a11y accessibility rules
npm run test:coverage    # Vitest + axe, >=90% coverage gate
npm run build
```

### Mobile (`mobile/`)

```bash
npm run typecheck
npm test                 # Jest
```

## Coding standards (summary)

- **Python** — PEP 8, 88-char lines (ruff), Google-style docstrings,
  `from __future__ import annotations`, type hints on public APIs, async I/O.
- **TypeScript** — strict mode, explicit types at module boundaries, no `any`
  in shipped code, accessible markup (labels, roles, focus management).
- **Security** — never commit secrets; `.env` is gitignored and blocked by the
  agent hooks. Credentials come from the environment / Application Default
  Credentials, never the codebase.
- **Licensing** — every source file starts with an
  `SPDX-License-Identifier` comment. No GPL/AGPL/SSPL dependencies.

## Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/) and sign off
every commit (Developer Certificate of Origin). Both are enforced in CI.

```
type(scope): imperative subject (<= 80 chars)

Body explaining *why* the change is needed.

Signed-off-by: Your Name <you@example.com>
```

Allowed types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`,
`ci`, `chore`, `revert`, `security`. Use `git commit -s` to add the sign-off.

## Pull request budget

Keep PRs reviewable (see [`.ai/rules/pr-budget.md`](./.ai/rules/pr-budget.md)):

| Change type | Soft cap (LOC, excl. tests) |
|-------------|-----------------------------|
| Bug fix | 200 |
| Refactor | 400 |
| Feature | 600 (+ tests) |

Split larger work into a sequence of focused, independently reviewable PRs.

## Reporting issues

Open a GitHub issue with reproduction steps, expected vs. actual behaviour, and
environment details. For suspected security vulnerabilities, do **not** open a
public issue — contact the maintainers privately.
