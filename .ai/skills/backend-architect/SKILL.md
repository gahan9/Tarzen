---
name: backend-architect
aliases:
  - package-architect
  - service-architect
version: "1.0.0"
description: >-
  Service and package architecture for Python backends — transport layer,
  async connectors with timeout/retry, settings management, shared state models,
  and clean separation between transport, business logic, and integrations.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - "src/**/*.py"
  - "src/**/connectors/**/*.py"
  - "src/**/config.py"
  - "src/**/server.py"
  - "pyproject.toml"
triggers:
  - "service layout"
  - "package layout"
  - "connector"
  - "architecture"
  - "transport layer"
  - "tool registration"
  - "config management"
  - "shared state"
delegates_to:
  - ai-engineer
  - devops-automator
---

# Backend Architect

## Purpose

Own the structural architecture of the Python package: transport layer, request
handling, connector abstraction, configuration management, and shared state.
Enforce clean separation between transport, business logic, and external
integrations.

## When to Use

- Designing or modifying the `src/` package structure.
- Adding or updating request/tool handlers and their mapping to business logic.
- Implementing or refactoring connectors to external systems.
- Defining or evolving shared state models and domain schemas.
- Configuring environment-driven settings.
- Choosing or switching the transport mechanism.

## When NOT to Use

- LLM prompt engineering or threshold tuning (use `ai-engineer`).
- CI/CD or Docker image builds (use `devops-automator`).
- Quality scoring or test evaluation (use `test-quality-evaluator`).
- Frontend or client-side concerns.

## Instructions

### Package structure

Maintain a layered, single-responsibility layout. Example:

```
src/your_package/
├── __init__.py
├── __main__.py          # Entry point: python -m your_package
├── server.py            # Transport setup and request handling
├── config.py            # Settings loader, env-driven configuration
├── pipeline/            # Business-logic orchestration
│   ├── state.py         # Shared state models
│   └── pipeline.py      # Composition / wiring
├── handlers/            # Individual handler implementations
├── models/              # Domain models (validated schemas)
├── connectors/          # External system integrations
│   ├── base.py          # Abstract connector interface
│   └── <system>.py      # Concrete connectors
└── llm/                 # LLM client wrapper
```

Every module has a single clear responsibility. If a file exceeds ~300 lines,
split it.

### Transport layer

- Support the transport modes your runtime needs (e.g. stdio, HTTP/SSE), selected
  via an environment variable.
- The transport handler is a thin translation layer — deserialize input, invoke
  business logic, serialize output. **No business logic in `server.py`.**
- Each handler maps to exactly one business-logic entrypoint.

### Connectors

- All connectors inherit from `connectors/base.py`.
- Connectors use an async HTTP client. Every external call MUST:
  - Have an explicit timeout (default 30s).
  - Implement retry with exponential backoff (max 3 retries).
  - Handle rate-limit responses (HTTP 429) with backoff.
  - Raise typed exceptions on failure (never swallow errors).
- Connectors MUST NOT import business-logic or shared-state modules.

### Shared state & models

- Define the shared state object in one place; it is the single source of truth
  for inter-stage communication.
- Domain models use strict validation (e.g. `ConfigDict(strict=True)`).
- A unified schema normalizes data across multiple external sources.

### Configuration

- All configuration flows through `config.py` using a settings loader.
- Never hard-code URLs, tokens, or credentials. Never log sensitive values.
- Wrap secrets in a secret type; unwrap only at the I/O boundary.

### Design principles

- Validate all inputs at module boundaries (transport entry, connector responses).
- Keep functions small and testable — each does one thing.
- Transport concerns and business-logic concerns must not be co-located.
- Prefer composition over inheritance for connector behavior extension.

## Output Format

- Architecture decisions: brief ADR format (Context → Decision → Consequences).
- Code: typed Python with docstrings, async/await, explicit error handling.
- Models: validated schema classes with field descriptions and examples.
- Configuration: a settings class with documented environment variables.

## References

- `principal-engineer` skill — scalability and packaging gates.
- `ai-engineer` skill — pipeline state and node wiring.
- `devops-automator` skill — runtime/transport deployment.
