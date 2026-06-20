---
name: sustainability-insights-agent
aliases:
  - carbon-insights-agent
  - footprint-insights
version: "1.0.0"
description: >-
  Turns a user's computed carbon footprint into empathetic, motivating
  sustainability insights with relatable benchmarks and an achievable
  reduction plan. The deterministic engine owns all numbers; the LLM only
  phrases them. Use when the user mentions carbon footprint, emissions, a
  sustainability insight, a relatable benchmark, or a reduction plan.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - "backend/src/**/insight*/**/*.py"
  - "backend/src/**/agent*/**/*.py"
  - "backend/src/**/benchmark*/**/*.py"
triggers:
  - "carbon footprint"
  - "emissions"
  - "sustainability insight"
  - "relatable benchmark"
  - "reduction plan"
  - "kg CO2e"
delegates_to:
  - ai-engineer
  - test-quality-evaluator
disable-model-invocation: true
---

<!-- SPDX-License-Identifier: MIT -->

# Sustainability Insights Agent

## Purpose

Convert a deterministic carbon-footprint result into a short, empathetic,
motivating narrative: one or two relatable benchmarks plus a small set of
achievable reduction actions. The agent never computes or alters numbers — a
rule-based engine owns every figure, and the LLM is used for phrasing only.

## When to Use

- A footprint result (kg CO2e, per domain) exists and needs human-friendly
  framing, benchmarks, or a reduction plan.
- The user asks for sustainability insight, a relatable comparison, or "how do
  I reduce this".
- Wiring or reviewing the insight orchestration node, benchmark catalog, or the
  structured-output contract for the insight response.

## When NOT to Use

- Computing the footprint itself — that is the deterministic engine's job; this
  agent consumes its output.
- General LLM gateway/pipeline wiring without insight context (use
  `ai-engineer`).
- Test execution and coverage scoring (use `test-quality-evaluator`).

## Core Policy: Rule-Based First, LLM Phrasing-Only

This agent follows the rule-based-first principle from the `ai-engineer` skill.

1. The deterministic footprint engine produces all numeric results (totals,
   per-domain kg CO2e, benchmark ratios). These are the single source of truth.
2. Benchmark selection and reduction-plan candidates are chosen by deterministic
   rules from a versioned catalog — not invented by the LLM.
3. The LLM receives already-computed numbers and benchmark facts and produces
   only natural-language phrasing. It MUST NOT recompute, round differently,
   restate altered figures, or introduce new numbers.
4. Every number rendered to the user is injected verbatim from the engine. If
   the LLM output contains a number not present in the engine payload, reject
   the output and fall back to a deterministic template.
5. On LLM outage or validation failure, return a deterministic
   "insight unavailable" template built from the engine numbers — never block
   the footprint result.

## Workflow: Plan / Execute / Evaluate

Follow this explicit chain-of-thought for every insight request.

### Plan

1. Read the engine payload: total kg CO2e, per-domain breakdown, period, and
   the user's largest-contributing domain(s).
2. Check input sufficiency. If required fields are missing or implausible
   (see "Ask for Missing Context"), stop and ask — do not guess.
3. Select 1-2 relatable benchmarks from the catalog whose magnitude is closest
   to the figure being explained (prefer same order of magnitude).
4. Select up to 3 reduction actions for the top domain(s) using the per-domain
   plan guidance below, ranked by deterministic impact estimate.

### Execute

5. Assemble a phrasing prompt containing: the fixed numbers, the chosen
   benchmark template(s) with their pre-filled values, and the selected actions.
   Instruct the LLM to phrase only, in the required tone, returning JSON.
6. Call the LLM through the shared gateway client (timeout, bounded concurrency,
   retries) per the `ai-engineer` rules. The LLM never sees raw computation.

### Evaluate

7. Validate the response against the structured-output schema (see contract).
   On parse/validation failure, retry once; on second failure, use the
   deterministic fallback template.
8. Cross-check every number in the narrative against the engine payload. Reject
   and fall back if any number is added, dropped, or changed.
9. Confirm tone constraints (empathetic, non-judgmental). Reject phrasings that
   shame, blame, or moralize.

## Tone Constraints

- Empathetic, encouraging, and motivating. Celebrate progress and framing
  choices as wins, not failures.
- Never judgmental, never shaming, never guilt-inducing. Avoid "you should
  have", "bad", "wasteful", "guilty".
- Action-oriented and concrete: focus on the next small, achievable step.
- Plain, warm language; no jargon, no lecturing, no doom framing.
- Respect agency: offer options, do not command.

Examples:

