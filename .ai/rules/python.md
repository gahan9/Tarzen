# Rule: Python Standards

Applies to all `**/*.py`. These are always-on conventions for Python code.

## Style & formatting

- Follow **PEP 8**. Line length **88** (Black/Ruff default).
- Names: `snake_case` functions/variables, `PascalCase` classes,
  `UPPER_SNAKE` constants.
- Google-style docstrings on all public functions and classes.
- Run `ruff check` and `ruff format --check` before considering work done.

## Typing

- Add `from __future__ import annotations` at the top of every module.
- Type hints on all public APIs. Run `mypy --strict` on the source tree.
- No `import *`. Imports are explicit.

## Error handling

- No bare `except:` — always catch specific exceptions.
- Never silently swallow errors; log with context or re-raise as a typed error.

## Async-first I/O

- All I/O-bound code is `async`. Never call blocking I/O inside `async def`;
  use `asyncio.to_thread()` for legacy sync libraries.
- Bound concurrency with `asyncio.Semaphore` to prevent connection storms.
- Prefer `asyncio.TaskGroup` (3.11+) over raw `gather` for structured errors.
- Every network call has an explicit timeout.

## Logging

- No `print()` in library code — use the standard `logging` module or a
  structured logger. CLIs may print to stdout.

## Packaging

- `pyproject.toml` (PEP 621) only — no `setup.py` / `setup.cfg`.
- Use a `src/` layout. Ship `py.typed` for typed packages.
- Pin dependencies to a minimum version (`>=`), not exact (`==`) unless justified.

## Environment

- Use `uv` for environment and dependency management.
- Prefix Python commands with `uv run` so they execute inside the project venv.
