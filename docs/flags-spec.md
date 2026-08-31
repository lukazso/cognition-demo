# Tool Specification: Feature Flag Admin Panel

- **Tool ID**: `flags`

## Outcome

- **Problem**: Feature flags are toggled ad hoc via config edits and direct
  database changes — there is no controlled path, no approval for
  production-impacting changes, and no record of who changed what and why.
- **Users**: Engineers (operators) manage flags day to day; supervisors
  control production-impacting and destructive changes; anyone in the team
  may look up a flag's current state and history.
- **Success**: Every flag change goes through a governed, audited path;
  production enablement requires elevated permission; retired flags cannot be
  silently resurrected.

## Roles and policies

| Role | May view | May execute | Constraints |
|---|---|---|---|
| viewer | all flags | — | read-only |
| operator | all flags | create, enable/disable in non-prod, update rollout in non-prod | cannot touch production or archive |
| supervisor | all flags | everything operators can, plus enable/disable in production, update production rollout, archive | only role that can change production or archive a flag |

## Data and integrations

| System | Data or operations | Access method | Notes |
|---|---|---|---|
| Flag configuration store | flags: read, change commands | connector | faked in the POC (fake connector with seed data and failure injection) |

## Domain model

One entity, **Feature flag**:

| Field | Type | Description |
|---|---|---|
| `id` | string | Flag identifier (`flag-1001`) |
| `key` | string | Unique flag key (`checkout.new-payment-flow`) |
| `description` | string | What the flag controls |
| `owner_team` | string | Owning team (`payments`, `growth`, ...) |
| `state` | string | Lifecycle state (`draft`, `active`, `archived`) |
| `staging_enabled` | bool | Enabled in staging |
| `prod_enabled` | bool | Enabled in production |
| `prod_rollout_pct` | int | Production rollout percentage 0–100 |
| `created_at` | string | ISO timestamp of creation |
| `updated_by` | string? | Actor of the last change |
| `change_note` | string? | Reason recorded with the last change |

## User journeys

- An engineer creates a flag for a new feature, enables it in staging, and
  verifies behavior; production stays off.
- A supervisor enables the flag in production at 10%, later raises the
  rollout to 100% with a reason, each step audited.
- After full rollout and code cleanup, a supervisor archives the flag with a
  note; it becomes read-only.
- A viewer looks up a flag to see its current environments, rollout, and full
  change history.

## Views

| View | Purpose | Data displayed | Main interactions |
|---|---|---|---|
| Flag list | overview of all flags | key, owner team, state badge, staging/prod enabled, prod rollout | open a flag |
| Flag detail | inspect and change one flag | all fields, available actions, audit trail | execute commands, switch role (POC) |

## Commands

| Command | Allowed roles | Input | Preconditions | Effect | Controls |
|---|---|---|---|---|---|
| `create` | operator, supervisor | `key` (required), `description` (required), `owner_team` (required) | key not already used | new flag in state `draft`, everything off | idempotency, audit |
| `activate` | operator, supervisor | — | state `draft` | state → `active` | idempotency, audit before/after |
| `set_staging` | operator, supervisor | `enabled` (required bool) | state `active` | `staging_enabled` updated | idempotency, audit before/after |
| `set_production` | supervisor | `enabled` (required bool), `reason` (required) | state `active` | `prod_enabled` updated | idempotency, audit before/after |
| `set_rollout` | supervisor | `percentage` (required int 0–100), `reason` (required) | state `active`, `prod_enabled` true | `prod_rollout_pct` updated | idempotency, audit before/after |
| `archive` | supervisor | `note` (required) | state `active`, `prod_enabled` false | state → `archived`, read-only | idempotency, audit before/after |

## Workflow

```text
draft  → active   (via activate)
active → archived (via archive; only when production is off)
```

Environment toggles and rollout changes happen within the `active` state.

## Acceptance scenarios

- Given a draft flag, when an operator activates it, then the state is
  `active` and an audit entry records actor, action, and draft→active.
- Given an active flag, when an operator attempts `set_production`, then it
  is denied server-side and the denial is audited.
- Given an active flag with production enabled, when a supervisor attempts
  `archive`, then the precondition fails, the flag is unchanged, and the
  failure is audited.
- Given `set_rollout` with a percentage outside 0–100 or without a reason,
  then the request fails validation, the flag is unchanged, and the failure
  is audited.
- Given a command is retried with the same idempotency key, then the recorded
  outcome is returned without re-executing.

## Seed data

10–12 flags spanning all three states, several owner teams, and interesting
variations: staging-only flags, production flags at partial rollout (e.g.
10%, 50%), a fully rolled-out flag, and archived flags.

## Out of scope

Per-user/segment targeting rules, SDK/client delivery of flag values,
scheduled rollouts, multi-environment matrices beyond staging/production,
flag analytics.
