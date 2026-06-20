---
name: code-reviewer
aliases:
  - pr-reviewer
  - commit-reviewer
  - diff-reviewer
version: "1.0.0"
description: >-
  Structured 16-point code review for commits and PRs — reviewability budget,
  commit hygiene, style/SOLID, tests, config-docs parity, SPDX/licensing,
  OWASP security, plagiarism screening, and citation enforcement.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "config/**/*.yaml"
  - "config/**/*.json"
  - "config/**/*.toml"
  - "config/**/*.ini"
  - "docs/**/*.md"
  - "pyproject.toml"
  - ".env*"
  - "README.md"
triggers:
  - "code review"
  - "PR review"
  - "review my commit"
  - "review this diff"
  - "review staged changes"
  - "review before push"
  - "review before merge"
  - "check this PR"
delegates_to:
  - principal-engineer
  - clean-code
---

# Code Reviewer

## Purpose

Execute a structured, repeatable 16-point review workflow for commits and pull
requests. Ensure every diff is reviewable in under 30 minutes, carries a
well-formed commit message with author sign-off, meets code-quality and
security standards, and cites authoritative sources for non-trivial logic.

## When to Use

- The user requests a "code review", "PR review", "review my commit", "review
  this diff", "review staged changes", or equivalent.
- A commit is about to be created or pushed.
- A pull request is being opened, updated, or prepared for merge.
- Files in `src/`, `tests/`, `docs/`, `config/`, `pyproject.toml`, or `.env*`
  were modified.

## When NOT to Use

- Pure documentation-only typo fixes with no config or code changes.
- Fast-forward-only merge commits (no conflict resolution code).
- Dependency-lock-file-only updates with no source changes — verify the lock
  file is isolated in its own commit, then skip the full review.

## Instructions

### Review progress tracker

Copy this tracker into your response and mark each phase as you complete it.
Stop and report immediately on the first **Critical** failure; otherwise
complete all phases.

```
Review Progress:
- [ ] Phase 1 — PR reviewability & commit hygiene
- [ ] Phase 2 — Code standards & cleanliness
- [ ] Phase 3 — Tests & documentation parity
- [ ] Phase 4 — Legal, security & IP
- [ ] Phase 5 — Citations & references
- [ ] Final verdict
```

---

### Phase 1 — PR reviewability & commit hygiene

#### 1.1 Size budget

Target: a reviewer clears the diff in **30 minutes or less**.

| PR type | Max diff (LOC changed) | Exception |
|---------|------------------------|-----------|
| Bugfix | 200 | Allowed above 200 only when a test reproducing the bug is included |
| Refactor | 400, **no behavior change** | Split into separate PRs if behavior also changes |
| Net-new feature | 600 + tests | May exceed when the PR description maps each commit to a design section |
| Generated / lock files | Excluded from budget | Must live in their own commit |

When a PR exceeds its budget without justification, request a split. Suggest
specific seams (per-module, per-layer, scaffolding-then-logic) from the diff.

#### 1.2 Commit message format

Enforce the project's commit convention (see `rules/git-commits.md`):

