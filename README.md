# DevSecOps Pipeline

![DevSecOps pipeline](https://github.com/iamafrozmohd/devsecops-pipeline/actions/workflows/devsecops.yml/badge.svg)

A small Python API, its container, and its Azure infrastructure code, all guarded by a **GitHub Actions security pipeline**. Every push runs six checks in parallel, and a failed security gate stops the pipeline the same way a failed unit test would.

The goal is to show the "shift left" workflow end to end: catch vulnerable code, leaked secrets, vulnerable dependencies, insecure cloud configuration and missing web protections **before** anything is deployed.

## The pipeline

| Stage | Tool | What it checks | Gate |
|---|---|---|---|
| Unit tests | `unittest` | App behavior, input validation, security headers | Any failing test |
| SAST | [Semgrep](https://semgrep.dev) | Source code and Dockerfile against the Python, Flask, Dockerfile and secrets rulesets | Any finding |
| Secret scanning | [Gitleaks](https://github.com/gitleaks/gitleaks) | The **entire git history** for API keys, tokens and passwords | Any secret |
| SCA | [Trivy](https://trivy.dev) | Python dependencies for known CVEs | HIGH / CRITICAL with a fix available |
| Container scan | Trivy | The built image (Alpine OS packages + Python packages) | HIGH / CRITICAL with a fix available |
| IaC scan | Terraform `fmt` / `validate` + [Checkov](https://www.checkov.io) | Azure Terraform and the Dockerfile against CIS-style policies | Any failed policy |
| DAST | [OWASP ZAP](https://www.zaproxy.org) baseline | The **running** container, from the outside, like an attacker would see it | Report uploaded as a build artifact |

Semgrep results are also uploaded to the repository's **Security → Code scanning** tab as SARIF.

```
push / PR
   │
   ├── Unit tests ─────────────┐
   ├── SAST (Semgrep)          │
   ├── Secret scan (Gitleaks)  │
   ├── SCA + container (Trivy) ┼──► DAST (ZAP vs. the running container)
   └── IaC (Terraform+Checkov) │
```

## What's being protected

**`app/`: a small hash-lookup API (Flask + Gunicorn)**
- `POST /api/hash` returns the SHA-256 of submitted text
- `GET /api/lookup/<sha256>` checks a hash against a local known-bad list
- Written defensively: strict input validation, a 16 KB request limit, security headers on every response (CSP, `X-Frame-Options`, `nosniff`, `no-store`), no debug mode, no secrets in code

**`app/Dockerfile`: a hardened container**
- Small Alpine base on a pinned Python version, OS packages upgraded at build time
- Runs as an unprivileged `app` user with no shell
- Built-in `HEALTHCHECK`, no pip cache, nothing extra copied in (`.dockerignore`)

**`terraform/`: Azure storage for scan reports**
- TLS 1.2 minimum, HTTPS only, infrastructure (double) encryption
- **No public access and no shared keys**: anonymous blob access off, shared-key auth off, Entra ID auth by default, public network access disabled, firewall default-deny
- SAS tokens limited to 1 day, blob versioning and 14-day soft delete for ransomware/accidental-delete recovery
- Geo-redundant replication

## Risk acceptance, not silent skips
Three Checkov policies are skipped, each with a written justification in [`.checkov.yaml`](.checkov.yaml): customer-managed keys (Microsoft-managed keys plus double encryption are used instead), private endpoints (public access is fully disabled, and the endpoint would live in a networking module), and queue logging (the account has no queues). In a real team these would go through a risk-acceptance review rather than being quietly suppressed.

## Run it locally
```bash
# App + tests
pip install -r app/requirements.txt
python -m unittest discover -s tests -t . -v

# Container
docker build -t hashapi app
docker run --rm -p 8080:8080 hashapi
curl -s localhost:8080/api/lookup/275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f

# The same scanners the pipeline uses
pip install semgrep checkov
semgrep scan --config p/python --config p/flask
checkov --config-file .checkov.yaml -d terraform
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image hashapi
```

## Notes
- The Terraform is **scanned, never applied**: the pipeline doesn't need or hold any Azure credentials.
- Scanner images use their `latest` tags to keep this demo simple. In production you'd pin every action and image to a specific version or digest so the pipeline itself can't be tampered with through a compromised upstream.

---
*Author: Afroz Mohammed · [LinkedIn](https://www.linkedin.com/in/iamafrozmohd) · Built on what I practiced in a hands-on DevSecOps training course (CI/CD, SAST/SCA/DAST, Docker/Trivy, Terraform on Azure).*
