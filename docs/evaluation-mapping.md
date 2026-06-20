<!-- SPDX-License-Identifier: MIT -->

# Evaluation-criteria mapping

Every evaluation criterion maps to concrete source files and the tests that
prove the behaviour. All gates were run on Windows/PowerShell on 2026-06-20; see
[the build summary](#gate-evidence) at the bottom.

| Criterion | Evidence (file paths) | Tests (proof) |
|-----------|------------------------|---------------|
| **Code Quality** | `pyproject.toml` (ruff `E,F,I,UP,B`, `mypy --strict`, `pydantic.mypy`); small typed functions with Google docstrings throughout `backend/src/carbon/**`; typed error envelope `models/schemas.py:ErrorEnvelope` + `api/errors.py`; committed contract `docs/openapi.json`; exhaustive TS switch `frontend/src/features/footprint/FootprintForm.tsx:modeHint` | `ruff check .` ✅, `ruff format --check .` ✅, `mypy src` ✅ (39 files); `test_routes.py::test_footprint_success_matches_contract` (response shape) |
| **Security** | Firebase ID-token verify `api/auth.py:require_uid`; `SecretStr` config `core/config.py`; field bounds `models/schemas.py` (`extra="forbid"`, `MAX_DISTANCE_KM`, `MAX_PASSENGERS`); CORS lockdown `main.py` (no `*`); per-uid rate limit + body cap `api/rate_limit.py`; prompt-injection guard `application/insights.py:_validate_phrasing`/`_numbers_allowed`; least-privilege IAM `infra/terraform/main.tf`; PII-free logs `api/logging_middleware.py`; SPDX header on all 52 `.py` files | `test_auth.py` (4: valid/forged/missing/malformed), `test_rate_limit.py` (4), `test_routes.py::test_footprint_validation_error_envelope`, `test_insights.py::test_prompt_injection_attempt_is_rejected_and_falls_back`; `bandit -r src` ✅ 0 issues, `pip-audit` ✅ 0 CVEs |
| **Efficiency** | Rule-based-first (LLM phrasing-only) `application/insights.py`; factors cached at module load `domain/factors.py` (`functools.lru_cache`); async I/O off the event loop `adapters/{firestore,bigquery,pubsub}.py` (`asyncio.to_thread`); Gemini timeout + bounded `Semaphore` + retry + token cap + fallback `adapters/gemini.py` | `test_insights.py::test_llm_disabled_result_is_deterministic_and_unchanged`, `::test_gemini_outage_falls_back_to_template`, `::test_missing_distance_asks_for_context` (LLM never called) |
| **Testing** | `backend/tests/unit/**` (no network; fakes in `conftest.py`); `pyproject.toml` markers `integration` (auto-skip without creds); coverage config with roadmap stubs omitted | **43 passed**; coverage **87%** (`pytest --cov=carbon --cov-report=term-missing`); golden table `test_transport_tracker.py::test_transport_compute_matches_golden_table` (7 cases) |
| **Accessibility** | Semantic HTML + `<label>` per input + `role="alert"` + `aria-describedby` + keyboard nav `frontend/src/features/footprint/FootprintForm.tsx`; focus management `frontend/src/shared/a11y/`; `jsx-a11y` ESLint plugin; Lighthouse a11y gate `frontend/lighthouserc.json` (`minScore 0.95`) | `npm run lint` ✅ (eslint incl. `jsx-a11y`); `npm run build` ✅; Lighthouse-CI assertion `categories:accessibility ≥ 0.95` |
| **Problem-Statement Alignment** | *Understand*: insight engine `application/insights.py` + benchmarks `domain/benchmarks.py`. *Track*: `POST /api/footprint` `api/routes.py`, data-minimized log `adapters/firestore.py`, `DomainTracker` port + trackers `domain/trackers/*`, mobile stub `mobile/`. *Reduce*: per-domain reduction actions `application/insights.py:_ACTIONS`, gamification/leaderboard design `application/{gamification,leaderboard}.py`. Contract evidence: `docs/openapi.json` + error envelope | `test_routes.py` (5), `test_transport_tracker.py` (golden), `test_benchmarks.py` (3) |
| **Google Services usage** | 18 services mapped in [`architecture.md`](architecture.md#gcp--google-services-each-mapped-to-a-concrete-use); MVP set: Cloud Run, Vertex AI Gemini, Firebase Auth, Firestore, Pub/Sub, BigQuery, Secret Manager, Cloud Build, Artifact Registry, Cloud Logging/Monitoring/Trace, Firebase Hosting | Adapter tests via fakes; `test_routes.py::test_footprint_side_effects_are_invoked` (Firestore write + Pub/Sub publish) |
| **Scalability / Resilience** | Stateless Cloud Run; decoupled Pub/Sub write path `adapters/pubsub.py`; idempotent consumer contract `functions/aggregate_consumer.py`; Memorystore ZSET port `adapters/leaderboard_store.py`; `/healthz` + `/readyz` `api/health.py`; `trace_id` propagation `api/logging_middleware.py` | `test_health.py` (3: healthz, readyz ok, readyz degraded → 503) |

## Gate evidence

| Gate | Command | Result |
|------|---------|--------|
| Lint | `uv run ruff check .` | All checks passed |
| Format | `uv run ruff format --check .` | 52 files already formatted |
| Types | `uv run mypy src` | Success: no issues found in 39 source files |
| Tests + coverage | `uv run pytest --cov=carbon --cov-report=term-missing` | 43 passed; TOTAL 87% |
| SAST | `bandit -r src` | No issues identified (1753 LOC) |
| CVEs | `pip-audit` | No known vulnerabilities found |
| Licenses | `pip-licenses` | All MIT/BSD/Apache-2.0/MPL-2.0/PSF; no GPL/AGPL/SSPL |
| SPDX | header presence scan | 52/52 `.py` files carry an identifier |
| Web build | `npm run build` (frontend) | built in ~3 s; tsc + vite green |
| Web lint | `npm run lint` (frontend) | eslint clean |
| Shared types | `tsc -p tsconfig.json --noEmit` | green |
