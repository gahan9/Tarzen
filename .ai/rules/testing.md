# Rule: Testing

Use `pytest`. Tests are part of the change, not a follow-up.

## Tiers

- **Unit** (`tests/unit/`): isolated logic, < 1s per test, no network.
- **Integration** (`tests/integration/`): component interaction; mark with
  `@pytest.mark.integration`; skip automatically when credentials are absent.
- **End-to-end** (`tests/e2e/`): full flow against fixtures.

Tag tiers with `pytest.mark` so they can be selected and gated independently.

## Expectations

- New non-trivial logic ships with at least one direct test.
- Bug fixes ship with a test that **fails on the base branch** and passes on the fix.
- Mock external clients (HTTP, LLM, DB) in unit tests — never hit live services in CI.
- Prefer table-driven `pytest.mark.parametrize` for classifiers and parsers.
- Use deterministic fixtures; seed any randomness.

## Coverage

- Target **>= 80%** line coverage on changed code. Treat a drop as a defect.
- Run: `pytest -x --cov=src --cov-report=term-missing`.

## Naming

- `test_<unit>_<scenario>_<expected_outcome>`.
