# Tool Specification: <Tool Name>

One-page spec describing user intent, not implementation. Devin builds the
tool from this document using the `create-internal-tool` Skill. Sections
marked *optional* may be omitted when they don't apply.

- **Tool ID**: `<url-safe id, e.g. flags>`

## Outcome

- What problem does this tool solve?
- Who uses it?
- What does success look like?

## Roles and policies

| Role | May view | May execute | Constraints |
|---|---|---|---|
| viewer | ... | — | ... |
| operator | ... | ... | ... |
| supervisor | ... | ... | e.g. only supervisors may perform destructive commands |

## Data and integrations

| System | Data or operations | Access method | Notes |
|---|---|---|---|
| `<system of record>` | ... | connector | ... |

## Domain model

Describe the important entities and their relationships. There may be more
than one entity. For each: name, key fields (name, type, description), and
how it relates to the others.

## User journeys

Short narratives of how each role uses the tool, e.g. "An operator opens the
queue, filters to pending cases, reviews one, and escalates it with a reason."

## Views

| View | Purpose | Data displayed | Main interactions |
|---|---|---|---|
| ... | ... | ... | ... |

## Commands

| Command | Allowed roles | Input | Preconditions | Effect | Controls |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

Controls may include: confirmation, approval, separation of duties,
idempotency, audit before/after values.

## Workflow *(optional)*

Include states and transitions only if the domain has a meaningful lifecycle.

```text
state_a → state_b (via command_x)
```

## Acceptance scenarios

Concrete given/when/then scenarios that define "done", covering the happy
path, a permission denial, and a validation failure at minimum.

## Seed data

Realistic demo records covering the interesting variations (states, roles,
edge cases).

## Out of scope

Anything explicitly not part of this tool.
