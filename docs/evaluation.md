# Evaluation

Hypothesis: *Given a standard application foundation, connector interface, and
governed action framework, Devin can build a production-shaped internal tool
with limited human intervention.*

## Procedure

1. Platform + KYC reference app are built and reviewed (this repo).
2. A human writes a one-page spec for a second tool (feature-flag admin panel)
   using `docs/tool-spec.template.md`.
3. In a fresh Devin session, Devin builds the tool using the
   `create-internal-tool` Skill, from the spec alone.
4. Record the results below.

## Pass criteria

- [ ] All backend tests pass (`pytest`)
- [ ] Lint passes (`ruff check .`, `npx eslint .`)
- [ ] Boundary checks pass (`lint-imports`, ESLint boundary rules)
- [ ] Frontend typechecks and builds (`npm run build`)
- [ ] **Zero changes under `platform/`** in the app PR
- [ ] The new tool's UI is in the same visual family (side-by-side screenshots)
- [ ] Human intervention limited to: writing the spec, reviewing the PR

## Results (to fill in after the experiment)

| Metric | Result |
|---|---|
| Human interventions (count + description) | |
| Platform files changed | |
| Tests / lint / boundaries | |
| Time to open PR | |
| Screenshots | |

## Escalation check

If the spec requires a capability the platform lacks, the Skill instructs
Devin to stop and propose a separate platform PR instead of inlining a
bespoke implementation. Note here whether that behavior was triggered and
followed.
