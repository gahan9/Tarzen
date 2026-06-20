# Code Review — Full 16-Point Matrix

Reference for the `code-reviewer` skill. Maps every reviewer priority to a
concrete check, the pass criterion, and the action on failure. Use this when
running a thorough review; the SKILL.md workflow points here.

| # | Check | What to look for in the diff | Pass criterion | Action on fail |
|---|-------|------------------------------|----------------|----------------|
| 1 | **Clean code** | Long functions, deep nesting, magic constants, narrating comments, dead code, vague names | Functions <= 50 LOC and complexity <= 10; constants named; comments explain *why*; no dead code | Recommended -- request specific refactors with file:line |
| 2 | **PR reviewable in <30 min** | Total LOC changed; mixing refactor + behavior change; generated files inline; unrelated edits | Within the size budget (200 / 400 / 600); single logical concern | Block -- propose specific split seams |
| 3 | **Commit describes changes & impact** | Body present; maps to touched files; states behavior / perf / API delta; migration notes | Body has clear "what changed" and "impact"; reviewer can predict the diff | Block -- propose a rewritten message |
| 4 | **Why-and-What in commit; title <= 80** | `type(scope): subject` form; imperative mood; body wrapped at 72; *why* before *what*; `Signed-off-by:` | Title <= 80; type + scope present; motivation clear; sign-off present | Block -- author must amend |
| 5 | **Style + types** | Linter + type checker clean; new files include `from __future__ import annotations`; idiomatic imports | All checks clean on changed files | Critical -- must fix before merge |
| 6 | **Config <-> documentation parity** | New keys in config files or `.env.example` without matching doc updates in the same PR | Every new/changed config key is documented with default + valid range | Block -- documentation drift is a defect |
| 7 | **Unit tests for new functionality** | New logic with no `tests/` change; bug fix without a regression test | Each non-trivial new function has a direct test; bug fixes ship a test that fails on base | Critical for non-trivial logic |
| 8 | **SOLID** | God-classes, duplicated `if/elif` ladders, subclasses changing return shapes, fat base classes, hard-coded concrete deps | Each principle satisfied; substitution-safe interfaces at boundaries | Recommended -- propose refactor |
| 9 | **Security & OWASP Top 10 (2021)** | A01..A10 patterns; plaintext secrets; scanner findings | OWASP scan clean; secrets via a secret type only; scanners green | Critical -- must fix (delegates to principal-engineer) |
| 10 | **Valid license scoping** | `SPDX-License-Identifier` on every new source file; `LICENSE` at root; new dependency licenses Allowed; notices updated | Identifiers present; deps Allowed; notices updated | Critical -- automatic reject (delegates to principal-engineer) |
| 11 | **Plagiarism / IP infringement** | Code that looks copied; unattributed snippets; Q&A-site-shaped code | Source identified; license Allowed; original notice preserved | Critical -- if GPL/AGPL/no-license, reject and reimplement |
| 12 | **No restricted-name leakage** | Internal / unreleased product, customer, or partner names in identifiers, strings, comments, tests, configs, logs, commits, docs | Only public names appear in source | Critical -- redact and use a generic placeholder until clearance |
| 13 | **Citations of authoritative sources** | Non-trivial algorithms / methods / patterns from prior art without a source reference | Citation present as arXiv / DOI / official-doc URL / repo permalink | Recommended -- request a citation |
| 14 | **Code duplication** | Repeated 5+ line blocks; reimplementation of an existing helper | No copy-paste duplication; reuse existing helpers | Recommended -- extract helper |
| 15 | **Optimisation opportunities** | Sequential `await` in loops; recomputed work; O(n^2) where a `dict` works; sync I/O in `async def`; unbounded `gather` | No anti-pattern present, or justified with a comment | Recommended -- include expected delta and how to measure |
| 16 | **Ask for clarity** | Ambiguous names, undocumented edge cases, unexplained `# TODO`, intent unclear | Reviewer can explain *why* every change exists | Stop and ask -- never invent intent |

## Verdict bands

| Verdict | Meaning |
|---------|---------|
| **APPROVE** | Zero Critical, zero Block. Recommended items are optional. |
| **REQUEST CHANGES** | One or more Recommended items to address; no Critical. |
| **BLOCK** | Any Critical (#5, #7 for non-trivial logic, #9, #10, #11, #12) or Block (#2, #3, #4, #6) item is failing. |

## Quick-run commands (Python example)

```bash
# Style + types (item 5)
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/

# Tests (item 7)
pytest tests/ -v --tb=short

# Security scans (item 9)
bandit -r src/
pip-audit
gitleaks detect --no-banner

# License audit (item 10)
pip-licenses --format=table --with-license-file --no-license-path

# Commit hygiene (items 3, 4)
git log --oneline -20
git log -1 --pretty=full
```

If any of these commands are not yet wired into CI, that is itself a finding
under item 9 -- raise it as Recommended with the exact config change required.
