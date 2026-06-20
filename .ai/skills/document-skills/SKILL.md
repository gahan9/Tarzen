---
name: document-skills
aliases:
  - docx
  - pdf
  - pptx
  - xlsx
  - office-docs
version: "1.0"
description: >-
  Pointer skill for creating, editing, and analyzing Office and PDF documents
  (.docx, .pdf, .pptx, .xlsx). This template does not vendor proprietary
  document tooling; instead it directs the agent to load the platform's own
  official document skill at runtime, or to use permissively licensed libraries.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - "**/*.docx"
  - "**/*.pdf"
  - "**/*.pptx"
  - "**/*.xlsx"
  - "**/*.xlsm"
  - "**/*.csv"
license: MIT
---

# Document Skills (Pointer)

## Purpose
Provide a discoverable entry point for document tasks (Word, PDF, PowerPoint,
Excel) without bundling proprietary, license-restricted tooling into this
portable template.

## Why this is a pointer, not a vendored skill
Anthropic's official `docx`/`pdf`/`pptx`/`xlsx` skills are licensed
"all rights reserved" and forbid copying, retaining copies outside Anthropic's
services, and creating derivative works. Vendoring them would violate
`.ai/rules/security.md` (no proprietary/incompatible-licensed content) and the
template's "publicly shareable" goal. This skill therefore points to runtime
options instead of re-hosting that content.

## When to Use
- Creating, editing, or analyzing `.docx`, `.pdf`, `.pptx`, `.xlsx` files.
- Extracting text/tables, filling PDF forms, or generating reports.

## Instructions
1. **Prefer the platform's native document skill at runtime.** If the running
   assistant (e.g. Claude) ships an official `docx`/`pdf`/`pptx`/`xlsx` skill,
   load and follow it there. Do not copy that skill's content into this repo.
2. **Otherwise use permissively licensed libraries** (all MIT/BSD/Apache-2.0):
   - DOCX: `python-docx`.
   - XLSX: `openpyxl` (read/write, formulas, styles); `pandas` for analysis.
   - PPTX: `python-pptx`.
   - PDF: `pypdf` (merge/split/extract), `pdfplumber` (text/tables),
     `reportlab` (generation), `pypdfium2` (render to image).
3. **Validate output**: open generated files and confirm zero corruption; for
   spreadsheets confirm zero formula errors (`#REF!`, `#DIV/0!`, `#VALUE!`,
   `#N/A`, `#NAME?`) before delivery.
4. Add any new runtime dependency to the project's dependency manifest and to
   `THIRD_PARTY_NOTICES.md`, and confirm its license is on the allowlist
   (MIT, BSD-2/3-Clause, Apache-2.0, ISC).

## When NOT to Use
- Do not vendor or paste proprietary document-skill content into this repo.

## Output Format
Deliver the requested document file plus a short note on the library used and
any validation performed.

## References
- `.ai/rules/security.md` — licensing allowlist and IP hygiene.
- python-docx, openpyxl, python-pptx, pypdf, pdfplumber, reportlab docs.
