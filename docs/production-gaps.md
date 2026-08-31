# Production Gaps

This POC prioritizes clear boundaries and working behavior. The following are
deliberately mocked or omitted, and what production hardening would replace
them with.

| POC choice | Production replacement |
|---|---|
| Mocked identity via `X-Mock-Role` header | Real SSO (Entra ID / OIDC) with signed tokens; role claims from the IdP |
| Three fixed roles | Role/permission management, per-resource (row-level) rules where needed |
| SQLite file for audit + idempotency | Postgres (or similar) with migrations, backups, retention policy |
| Fake in-memory connectors | Real connectors to systems of record with timeouts, retries with backoff, circuit breaking |
| No secrets handling | Central secrets manager (Vault, cloud KMS) injected into connectors |
| Single process, no deploy story | Containerized deploy, CI/CD to staging/prod, health checks, availability monitoring |
| Audit of mutations only | Read auditing where compliance requires it; log shipping to SIEM |
| Import-linter + ESLint boundaries | Same, plus code review policy and CODEOWNERS on `platform/` |
| No rate limiting / quotas | Per-user and per-tool rate limits |
| Client-generated idempotency keys | Same pattern, plus key TTL/cleanup and server-side dedup windows |
| English-only, desktop-first UI | Localization, accessibility audit, responsive/mobile support if needed |

None of these gaps change the shape of app code: apps declare models,
policies, connectors, and UI config; the platform owns the hardening.
