# Rule: Security & Licensing

Always-on. Violations block merge.

## Secrets (non-negotiable)

- **No plaintext secrets** in source code, comments, docstrings, tests, configs,
  logs, or CLI `--help` output. Ever.
- Load credentials from environment variables or a secret manager. Wrap them in
  a secret type (e.g. `pydantic.SecretStr`) and unwrap only at the I/O boundary.
- `.env` files are **gitignored** and blocked by `guard-env-files.py`
  (fail-closed). Commit a `.env.example` with placeholder values only.
- Never log a secret at any level. Never return a secret in an error payload.
- Never pass a raw credential across module boundaries — inject settings once.

### `.gitignore` baseline

```
.env
.env.*
!.env.example
*.pem
*.key
credentials.json
secrets.yaml
token.txt
```

## Licensing

- Every source file declares its license via an SPDX identifier, e.g.
  `# SPDX-License-Identifier: MIT` as the first or second line.
- A `LICENSE` file exists at the repo root and matches the SPDX identifier.
- **Allowed dependency licenses**: MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC.
- **Blocked**: GPL, AGPL, SSPL, BSL, Commons Clause, and any "no license" /
  unknown package. Copyleft contaminates permissively licensed code.
- On any dependency change, update `THIRD_PARTY_NOTICES.md`.

## IP hygiene

- Do not copy code without an identified, compatible-license source. Stack
  Overflow snippets (CC BY-SA) are not safe to paste — reimplement.
- Keep proprietary, internal, or unreleased product/customer names out of source,
  tests, configs, commit messages, and docs. Use generic placeholders.

## Scanning (wire into CI)

- `bandit` — Python SAST.
- `pip-audit` / `safety` — dependency CVEs.
- `gitleaks` / `trufflehog` — secret scanning across history.
- `pip-licenses` / `liccheck` — license audit.
