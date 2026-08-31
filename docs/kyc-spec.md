# Tool Specification: KYC Review Queue

- **Tool ID**: `kyc`

## Outcome

- **Problem**: Customer KYC submissions must be reviewed, escalated when
  risky, and resolved with a full audit trail — today this is manual and
  untracked.
- **Users**: Compliance operators (review, escalate) and supervisors
  (approve/reject); anyone in the team may look up a case.
- **Success**: Every case reaches a terminal decision through a controlled
  path, and every decision (including denials and failures) is auditable.

## Roles and policies

| Role | May view | May execute | Constraints |
|---|---|---|---|
| viewer | all cases | — | read-only |
| operator | all cases | start_review, escalate | cannot make final decisions |
| supervisor | all cases | start_review, escalate, approve, reject | only role that can decide a case |

## Data and integrations

| System | Data or operations | Access method | Notes |
|---|---|---|---|
| KYC system of record | cases: read, review commands | connector | faked in the POC (`KycConnector`) |

## Domain model

One entity, **KYC case**:

| Field | Type | Description |
|---|---|---|
| `id` | string | Case identifier (`kyc-1001`) |
| `applicant_name` | string | Applicant full name |
| `email` | string | Applicant email |
| `country` | string | ISO country code |
| `risk_score` | int | 0–100 risk score from screening |
| `documents` | list[string] | Submitted document names |
| `state` | string | Lifecycle state |
| `submitted_at` | string | ISO timestamp of submission |
| `reviewer_id` | string? | Operator who started the review |
| `resolution_note` | string? | Escalation/approval/rejection note |

## User journeys

- An operator opens the queue, picks a pending case, starts the review, and
  either lets a supervisor decide or escalates it with a reason.
- A supervisor opens an in-review or escalated case and approves it (optional
  note) or rejects it (required reason).
- A viewer looks up a case to see its current state and full audit history.

## Views

| View | Purpose | Data displayed | Main interactions |
|---|---|---|---|
| Queue | triage all cases | id, applicant, country, risk, state badge, submitted | open a case |
| Case detail | review and act on one case | all fields, available actions, audit trail | execute commands, switch role (POC) |

## Commands

| Command | Allowed roles | Input | Preconditions | Effect | Controls |
|---|---|---|---|---|---|
| `start_review` | operator, supervisor | — | state `pending` | state → `in_review`, sets reviewer | idempotency, audit before/after |
| `escalate` | operator, supervisor | `reason` (required) | state `in_review` | state → `escalated`, note set | idempotency, audit before/after |
| `approve` | supervisor | `note` (optional) | state `in_review` or `escalated` | state → `approved`, note set | idempotency, audit before/after |
| `reject` | supervisor | `reason` (required) | state `in_review` or `escalated` | state → `rejected`, note set | idempotency, audit before/after |

## Workflow

```text
pending   → in_review (via start_review)
in_review → escalated (via escalate)
in_review → approved  (via approve)
in_review → rejected  (via reject)
escalated → approved  (via approve)
escalated → rejected  (via reject)
```

## Acceptance scenarios

- Given a pending case, when an operator starts review, then the state is
  `in_review` and an audit entry records actor, action, and pending→in_review.
- Given an in-review case, when a viewer attempts any command, then it is
  denied server-side and the denial is audited.
- Given an in-review case, when an operator escalates without a reason, then
  the request fails validation, the state is unchanged, and the failure is
  audited.
- Given a command is retried with the same idempotency key, then the recorded
  outcome is returned without re-executing.

## Seed data

12 cases spanning all five states with varied countries and risk scores.

## Out of scope

Document upload/inspection, sanctions-list integration, SLA timers.
