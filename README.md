# Internal Tools Platform POC

A proof of concept for building governed internal tools with Devin on a shared
platform, instead of a licensed low-code platform. See
`docs/architecture.md` for the design and `docs/evaluation.md` for the
experiment this repo exists to run.

**Hypothesis**: given a standard application foundation, connector interface,
and governed action framework, Devin can build a production-shaped internal
tool with limited human intervention.

## Layout

```text
platform/
├── backend/    # auth, actions, audit, connectors, db, http, testing (import name: platform_core)
└── frontend/   # shadcn-style UI kit, API client, QueuePage/DetailPage/ActionBar
apps/
└── kyc/        # reference app: backend (models/policies/connector/tests) + frontend config
docs/           # architecture, tool spec template, KYC spec, production gaps, evaluation
.agents/skills/create-internal-tool/   # the Devin Skill that builds new tools from a spec
```

Every mutation goes through one governed pipeline:
authenticate → authorize → idempotency → validate state → validate input →
execute via connector → audit. Identity is mocked (`X-Mock-Role` header:
`viewer` / `operator` / `supervisor`); no real SSO in this POC.

## Run it

```bash
# backend (Python 3.10+)
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn server:app --reload --port 8000

# frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to :8000
```

## Verify

```bash
.venv/bin/pytest -q          # backend tests
.venv/bin/ruff check .       # backend lint
.venv/bin/lint-imports       # backend import boundaries
npx eslint .                 # frontend lint + boundary rules
npm run build                # typecheck + build
```

## Adding a tool

Write a one-page spec from `docs/tool-spec.template.md`, then ask Devin to
build it — the `create-internal-tool` Skill does the rest. App PRs must not
touch `platform/`; missing platform capabilities are escalated as separate
platform PRs.
