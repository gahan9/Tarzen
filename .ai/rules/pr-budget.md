# Rule: Pull Request Budget

A reviewer should clear any diff in **30 minutes or less**. Keep PRs small and
focused on a single logical concern.

| PR type | Max diff (LOC changed) | Exception |
|---------|------------------------|-----------|
| Bugfix | 200 | Allowed above 200 only when a test reproducing the bug is included |
| Refactor | 400, **no behavior change** | Split into separate PRs if behavior also changes |
| Net-new feature | 600 + tests | May exceed when the PR description maps each commit to a design section |
| Generated / lock files | Excluded from budget | Must live in their own commit |

When a PR exceeds its budget without justification, split it. Good seams:

- Per-module or per-layer boundaries.
- Scaffolding first, then logic.
- Pure refactor in one PR, behavior change in the next.

Keep generated files and dependency lock updates in isolated commits so they do
not inflate the reviewable surface.
