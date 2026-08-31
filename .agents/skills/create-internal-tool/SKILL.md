---
name: create-internal-tool
description: Build a new internal tool on the shared platform from a one-page tool specification. Use when asked to create, add, or implement a new internal tool/app in this repository from a spec in docs/.
---

# Create an internal tool from a spec

You are building a new tool on top of the shared platform in this repository.
The platform owns identity, authorization, governed execution, idempotency,
audit, connectors, HTTP plumbing, and a shared UI kit. A tool provides its
domain: entities, policies, connectors, commands, and views.

The existing tools under `apps/` are **worked examples**, not structures that
must be copied exactly. Inspect them for established patterns, style, and how
they use platform capabilities — but do not treat any of them as prescriptive.
For instance, `apps/kyc/` happens to be a single-entity queue tool with a
lifecycle; your tool may have multiple related entities, commands that are not
state transitions, and views that are not queues.

## Mandatory boundaries (never relax these)

1. External data access goes through connectors — never import `sqlite3`,
   `httpx`, `requests`, or any data source or HTTP client in app code.
   `lint-imports` and ESLint enforce this; run them.
2. Sensitive writes go through governed execution (`run_action` via the
   platform's action layer) — never mutate a system of record outside it.
3. Authorization is enforced server-side, never only in the UI.
4. Audit records exist for successful, denied, and failed actions.
5. Behavioral tests cover the permission matrix, validation failures, and
   audit outcomes.
6. Declare all dependencies inside the app's own manifests
   (`apps/<tool_id>/backend/pyproject.toml`, `apps/<tool_id>/frontend/package.json`)
   — there is no repo-root toolchain to add them to. Keep them minimal; the
   platform packages already provide the common runtime.

## What is flexible

- **Lifecycle states and transitions are optional.** Use them only if the
  domain has a meaningful lifecycle (the spec's Workflow section). Commands
  without a state transition (e.g. updating a flag's rollout percentage) are
  fine — model them as governed actions whose effect is a field change.
- **Multiple related entities are allowed.** Give each entity a connector
  resource type, or model child data as fields of the parent — whichever the
  domain calls for.
- **App-specific pages and components are allowed.** Use platform components
  where they fit — they keep tools in the same visual family — but when a
  spec needs a view the kit doesn't cover, build it inside
  `apps/<tool_id>/frontend/` using the platform's UI primitives, theme
  tokens, and API client rather than blocking the tool.

## When to stop and escalate vs. build in-app

- If a missing capability affects **authorization, governed execution,
  auditing, or connector safety**: STOP. Do not inline a bespoke workaround
  in the app. Report the gap and propose a separate platform PR that adds the
  capability generally; the app PR waits for it.
- If only a **UI pattern** is missing: implement it inside the application
  (composing platform primitives), and note it in the PR as a candidate for
  future promotion into the platform kit.
- If an existing platform contract **unnecessarily requires a status or state
  transition** for your tool, loosen it minimally (e.g. make the field
  optional with a default) in a small, clearly-explained platform change —
  do not fork or bypass the contract.

## Inputs

A one-page spec at `docs/<tool-id>-spec.md` following
`docs/tool-spec.template.md` (outcome, roles/policies, data & integrations,
domain model, user journeys, views, commands, optional workflow, acceptance
scenarios). If any section is missing or ambiguous, ask before building.

## Steps

Use `<tool_id>` from the spec (e.g. `flags`).

Each app is fully self-contained: its backend has its own `pyproject.toml`,
venv, and `server.py` entrypoint; its frontend has its own `package.json` and
Vite build. Start by copying the manifests and configs from an existing app
(e.g. `apps/kyc/`) and renaming.

1. **Backend** — create `apps/<tool_id>/backend/` with `pyproject.toml`
   (package `<tool_id>-app`, depending on `platform-core`), `server.py`
   (`create_app([TOOL])`), and the package `<tool_id>_app/`:
   - `models.py`: Pydantic models for each entity, plus one input model per
     command (empty model if no input). Add a state enum only if the spec has
     a Workflow section.
   - `policies.py`: `READ_ROLES` and `ACTIONS: list[Action]` — one `Action`
     per command row with `name="<tool_id>.<command>"`, `allowed_roles`,
     `valid_from_states`/`to_state` when there is a lifecycle, and
     `input_schema`.
   - `connector.py`: a `FakeConnector` subclass per resource type with seed
     data from the spec and `apply_command` implementing each command's
     effect. A command that creates a resource is an `Action` with
     `creates_resource=True` (no `valid_from_states`), invoked at
     `POST /api/<tool_id>/resources/actions/<command>`, and the connector
     implements `build_record` — assigning the id and rejecting duplicates
     with `Err` — instead of `apply_command`.
   - `config.py`: a `make_tool()` factory returning a fresh `ToolConfig`,
     and `TOOL = make_tool()`.
2. **Set up the venv**:
   ```bash
   cd apps/<tool_id>/backend
   python3 -m venv .venv
   .venv/bin/pip install -e ../../../platform/backend
   .venv/bin/pip install -e ".[dev]"
   ```
3. **Tests** — `apps/<tool_id>/backend/<tool_id>_app/tests/` using the shared
   fixtures from `platform_core.testing`: cover the acceptance scenarios, the
   permission matrix, invalid input, unknown resource, idempotent replay, and
   audit records for success and every failure mode (plus transition tests if
   the tool has a lifecycle).
4. **Frontend** — create `apps/<tool_id>/frontend/` with its own
   `package.json`, Vite/TypeScript/Tailwind/ESLint configs (copy from an
   existing app; keep the `@platform` alias pointing at
   `../../../platform/frontend`), and `src/`: prefer a declarative
   `ToolFrontendConfig` (see `apps/kyc/frontend/src/tool.ts`) mounted via
   `AppShell` in `src/main.tsx` when the spec's views map to the platform's
   queue/detail patterns; add app-specific pages or components when they
   don't, built from platform UI primitives and the platform API client.
5. **Extend CI**: add `<tool_id>-backend` and `<tool_id>-frontend` jobs to
   `.github/workflows/ci.yml`, mirroring the existing per-app jobs.
6. **Verify** — all must pass, run inside the app's own directories:
   ```bash
   # apps/<tool_id>/backend
   .venv/bin/pytest -q
   .venv/bin/ruff check .
   .venv/bin/lint-imports
   # apps/<tool_id>/frontend
   npm install
   npx eslint .
   npm run build
   ```
7. **Confirm the boundary**: `git status` should show changes only under
   `apps/<tool_id>/` plus the CI jobs. Any platform change must be one of the
   narrow cases above and called out explicitly in the PR.
8. Open a PR.

## UI consistency

Whether declarative or app-specific, all UI must use the platform kit's
components, theme tokens, and API client — no new design systems, raw fetch
calls, or one-off styling. That is what keeps every tool in the same visual
family.
