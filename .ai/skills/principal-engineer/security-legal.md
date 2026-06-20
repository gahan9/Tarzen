# Security, Secrets Management & Legal Compliance Reference

On-demand detailed reference for the `principal-engineer` skill. Read this file
when you need specific templates, CI configurations, secret-manager integration
patterns, or license audit procedures.

---

## 1. SPDX License Header Templates

Every source file begins with an SPDX identifier **before any code or imports**.
Use the identifier that matches the repo `LICENSE`.

```python
# SPDX-License-Identifier: MIT
```

```rust
// SPDX-License-Identifier: MIT
```

```bash
#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
```

```toml
# SPDX-License-Identifier: MIT
```

```markdown
<!-- SPDX-License-Identifier: MIT -->
```

If a project also requires a copyright line, add it above the SPDX line using the
project's chosen holder and year. This template enforces SPDX presence only.

---

## 2. LICENSE File

Place at the repo root. Must match the SPDX identifier used in headers. Use a
standard text from <https://spdx.org/licenses/> (MIT, Apache-2.0, BSD-3-Clause,
etc.) and fill in the copyright holder and year.

---

## 3. Dependency License Audit

### Automated audit with pip-licenses

```bash
pip install pip-licenses
pip-licenses --format=table --with-urls --order=license
```

### CI enforcement with liccheck

```toml
[tool.liccheck]
authorized_licenses = [
    "MIT", "MIT License",
    "BSD", "BSD License", "BSD-2-Clause", "BSD-3-Clause",
    "Apache Software License", "Apache-2.0",
    "ISC", "ISC License",
    "Python Software Foundation License", "PSF",
]
unauthorized_licenses = [
    "GPL", "GPLv2", "GPLv3", "GNU General Public License",
    "AGPL", "AGPLv3",
    "Server Side Public License", "SSPL",
    "Business Source License", "BSL",
]
```

### THIRD_PARTY_NOTICES.md template

```markdown
# Third-Party Notices

This project uses the following third-party libraries:

| Package | Version | License | Copyright |
|---------|---------|---------|-----------|
| example-lib | 1.x | MIT | Example Author |

Generated with: `pip-licenses --format=markdown`
```

---

## 4. Secure Secret Storage Patterns

### Priority 1: Secret manager (production)

```python
# HashiCorp Vault
import hvac, os

def get_secret(path: str, key: str) -> str:
    client = hvac.Client(url=os.environ["VAULT_ADDR"], token=os.environ["VAULT_TOKEN"])
    secret = client.secrets.kv.v2.read_secret_version(path=path)
    return secret["data"]["data"][key]
```

Cloud equivalents: Azure Key Vault (`azure-keyvault-secrets`), AWS Secrets
Manager (`boto3`), GCP Secret Manager (`google-cloud-secret-manager`).

### Priority 2: System keyring (developer workstations)

```python
import keyring

keyring.set_password("myapp", "api_token", "...")
token = keyring.get_password("myapp", "api_token")
```

Backends: macOS Keychain, Windows Credential Manager, GNOME Keyring, KDE Wallet.

### Priority 3: Environment variables via a settings loader

This is the minimum acceptable standard for any deployment.

```python
from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    api_token: SecretStr
    api_base_url: str = "https://api.example.com"
```

- A secret type prevents accidental logging — `str(settings.api_token)` returns
  `'**********'`. Call `.get_secret_value()` only at the I/O boundary.
- `.env` is **always** gitignored.

### .env.example (committed, placeholders only)

```bash
# Copy to .env and fill in real values. NEVER commit .env to git.
APP_API_TOKEN=your-token-here
APP_API_BASE_URL=https://api.example.com
```

---

## 5. Security Scanning CI Pipeline (GitHub Actions)

```yaml
name: Security & Legal

on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # full history for gitleaks

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install tools
        run: pip install bandit pip-audit pip-licenses liccheck

      - name: Bandit (Python SAST)
        run: bandit -r src/ -f json -o bandit-report.json || true

      - name: pip-audit (CVE check)
        run: pip-audit

      - name: License audit
        run: |
          pip-licenses --format=table --with-urls
          liccheck -s pyproject.toml

      - name: SPDX header check
        run: |
          MISSING=$(grep -L 'SPDX-License-Identifier' $(git ls-files 'src/*.py' 'tests/*.py'))
          if [ -n "$MISSING" ]; then
            echo "::error::Missing SPDX identifier in: $MISSING"
            exit 1
          fi

      - name: Gitleaks (secret scan)
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 6. .gitignore Security Baseline

```gitignore
# Secrets — NEVER commit
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx
credentials.json
secrets.yaml
token.txt
service-account*.json

# Cloud auth
.vault-token
.aws/credentials
```

---

## 7. Token Rotation & Expiry

| Token Type | Suggested Max Lifetime | Rotation Trigger |
|-----------|------------------------|------------------|
| Service API token | 90 days | Calendar reminder + CI warning |
| Cloud provider key | 90-180 days | Provider console policy |
| Personal access token | 30-90 days | Use fine-grained tokens with auto-expiry |

Rotate immediately on personnel change or suspected leak. Never embed expiry
logic that depends on a hard-coded date in source — drive it from configuration.

---

## 8. Secure Coding Checklist (Quick Reference)

```
Security & Legal Review:
- [ ] SPDX-License-Identifier present on ALL source files
- [ ] SPDX identifier matches the project LICENSE file
- [ ] No new GPL/AGPL/SSPL dependencies introduced
- [ ] THIRD_PARTY_NOTICES.md updated if dependencies changed
- [ ] No plaintext secrets in source code, comments, or docstrings
- [ ] No secrets in CLI --help output or example commands
- [ ] .env is gitignored; .env.example has placeholder values only
- [ ] All credentials loaded via a secret type or secret manager
- [ ] No secrets logged at any log level (verify with grep)
- [ ] bandit passes with zero high-severity findings
- [ ] pip-audit shows no known CVEs in dependencies
- [ ] gitleaks clean on full git history
```
