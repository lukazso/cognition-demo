# Tool Specification: <Tool Name>

One-page spec. Fill in every section; keep it under a page. Devin builds the
tool from this document using the `create-internal-tool` Skill.

## Overview

- **Tool ID**: `<url-safe id, e.g. flags>`
- **Purpose**: one or two sentences on what this tool is for and who uses it.

## Resource

The single resource type this tool manages.

- **Resource type**: `<e.g. feature_flag>`
- **Fields**: name, type, and short description for each field.

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier |
| ... | ... | ... |

## Lifecycle states

List the states and the allowed transitions.

```text
state_a → state_b (via action_x)
state_b → state_c (via action_y)
```

## Actions

One row per governed action.

| Action | From states | To state | Allowed roles | Input fields (name: type, required?) |
|---|---|---|---|---|
| `start_review` | `pending` | `in_review` | operator, supervisor | — |
| ... | ... | ... | ... | ... |

## Read access

Which roles may view the queue and detail pages (default: all roles).

## Queue page

Columns to show, in order. Mark the status column.

## Detail page

Fields to show on the detail card.

## Seed data

8–12 realistic demo records covering every lifecycle state.

## Out of scope

Anything explicitly not part of this tool.