1. **Title <= 80 characters total**, imperative voice, no trailing period.
2. **`type`** is one of: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`,
   `build`, `ci`, `chore`, `revert`, `security`.
3. **`scope`** is the primary touched subsystem.
4. **Body wraps at 72 characters**.
5. **Author sign-off is mandatory** (`git commit -s`).
6. **Why before what** — motivation must be clear from the message alone.

If the commit message does not pass this bar, **block the PR** and propose a
rewritten message.

---

### Phase 2 — Code standards & cleanliness

#### 2.1 Clean code

| Smell | Pass criterion |
|-------|----------------|
| Function length | <= 50 lines (excluding docstring); split if mixing I/O + parsing + business logic |
| Cyclomatic complexity | <= 10 per function; flag deeper nesting |
| Magic numbers / strings | Promote to a named constant or config field |
| Comments narrating code | Delete — comments explain *why*, not *what* |
| Dead code | Delete — no commented-out blocks |
| Naming | Follow the language's idiomatic conventions |

For deep readability judgment, delegate to the `clean-code` skill.

#### 2.2 Linting & type checking

Run the project's configured linter and type checker. For Python (Ruff + mypy):

- Run `ruff check src/ tests/` and `ruff format --check src/ tests/`.
- Run `mypy` in strict mode against the source tree.
- Confirm new files include `from __future__ import annotations`.

#### 2.3 SOLID principles

| Principle | Smell | Example fix |
|-----------|-------|-------------|
| **S**ingle responsibility | A module both fetches data *and* classifies | Split into I/O layer + pure logic layer |
| **O**pen/closed | New variant requires editing a giant `if/elif` ladder | Use a registry or strategy pattern |
| **L**iskov substitution | A subclass changes the return shape | Define a `Protocol`; both must satisfy it |
| **I**nterface segregation | One base class with 12 methods, half unused | Split into focused interfaces |
| **D**ependency inversion | A module imports a concrete implementation directly | Inject an interface-typed dependency |

#### 2.4 Duplication scan

- Search the diff for repeated 5+ line blocks. If found, extract a helper.
- Cross-check: does the change reimplement something that already exists?

#### 2.5 Optimization opportunities

Flag and propose fixes for: sequential `await` in loops (use `asyncio.gather` /
`TaskGroup`), recomputed expensive transforms (cache), re-reading config per
call (`lru_cache`), O(n²) matching (use a `dict`), sync blocking I/O inside
`async def`, unbounded `asyncio.gather` (use a `Semaphore`).

Every optimization suggestion must include: **what to change, expected delta,
and how to measure it**.

#### 2.6 Ask for clarity

If intent is unclear, **stop and ask**. Do not approve and do not invent intent.

---

### Phase 3 — Tests & documentation parity

#### 3.1 Unit-test heuristics

| Code surface | Minimum test |
|--------------|--------------|
| New parser / classifier | Table-driven `parametrize` over (input, expected) |
| New config / settings field | One test asserting default + one asserting env override |
| New connector / client method | Mocked HTTP; assert URL, headers, parsed shape |
| New handler / node | Fixture input in, assert output delta |
| Bug fix | A test that **fails on the base branch** and passes on the fix branch |

If the diff adds non-trivial logic with **zero** new tests, request tests.

#### 3.2 Config-to-documentation parity (mandatory)

Any new or modified configuration in the diff requires a matching documentation
update **in the same PR**. If the documentation update is missing, **block the
PR**. Documentation drift is a defect, not a follow-up.

---

### Phase 4 — Legal, security & IP

Delegate the licensing and security gates to the `principal-engineer` skill for
in-depth analysis. Run those gates, then add the IP checks below.

1. **Licensing gate** — `SPDX-License-Identifier` on every source file; project
   `LICENSE` at repo root; dependency license audit; `THIRD_PARTY_NOTICES.md`
   updated on any dependency change.
2. **Security & secrets gate** — no plaintext tokens; credentials via a secret
   type; `bandit` / `pip-audit` / `gitleaks` clean.
3. **OWASP quick scan** — for any new HTTP / parsing / templating code, walk the
   OWASP Top 10 (2021). Reference: <https://owasp.org/Top10/>.

#### 4.1 Plagiarism / IP-infringement screening

Before approving any non-trivial block (>= 20 LOC of original logic):

- If the code looks copied, **find the source** (code search, official docs).
- Verify the source license is **Allowed**: MIT, BSD-2-Clause, BSD-3-Clause,
  Apache-2.0, ISC. Preserve the original copyright + license notice above the
  imported block and update `THIRD_PARTY_NOTICES.md`.
- If GPL / AGPL / SSPL / no-license: **reject**. Reimplement from spec.
- Stack Overflow / Q&A sites are CC BY-SA — not safe to paste. Reimplement.

#### 4.2 Restricted-name leak detection

Keep internal, proprietary, or unreleased product/customer/partner names out of
source identifiers, string literals, comments, tests, configs, logs, commit
messages, and docs. If unsure whether a name is public, **default to redact**
and use a generic placeholder until clearance is confirmed.

---

### Phase 5 — Citations & references

Any non-trivial algorithm, statistical method, security pattern, or
architectural pattern adopted from prior art **must cite its source** in the
docstring or an adjacent comment. Trivial code is exempt. See `citations.md`.

---

## Output Format

Deliver the review using this exact structure:

```
What works:
- [1-3 specific things done well — always lead with this]

Critical (must fix before merge):
- [File:line] [Problem] -- [Why it matters] -- [Specific fix]

Recommended (should fix, ROI: <estimate>):
- [File:line] [Problem] -- [Trade-off] -- [Fix]

Nice-to-have:
- [Suggestion]

Verdicts:
- Reviewability      : PASS / FAIL
- Style / SOLID      : PASS / FAIL
- Tests              : PASS / FAIL
- Config <-> Docs    : PASS / FAIL
- Legal / Licensing  : PASS / FAIL  (delegates to principal-engineer)
- Security / OWASP   : PASS / FAIL  (delegates to principal-engineer)
- IP / Leakage       : PASS / FAIL
- Citations          : PASS / FAIL

Overall: APPROVE / REQUEST CHANGES / BLOCK
```

Rules for feedback:

1. Always lead with **What works**.
2. Quote `file:line` for every finding. No hand-waving.
3. "Looks good" without specifics is not a review.
4. For every Recommended item, quantify the ROI or state the exact measurement
   that would settle it.

## References

- OWASP Top 10 (2021): <https://owasp.org/Top10/>
- PEP 8: <https://peps.python.org/pep-0008/>
- Conventional Commits: <https://www.conventionalcommits.org/>
- SPDX License List: <https://spdx.org/licenses/>
- Companion files: `checklist.md` (full 16-point matrix), `citations.md`
  (citation source registry).
- Delegated depth: `principal-engineer` (legal, security, async patterns).
