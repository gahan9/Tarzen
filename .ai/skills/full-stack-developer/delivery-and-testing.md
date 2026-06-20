# Delivery & Testing Playbook

Reference for testing, version control, CI/CD, containers, deployment, and
observability. Load when shipping or hardening an app. For deep pipeline/infra
ownership, defer to the `devops-automator` skill.

## Testing — match depth to risk

Don't chase 100% coverage; cover what breaks expensively. The classic pyramid:
many fast unit tests, fewer integration tests, a thin layer of E2E on the
critical journeys.

| Layer | Tests what | Tools (JS / Python) |
|-------|------------|---------------------|
| Unit | Pure logic, one function/component | Jest, Vitest / pytest |
| Component | A UI component's behavior | React Testing Library |
| Integration | Modules together, API + DB | Supertest / pytest + test DB, DRF `APITestCase` |
| E2E | Real user flow in a browser | Playwright, Cypress |

Rules:

- **Test behavior, not implementation.** Assert outcomes a user/caller observes,
  not internal calls — so refactors don't break tests.
- Cover the **edge cases and error paths**, not just the happy path: empty inputs,
  bad auth, boundary values, failure responses.
- Tests are **deterministic and isolated** — no shared mutable state, no reliance
  on test order, no live network by default (mock external services; gate real
  integration behind an explicit marker).
- TDD where the design is unclear: red → green → refactor.
- A prototype with no automated tests must still have a documented manual
  run-through in the PR. "I ran it and X happened."
- Never claim "passing"/"done" without actually running the suite and reading the
  output.

## Version control & collaboration

- Small, focused commits; **conventional commit** messages
  (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
- Short-lived feature branches; PRs that explain the **why**, list the change, and
  state the test plan.
- Resolve conflicts deliberately (understand both sides). Keep `main` green and
  releasable.
- Never commit secrets, build artifacts, or `node_modules`/venv. Maintain
  `.gitignore`; if a secret leaks, rotate it.

## CI/CD

A baseline pipeline runs on every PR:

1. Install (cached deps) → 2. Lint + format check → 3. Type-check →
4. Test → 5. Build → 6. (on merge) Deploy.

- Fail fast and loudly; a red pipeline blocks merge.
- Pin dependency versions (lockfiles) for reproducible builds.
- Run security scans in CI (`npm audit`/`pip-audit`, dependency review, secret
  scanning).
- Keep secrets in the CI provider's secret store, injected as env vars.
- Tools: GitHub Actions / GitLab CI. Promote build artifacts through
  environments; don't rebuild per stage.

## Containers (Docker)

- One concern per image; small base (`-slim`/`-alpine`), **multi-stage builds** to
  drop build tooling from the runtime image.
- Pin base image tags; run as a **non-root** user; never bake secrets into layers
  (use build args/runtime env/secret mounts).
- Order layers for cache reuse (dependencies before source). Add a `.dockerignore`.
- `docker-compose` for local multi-service dev (app + db + cache). Define a
  `HEALTHCHECK`.

## Environments & configuration

- **Config via environment, not code.** Same image across dev/staging/prod;
  behavior differs by env vars only (12-factor).
- Distinct dev / staging / prod with separate credentials and data.
- Secrets from a manager (Vault, cloud KMS/Secrets Manager) in prod; `.env`
  (gitignored) only locally.

## Deployment

- Choose by needs: managed platforms (Vercel/Netlify for frontends; Render,
  Railway, Fly, Heroku for full-stack) get you live fast; cloud (AWS/GCP/Azure)
  or Kubernetes when you need the control and can staff the ops.
- Prefer **zero-downtime** strategies (rolling/blue-green) and keep a fast
  rollback. Decouple DB migrations from code deploys (expand/contract).
- Serve over HTTPS; terminate TLS at the edge/load balancer; set security headers.

## Observability (required before "production")

- **Structured logs** (JSON) with levels and correlation/request IDs; never log
  secrets or PII.
- **Error tracking** (Sentry or equivalent) wired on client and server.
- **Health/readiness endpoints** for the orchestrator/load balancer.
- At least one metric and one alert that prove the core flow works and page a
  human when it doesn't. Track the user-facing SLI (latency, error rate).

## Pre-ship checklist

- [ ] Lint, type-check, and tests pass locally and in CI (actually run)
- [ ] Critical paths have integration/E2E coverage; edge cases tested
- [ ] No secrets in source, image layers, or logs; deps pinned and audited
- [ ] Config via env; staging/prod separated; HTTPS enforced
- [ ] Migrations reversible and decoupled from the code deploy
- [ ] Structured logs, error tracking, health check, and one real alert in place
- [ ] Rollback path verified