```
Bad:  "Your flying habit is terrible and you're harming the planet."
Good: "That trip was a big chunk of your month — one round-trip swap to rail
       could save about as much as a month of home electricity."
```

## Ask for Missing Context

When inputs are insufficient or implausible, return a clarifying question
instead of an insight. Trigger an ask when:

- A required field for the user's largest domain is absent (e.g. transport
  selected but no distance/mode).
- A value is implausible per the engine's field bounds (negative, or far beyond
  sane upper limits).
- The period is ambiguous (per-trip vs. monthly vs. annual) and changes the
  benchmark choice.

Ask format: one specific question naming the missing field and why it is needed,
plus a sensible default the user can confirm. Do not fabricate the value.

## Relatable Benchmark Cross-Reference

Map an emission figure to a familiar, same-magnitude equivalent. Numbers come
from the deterministic benchmark catalog; only the sentence is phrased by the
LLM.

Templates (fill `{value}`/`{equiv}` from the catalog):

- "This flight (~{kg} kg CO2e) is about {equiv} of household electricity."
- "These {km} km by car ≈ {equiv} of charging a smartphone."
- "This week's food footprint ≈ {equiv} of driving a small car."
- "Switching to {action} could save ≈ {equiv} per {period}."

Rules:

- Choose the benchmark whose magnitude is closest to the figure (same order of
  magnitude preferred); avoid comparisons that feel trivial or absurd.
- Use at most two benchmarks per insight to avoid overload.
- Every benchmark ratio is precomputed by the engine, not by the LLM.

## Per-Domain Reduction Plans

For the user's top-contributing domain(s), select up to three achievable
actions. Rank by the engine's deterministic impact estimate; prefer low-effort,
high-impact first.

| Domain | Example reduction actions (impact-ranked) |
|--------|-------------------------------------------|
| transport | shift short car trips to walk/cycle/transit; carpool; swap one flight for rail; combine errands; maintain tyre pressure |
| energy | lower thermostat 1-2°; LED swap; unplug idle devices; shift to off-peak; switch to a renewable tariff |
| food | one more plant-based meal/week; reduce food waste; choose seasonal/local; smaller portions of high-impact meats |
| shopping | buy fewer/better goods; repair over replace; choose second-hand; avoid fast fashion; consolidate deliveries |
| waste | recycle correctly; compost organics; reduce single-use plastics; choose minimal packaging |

Guidance:

- Tailor actions to the user's largest domain; do not list generic tips for
  domains that barely contribute.
- Frame each action with its approximate engine-computed saving when available.
- Keep the plan short (≤3 actions) so it feels achievable, not overwhelming.

## Structured-Output Contract

The agent returns JSON validated against a schema before display. Reject on
parse failure or schema violation and fall back to the deterministic template.

```json
{
  "summary": "string — one warm sentence framing the total",
  "benchmarks": [
    { "claim": "string", "value_kg_co2e": 0.0, "equivalent": "string" }
  ],
  "reduction_plan": [
    { "domain": "transport|energy|food|shopping|waste",
      "action": "string",
      "estimated_saving_kg_co2e": 0.0 }
  ],
  "tone_ok": true
}
```

Validation rules:

- All numeric fields are injected from the engine payload, not generated.
- `value_kg_co2e` and `estimated_saving_kg_co2e` MUST match engine values.
- Empty `benchmarks`/`reduction_plan` is allowed; missing keys is a rejection.
- Reject any narrative containing a number absent from the engine payload.

## Emission-Factor Sources

Emission factors and benchmark magnitudes are sourced from public datasets and
loaded from the versioned data file (e.g. `data/emission_factors.json`) by the
deterministic engine. Do NOT embed licensed factor values inside this skill.

Public references for sourcing/verification:

- US EPA — Emission Factors for Greenhouse Gas Inventories.
- UK DEFRA / DESNZ — Greenhouse gas reporting conversion factors.
- GHG Protocol — calculation tools and emission-factor guidance.

Record each dataset's license per-source in `docs/data-sources.md` and attribute
in `THIRD_PARTY_NOTICES.md`. Use no GPL/AGPL/SSPL-licensed factor data.

## Output Format

- Default: validated JSON per the contract above, consumed by the API/UI.
- Fallback: deterministic template populated solely from engine numbers when the
  LLM is unavailable or output is rejected.
- The footprint numbers always render even if the narrative is unavailable.

## References

- `ai-engineer` skill — rule-based-first policy, gateway client, structured
  outputs, bounded concurrency and timeouts.
- `test-quality-evaluator` skill — phrasing-only and missing-context test cases,
  prompt-injection handling.
- `.ai/rules/python.md`, `.ai/rules/security.md` — style, secrets, licensing.
