# Tool Specification: KYC Review Queue

## Overview

- **Tool ID**: `kyc`
- **Purpose**: Compliance operators review customer KYC submissions, escalate
  risky cases, and supervisors approve or reject them.

## Resource

- **Resource type**: `kyc_case`

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

## Lifecycle states

```text
pending   → in_review (via start_review)
in_review → escalated (via escalate)
in_review → approved  (via approve)
in_review → rejected  (via reject)
escalated → approved  (via approve)
escalated → rejected  (via reject)
```

## Actions

| Action | From states | To state | Allowed roles | Input fields |
|---|---|---|---|---|
| `start_review` | `pending` | `in_review` | operator, supervisor | — |
| `escalate` | `in_review` | `escalated` | operator, supervisor | `reason`: string, required |
| `approve` | `in_review`, `escalated` | `approved` | supervisor | `note`: string, optional |
| `reject` | `in_review`, `escalated` | `rejected` | supervisor | `reason`: string, required |

## Read access

All roles (viewer, operator, supervisor).

## Queue page

Columns: Case (id, link to detail), Applicant, Country, Risk, State (status), Submitted.

## Detail page

Fields: Applicant, Email, Country, Risk score, Submitted, Reviewer, Resolution note.

## Seed data

12 cases spanning all five states with varied countries and risk scores.

## Out of scope

Document upload/inspection, sanctions-list integration, SLA timers.
