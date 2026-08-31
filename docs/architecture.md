# Internal Tools Platform POC — Design

## Hypothesis

> Given a standard application foundation, connector interface, and governed action framework, Devin can build a production-shaped internal tool with limited human intervention.

**Falsifiable success criterion:** after the platform and reference app (KYC review queue) exist, Devin builds a second tool (feature-flag admin panel) from a one-page spec using the `create-internal-tool` Skill, such that:

- all tests and lint pass,
- zero changes to `platform/` are required (if the spec needs a platform capability that doesn't exist, that's handled by the extension workflow below, in a separate PR — not by the app build),
- every mutation goes through the governed action pipeline (enforced by an import-boundary check, not convention),
- the UI is visibly the same family as the reference app,
- human intervention is limited to writing the spec and reviewing the PR.

This is a proof of concept: clear boundaries and working behavior are prioritized over completeness.

## Repo structure

```
README.md
docs/
├── architecture.md            # this document
├── tool-spec.template.md      # one-page spec an engineer fills in per tool
├── kyc-spec.md                # spec for the reference app
├── production-gaps.md         # honest list of what a real platform adds
└── evaluation.md              # results of the app-#2 experiment
.agents/
└── skills/
    └── create-internal-tool/
        └── SKILL.md           # Devin Skill: spec → working tool
platform/
├── backend/                   # installable package: pyproject.toml + platform_core/
│   ├── auth/                  # identity provider interface + mocked provider, roles
│   ├── actions/               # governed action pipeline
│   ├── audit/                 # append-only audit log (table + query API)
│   ├── connectors/            # typed connector contract + fake connector base
│   ├── db/                    # SQLite engine, session, migration helper
│   └── testing/               # pytest fixtures: users-by-role, fake connectors, audit assertions
└── frontend/                  # source library: package.json (lint/typecheck only), consumed
    │                          #   by app frontends via the @platform alias
    ├── components/            # shadcn-based kit: QueuePage, DetailPage, ActionBar,
    │                          #   StatusBadge, AuditTrail, RoleSwitcher
    ├── api/                   # typed client: fetch wrapper, action invocation, error shape
    └── theme/                 # tokens; single source of visual identity
apps/
└── kyc/
    ├── backend/               # own pyproject.toml + venv + server.py entrypoint
    │   └── kyc_app/
    │       ├── models.py      # domain model + states
    │       ├── policies.py    # role → action permissions, state-transition table
    │       ├── connector.py   # KYC system-of-record connector (fake impl for POC)
    │       ├── config.py      # ToolConfig wiring the tool into the platform
    │       └── tests/
    └── frontend/              # own package.json + Vite build; composes platform components
```

Domain-first layout: `platform/` and each `apps/<tool>/` contain their own `backend/` + `frontend/`, so a new tool is exactly one new folder (which is what the Skill scaffolds). Dependencies and setup are encapsulated per package: `platform/backend` is an installable Python package (`platform-core`), each app backend has its own `pyproject.toml`/venv depending on it, and each app frontend has its own `package.json`/Vite build consuming `platform/frontend` as source via the `@platform` alias. There is no repo-root toolchain. `db/` is part of the platform because persistence and migrations are where apps otherwise quietly diverge.

## Capability 1 — Governed access and actions

Every mutation in every app is a **governed action** executed through a single choke point:

```
run_action(action, actor, resource_id, input, idempotency_key)
  1. authenticate  → actor comes from the identity provider (mocked)
  2. authorize     → actor.role ∈ action.allowed_roles           else PermissionDenied
  3. validate      → resource.state ∈ action.valid_from_states   else InvalidTransition
                     input parses against action.input_schema     else ValidationError
  4. idempotency   → if key seen: return recorded outcome, do not re-execute
  5. execute       → action.handler(ctx) — may call connectors, never the DB of another system
  6. audit         → append record {actor, role, action, resource, input digest,
                     outcome (success | each error class), before_state, after_state, ts}
```

An action is declarative data plus a handler:

```python
approve = Action(
    name="kyc.approve",
    allowed_roles={Role.SUPERVISOR},
    valid_from_states={"in_review", "escalated"},
    to_state="approved",
    input_schema=ApproveInput,        # pydantic
    handler=approve_handler,
)
```

- **Identity:** `CurrentUserProvider` interface; the POC ships only a mocked provider with roles `viewer` / `operator` / `supervisor` (selected via header / UI RoleSwitcher). The interface is the enterprise-SSO integration point; no real SSO is implemented.
- **Audit:** append-only table; every outcome (including denials and validation failures) is recorded. The DetailPage renders the resource's audit trail.
- **Reads** go through a lighter path: authenticate → authorize (role-based, resource-level filter hook) → query. Reads are not audited in the POC (listed in production-gaps).

