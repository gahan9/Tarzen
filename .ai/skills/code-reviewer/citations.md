# Citation Source Registry

Reference for the `code-reviewer` skill, Phase 5. Use this when deciding **what
counts as an authoritative source** for a non-trivial block of code, and how to
format the citation in a source file.

A citation is required for any non-trivial algorithm, statistical method,
security pattern, or architectural pattern adopted from prior art. Trivial
boilerplate, glue, and well-known idioms are exempt.

## Acceptable source classes

Listed in descending order of preference. One source is enough; pick the one
closest to where the idea originally came from.

### 1. Peer-reviewed research (highest signal)

| Venue | How to cite |
|-------|-------------|
| **arXiv** — <https://arxiv.org/> | `# Vaswani et al., "Attention Is All You Need", arXiv:1706.03762` |
| **IEEE Xplore** — <https://ieeexplore.ieee.org/> | `# Smith et al., IEEE Trans. Computers 2021, DOI 10.1109/TC.2021.xxxxxxx` |
| **ACM Digital Library** — <https://dl.acm.org/> | `# Author et al., "Title", SOSP '23, DOI 10.1145/xxxxxxx.xxxxxxx` |
| **ScienceDirect / Elsevier** — <https://www.sciencedirect.com/> | `# Salton & Buckley, IP&M 1988, DOI 10.1016/0306-4573(88)90021-0` |
| **USENIX** — <https://www.usenix.org/publications> | `# Author et al., USENIX OSDI '23, https://www.usenix.org/conference/osdi23/presentation/<slug>` |
| **JMLR / TMLR** — <https://jmlr.org/> | `# Author et al., JMLR 24(123):1-30, 2023, https://jmlr.org/papers/v24/<id>.html` |
| **OpenReview** — <https://openreview.net/> | `# Author et al., ICLR 2024, https://openreview.net/forum?id=<id>` |

### 2. Official framework / library documentation

Cite a **versioned URL** so the link cannot silently shift meaning.

```python
# Pattern: a secret type that masks credentials in repr / JSON.
# Source: https://docs.pydantic.dev/latest/concepts/types/#secret-types
api_key: SecretStr = SecretStr("")
```

### 3. High-signal open-source reference repositories

Cite a **repo + path + permalinked commit** so the snippet is reproducible.
Format: `<org>/<repo> @ <short-sha> : <path>`.

```python
# Pattern adapted from <org>/<repo> @ a1b2c3d :
# path/to/source.py -- <brief note on what was adapted>
```

## Sources that are NOT acceptable on their own

| Source | Why insufficient | What to do instead |
|--------|------------------|--------------------|
| Stack Overflow / Stack Exchange | License is **CC BY-SA** — incompatible with permissive code | Reimplement citing the official doc or paper the answer references |
| Random blog posts / Medium | Not version-stable; often unreviewed; license unclear | Use only as a hint; cite the underlying paper / doc / repo |
| LLM output without verification | Cannot be cited; provenance unknown | Verify against an authoritative source before merging |
| Wikipedia | OK for a *concept definition*; not for an *algorithm implementation* | Follow Wikipedia's references back to the primary source and cite that |
| Personal repos with no license file | "No license" = all rights reserved; copying is infringement | Reject; reimplement |

## Citation placement

Place the citation comment **immediately above** the function, class, or block
it justifies. For module-wide patterns, place it in the module docstring.

```python
# SPDX-License-Identifier: MIT
"""TF-IDF similarity for document retrieval.

Algorithm: term-frequency * inverse-document-frequency with sublinear TF
scaling and L2-normalised vectors.

References:
    - Salton & Buckley, "Term-weighting approaches in automatic text
      retrieval", Information Processing & Management 24(5), 1988.
      DOI: 10.1016/0306-4573(88)90021-0
"""
```

## When in doubt

If the reviewer cannot find a source for a non-trivial block within five minutes
of search, that itself is the finding. Ask the author to produce the citation;
if they cannot, the code is unverified and should not merge until provenance is
established or the block is reimplemented from a known source.
