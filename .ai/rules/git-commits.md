# Rule: Commit Messages

Follow Conventional Commits with a mandatory sign-off.

## Anatomy

```
<type>(<scope>): <subject — imperative mood, <= 80 chars total>

<Why this change exists. 1-3 short paragraphs: the problem, the option
chosen, and the trade-offs knowingly accepted.>

<What changed at a high level. Map to key files / modules. Bullets fine.>

<Impact. Behavior delta, perf delta, API delta, migration notes, follow-ups.>

Refs: PROJ-123, GH#456            # optional issue / ticket links
Signed-off-by: Author Name <author@example.com>
```

## Rules

1. **Title <= 80 characters total** (including `type(scope): `). Imperative
   voice. No trailing period.
2. **`type`** is one of: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`,
   `build`, `ci`, `chore`, `revert`, `security`.
3. **`scope`** is the primary touched subsystem (directory or module name).
4. **Body wraps at 72 characters** per line for `git log` readability.
5. **Sign-off is mandatory** — use `git commit -s`. The `Signed-off-by:` line
   asserts the right to contribute under the project license (DCO).
6. **Why before what.** A reviewer must understand the motivation from the
   message alone, without opening the diff.

## Example — good

```
fix(config): mask API key in repr and JSON via secret type

Plaintext bearer tokens were leaking into log output during startup
because the api_key field was a bare str. A secret type masks the
value in __repr__ and JSON serialization, closing the leak without
changing the runtime contract.

- config.py: api_key -> secret type
- client.py: unwrap only at the one HTTP boundary
- tests/test_config.py: assert the value is masked in repr + JSON

Impact: zero behavior change at the HTTP layer; logs are now safe to
attach to bug reports. No migration needed.

Signed-off-by: J. Doe <jdoe@example.com>
```