## Capability 2 — Data/tool integration layer

A typed connector contract is the only way app code touches a system of record:

```python
class Connector(Protocol[TResource]):
    def list(self, query: Query) -> ConnectorResult[Page[TResource]]: ...
    def get(self, resource_id: str) -> ConnectorResult[TResource]: ...
    def execute(self, command: Command, idempotency_key: str) -> ConnectorResult[CommandOutcome]: ...

ConnectorResult = Ok[T] | Err            # Err.kind ∈ {timeout, not_found, conflict,
                                          #   upstream_error, invalid_request}
```

- Consistent timeout and failure representation: every connector call returns `Ok | Err` with one of the fixed error kinds; no connector-specific exceptions leak upward.
- Commands carry idempotency keys end to end (action pipeline generates/records them).
- `platform/connectors` ships a `FakeConnector` base with scriptable data and failure injection (`fail_next(kind="timeout")`) — this is what tests and the POC runtime use.
- **Boundary rule:** `apps/**` may import `platform/*` and their own modules only; nothing in `apps/**` or `frontend/**` opens a DB connection or HTTP client directly. Enforced with import-linter (backend) and an ESLint boundary rule (frontend), wired into CI — so the constraint holds against an AI builder, not just a code reviewer.

Explicit non-goals: no connector marketplace, no generic retry framework (a single simple retry-once-on-timeout helper at most), no secrets manager (a `Secrets` interface reading env vars marks the integration point).

## Capability 3 — Repeatable delivery mechanism

- **`docs/tool-spec.template.md`** — one page: tool name, resource model + states, state-transition table, roles → actions matrix, connector data shape, queue columns/filters, detail-page fields. This is the entire human input for a new tool.
- **`.agents/skills/create-internal-tool/SKILL.md`** — the Devin Skill: reads a filled spec, then walks a fixed checklist: scaffold `apps/<tool>/backend/` and `apps/<tool>/frontend/` mirroring `apps/kyc/`, define models/policies/actions, implement the connector as a `FakeConnector`, compose pages exclusively from `platform/components`, write tests using `platform/testing` fixtures, run lint + boundary checks + tests. The Skill dictates the layout patterns (QueuePage → DetailPage → ActionBar), which is what makes every generated tool the same visual family without inventing a UI kit.
- **Platform extension workflow** — when a spec needs a capability or UI component the platform doesn't have, the Skill instructs Devin to **stop and escalate rather than improvise**: (1) never fork/inline a bespoke variant inside the app; (2) propose the missing capability as a separate platform PR (generalized, not tool-specific: added to `platform/`, themed, tested, documented in the Skill's component inventory), reviewed by a platform owner; (3) the app PR then builds on it. This keeps the "zero platform changes in an app PR" invariant while giving the platform a governed way to grow — mirroring how a real platform team would take contributions.
- **Testing conventions:** every app ships the same four test classes — permissions (role matrix), transitions (state table incl. invalid), idempotency (replay returns recorded outcome), audit (every outcome recorded). Platform fixtures make each a few lines.

## UI approach

No custom UI kit. shadcn/ui + Tailwind, wrapped once in `platform/frontend/components/` as a handful of opinionated composites (QueuePage, DetailPage, ActionBar, StatusBadge, AuditTrail, RoleSwitcher). Apps compose these; the theme lives in one place. Visual consistency across tools is a Skill-enforced property, which is exactly what the POC is demonstrating.

## Reference app: KYC review queue

Chosen because it exercises the platform hardest: multi-state lifecycle (`pending → in_review → approved | rejected | escalated`), role-differentiated actions (operator can review/escalate; only supervisor approves/rejects; viewer is read-only), and audit sensitivity.

## Evaluation (the actual experiment)

1. Platform + KYC app are built and reviewed by a human (with Devin, but not the artifact under test).
2. A human writes `feature-flags-spec.md` from the template (~1 page).
3. Devin, invoking the Skill, builds the feature-flag admin panel in a fresh session.
4. Record in `docs/evaluation.md`: number/nature of human interventions, whether platform code changed, test/lint/boundary results, side-by-side UI screenshots.

## Out of scope (tracked in production-gaps.md)

Real SSO/Entra, secrets management, read auditing, retry/backoff policy, deployment/hosting, migrations beyond SQLite, multi-tenancy, approval workflows for the tools themselves, observability.
