---
name: create-internal-tool
description: Build a new internal tool on the shared platform from a one-page tool specification. Use when asked to create, add, or implement a new internal tool/app in this repository from a spec in docs/.
---

# Create an internal tool from a spec

You are building a new tool on top of the shared platform in this repository.
The platform owns identity, authorization, state-transition validation,
idempotency, audit, connectors, HTTP routing, and the entire UI rendering.
A tool is **declarative configuration plus a connector** — nothing more.

## Hard rules

1. **Never modify anything under `platform/`.** If the spec requires a
   capability the platform lacks (a new field kind, a new page pattern, a new
   connector behavior), STOP. Do not inline a bespoke implementation in the
   app. Report the missing capability and propose a separate platform PR that
   adds it generally; the app PR must wait for it.
2. Never import `sqlite3`, `httpx`, `requests`, or any data source or HTTP
   client in app code. All data access goes through the tool's connector; all
   mutations go through governed `Action`s. `lint-imports` and ESLint enforce
   this — run them.
3. Do not add dependencies.
4. Follow the KYC reference app (`apps/kyc/`) exactly for structure and style.

## Inputs

A one-page spec at `docs/<tool-id>-spec.md` following
`docs/tool-spec.template.md`. If any section is missing or ambiguous, ask
before building.

## Steps

Use `<tool_id>` from the spec (e.g. `flags`).

1. **Backend** — create `apps/<tool_id>/backend/` mirroring `apps/kyc/backend/`:
   - `models.py`: a `str`-enum of lifecycle states, a Pydantic resource model,
     and one Pydantic input model per action (empty model if no input).
   - `policies.py`: `READ_ROLES` and `ACTIONS: list[Action]` — one `Action`
     per spec row with `name="<tool_id>.<action>"`, `command`, `allowed_roles`,
     `valid_from_states`, `to_state`, `input_schema`.
   - `connector.py`: a `FakeConnector` subclass with `resource_type`, seed
     data from the spec (cover every state), and `apply_command` mutating the
     record per command.
   - `config.py`: `TOOL = ToolConfig(tool_id=..., connector=..., actions=ACTIONS, read_roles=READ_ROLES)`
     with a `make_tool()` factory returning a fresh `ToolConfig` for tests.
   - `__init__.py` files for each package.
2. **Register the backend**: add the tool's `TOOL` to `apps/registry.py`.
3. **Tests** — create `apps/<tool_id>/backend/tests/` mirroring
   `apps/kyc/backend/tests/`: conftest wiring the tool into the shared
   fixtures from `platform_core.testing`, plus test classes covering the
   permission matrix, valid/invalid transitions, invalid input, unknown
   resource, idempotent replay, key reuse across actions, and audit records
   for success and every failure mode.
4. **Frontend** — create `apps/<tool_id>/frontend/index.ts` exporting a
   `ToolFrontendConfig` (see `apps/kyc/frontend/index.ts`): columns, detail
   fields, `statusKey`, a `statusVariants` badge mapping for every state, and
   an `ActionDef` per action (short name, label, destructive variant for
   destructive actions, `fields` for actions with input).
5. **Register the frontend**: add the config to `TOOLS` in `apps/registry.ts`.
6. **Verify** — all must pass:
   ```bash
   .venv/bin/pytest -q
   .venv/bin/ruff check .
   .venv/bin/lint-imports
   npx eslint .
   npm run build
   ```
7. **Confirm the boundary**: `git status` must show no changes under
   `platform/`, `src/`, or root config files (except the two registry files).
8. Open a PR containing only `apps/<tool_id>/` and the two registry edits.

## UI consistency

Do not write JSX, CSS, or new components for the tool. The queue page, detail
page, action bar, badges, and audit trail are rendered by the platform from
your `ToolFrontendConfig` — that is what keeps every tool in the same visual
family.
