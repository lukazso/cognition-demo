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
├── backend/    # installable package `platform-core`: auth, actions, audit, connectors, db, http, testing
└── frontend/   # source library: shadcn-style UI kit, API client, QueuePage/DetailPage/ActionBar
apps/
├── kyc/        # reference app — fully self-contained:
│   ├── backend/   # own pyproject.toml + venv; `kyc_app` package + server.py entrypoint
│   └── frontend/  # own package.json + Vite build; consumes platform/frontend via @platform alias
└── flags/      # feature flag admin panel, built from docs/flags-spec.md
docs/           # architecture, tool spec template, tool specs, production gaps, evaluation
.agents/skills/create-internal-tool/   # the Devin Skill that builds new tools from a spec
```

Every mutation goes through one governed pipeline:
authenticate → authorize → idempotency → validate state → validate input →
execute via connector → audit. Identity is mocked (`X-Mock-Role` header:
`viewer` / `operator` / `supervisor`); no real SSO in this POC.

Dependencies and setup are encapsulated per package: each app owns its own
Python venv, npm install, and build; the only shared pieces are the two
`platform/` packages an app depends on. There is no repo-root toolchain.

## Run the KYC reference app

With [`just`](https://github.com/casey/just) installed, one command handles
all dependency setup and starts the app (Ctrl+C stops both processes):

```bash
cd apps/kyc
just dev        # backend on :8000 + frontend on :5173, cleaned up on exit
```

Or run the halves in separate terminals:

```bash
just backend    # creates the venv, installs deps, serves the API on :8000
just frontend   # npm install + Vite dev server on :5173 (proxies /api to :8000)
```

Or manually:

```bash
# backend (Python 3.10+), from apps/kyc/backend/
cd apps/kyc/backend
python3 -m venv .venv
.venv/bin/pip install -e ../../../platform/backend
.venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn server:app --reload --port 8000

# frontend, from apps/kyc/frontend/
cd apps/kyc/frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to :8000
```

Then open http://localhost:5173/kyc — the KYC reference app, seeded with 12
demo cases across all lifecycle states. Use the role switcher in the header
to act as `viewer` (read-only), `operator` (start review, escalate), or
`supervisor` (also approve/reject); each case's detail page shows the
available actions for the current role/state and the audit trail. The API is
also directly usable, e.g.:

```bash
curl -H "X-Mock-Role: supervisor" localhost:8000/api/kyc/resources
```

## Run the feature flag admin panel

Same shape as the KYC app (`cd apps/flags && just dev`), served at
http://localhost:5173/flags with 12 seeded flags across `draft`, `active`,
and `archived`.

## Verify

Each package verifies independently (CI runs one job per package):

```bash
# platform/backend
.venv/bin/ruff check . && .venv/bin/lint-imports

# platform/frontend
npm run lint && npm run typecheck

# apps/<tool>/backend
.venv/bin/ruff check . && .venv/bin/lint-imports && .venv/bin/pytest -q

# apps/<tool>/frontend
npx eslint . && npm run build
```

## Adding a tool

Write a one-page spec from `docs/tool-spec.template.md`, open a spec PR for
review, then comment `@devin build this tool from the spec` — the
`create-internal-tool` Skill does the rest. See `docs/dev-workflow.md` for
the full spec → review → Devin → implementation-PR flow. App PRs must not
touch `platform/`; missing platform capabilities are escalated as separate
platform PRs.
