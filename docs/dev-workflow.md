# Developer workflow: from spec to tool

How a new internal tool goes from idea to production-shaped implementation.

```text
human opens a spec PR (docs/<tool-id>-spec.md)
    ↓
human reviews the requirements (intent review)
    ↓
reviewer comments: @devin build this tool from the spec
    ↓
Devin starts a fresh session, applies the create-internal-tool Skill
    ↓
Devin opens an implementation PR (apps/<tool-id>/ + registries only)
    ↓
CI (tests, lint, boundary checks) + human review (code review)
```

## 1. Spec PR

Copy `docs/tool-spec.template.md` to `docs/<tool-id>-spec.md` and fill it in.
The spec describes user intent — outcome, roles, data, journeys, views,
commands — not implementation. A spec PR should touch only the spec file.

Reviewing the spec PR is the **intent approval**: roles and permissions,
command preconditions and controls, and what is out of scope.

## 2. Triggering Devin

Prerequisite (one-time): install the Devin GitHub integration with access to
this repository (Devin webapp → Settings → Integrations → GitHub).

Once the spec PR is approved and merged, a reviewer comments on the PR:

> @devin build this tool from the spec in docs/&lt;tool-id&gt;-spec.md

Devin starts a fresh session with the PR as context. Repository Skills in
`.agents/skills/` are discovered automatically at session start, and the
`create-internal-tool` Skill's description ("build a new internal tool from a
one-page tool specification") matches this request, so Devin applies it
without being told. Naming the Skill explicitly in the comment
(`@devin use the create-internal-tool skill to build ...`) also works and
makes the match unambiguous.

## 3. Implementation PR

Devin opens a PR that should contain only `apps/<tool_id>/` plus the two
registry entries. It links back to the spec PR. Main CI enforces the
platform boundaries (import-linter, ESLint rules, tests, build).

Reviewing the implementation PR is the **code approval**: the reviewer
checks the acceptance scenarios are covered by tests and that any platform
change is one of the narrow allowed cases called out in the PR.

## Escalation path

If Devin reports a missing platform capability (authorization, governed
execution, auditing, or connector safety), that becomes a separate platform
PR reviewed by the platform owners; the tool PR waits for it. UI-only gaps
are built inside the app and flagged for future promotion into the kit.
