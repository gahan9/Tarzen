<!-- SPDX-License-Identifier: MIT -->

# AI tool usage (submission essentials)

This document covers the challenge's Submission Essentials: which AI tools were
used and why, the architecture + prompt-flow, what GenAI handled versus what
humans designed, and a LinkedIn-ready narrative.

## AI tools used and why

| Tool | Role in the project | Why |
|------|---------------------|-----|
| **AI coding assistant (agentic IDE)** | Scaffolding the hexagonal backend, frontend, infra, tests, and docs under human-authored rules/skills | Speed on boilerplate and consistency with a single source-of-truth config in `.ai/` |
| **Google Vertex AI — Gemini** | *Runtime* feature: phrasing-only "Sustainability Insights Agent" that turns computed numbers into warm, non-judgmental copy | Empathetic, relatable language is exactly what an LLM is good at — and exactly where determinism is *not* required |
| **Project rules + skills** (`.ai/rules/*`, `.ai/skills/sustainability-insights-agent/SKILL.md`) | Encode style, security, testing, PR-budget, and the agent's tone/policy contract so AI output stays in-bounds | Makes AI assistance auditable and repeatable across Cursor/Claude/Copilot/Codex/Antigravity adapters |

## Architecture + prompt-flow

The agent follows an explicit **Plan → Execute → Evaluate** chain
(`backend/src/carbon/application/insights.py`):

1. **Plan**: if required data is thin (e.g. `distance_km <= 0`) the engine
   short-circuits to an *ask-for-context* response and never calls the LLM.
   Otherwise it computes the deterministic footprint and selects a relatable
   benchmark (`domain/benchmarks.py`).
2. **Execute**: it builds a constrained prompt — a system prompt that declares
   every payload value a fixed fact and forbids following embedded instructions,
   plus a user prompt carrying the `fixed_facts` and `candidate_actions` to
   *rephrase only*. Gemini runs with an 8 s timeout, bounded concurrency, ≤ 2
   retries, and a 512-token cap (`adapters/gemini.py`).
3. **Evaluate**: the JSON output is validated against a Pydantic schema
   (`models/insight.py:GeminiPhrasing`); every number in it must match an
   engine-produced value (numeric allow-list) and `tone_ok` must be true.
   Anything else is rejected and a deterministic template is returned with
   `llm_used=false`. On any Gemini outage the same fallback applies.

```
request → deterministic engine (numbers) → policy gate
        → [allowed] Gemini phrasing → schema + numeric-allow-list validation
        → [pass] warm copy   |   [fail/outage] deterministic template
```

## What GenAI handled vs what humans designed

| GenAI handled | Humans designed / own |
|---------------|------------------------|
| Empathetic phrasing of insight copy (and only that) at runtime | The deterministic footprint math, emission factors, and benchmark catalogue |
| First-draft scaffolding of modules, tests, and docs | Hexagonal architecture, port/adapter boundaries, and the DI container |
| Boilerplate (Pydantic models, FastAPI wiring, TS forms) | The security model: auth, rate limits, CORS, prompt-injection guard, PII minimization, least-privilege IAM |
| Repetitive test bodies from a stated table | Golden-table values, test strategy, and coverage gating |
| Suggested copy and structure for these docs | The evaluation-mapping, threat model, data governance, and dataset-license decisions |

Critically, **no number a user sees comes from the LLM** — GenAI only rephrases
facts the deterministic engine produced. Every AI-assisted change passed the
same gates a human change must: ruff, `mypy --strict`, pytest (87% coverage),
bandit, pip-audit, license audit, and SPDX checks.

## LinkedIn-ready narrative

> I built a Carbon Footprint Awareness Platform on Google Cloud that helps people
> *understand, track, and reduce* everyday emissions — and I used AI the way I
> think it should be used in production: as a careful collaborator, not an oracle.
>
> The footprint math is 100% deterministic, driven by versioned public emission
> factors (UK DEFRA/DESNZ 2024, OGL v3.0). Google's Gemini (Vertex AI) only ever
> *rephrases* those computed facts into warm, non-judgmental coaching — and a
> validation layer rejects any model output that invents a number or breaks tone,
> falling back to a deterministic template. So the AI can make the experience
> kinder, but it can never make the data wrong.
>
> Under the hood: a hexagonal FastAPI backend on Cloud Run, Firebase Auth,
> Firestore (data-minimized), Pub/Sub + Cloud Functions for an event-driven write
> path, BigQuery (aggregate-only) for analytics, and least-privilege IAM — 18
> Google services mapped to concrete uses. It ships with a threat model
> (prompt-injection, token replay, cost-DoS, over-posting, PII leakage), 43 tests
> at 87% coverage, and clean SAST/CVE/license gates.
>
> An AI assistant accelerated the boilerplate; the architecture, security model,
> and evaluation evidence are human-owned. That combination — speed from AI,
> judgment from engineering — is how I want to build.
