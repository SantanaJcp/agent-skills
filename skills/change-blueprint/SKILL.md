---
name: change-blueprint
description: "Turn clarified requirements into a compact specification and a separate implementation plan with two human gates. Use when a change is ready for decision-complete planning; redirect broad ambiguity to discovery and do not implement the plan."
license: Apache-2.0
metadata:
  tags: "specification, planning, testing"
---

# Change Blueprint

## Purpose

Produce two separately approvable canonical artifacts: `spec.md` for product intent and `implementation-plan.md` for execution.

Read [the Acta v2 protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: write `scenario-spec.json` (Gate A) or `scenario-plan.json` (Gate B) and run [the bundled generator](references/acta2/generate-instrument.mjs); after both gates are accepted, write `canonical.json` and run [the record generator](references/acta2/generate-record.mjs). [instrument-spec.html](references/instrument-spec.html), [instrument-plan.html](references/instrument-plan.html), and [record.html](references/record.html) are rendered examples. The Acta 0.1 recipe ([acta-protocol.md](references/acta-protocol.md), [acta-scaffold.html](references/acta-scaffold.html)) remains bundled as the published compatibility fallback; Acta v2 is authoritative.

## Readiness

Inspect the conversation, repository, domain context, ADRs, tracker, chosen code path, and optional interface direction. Ask only blocking questions whose answers cannot be discovered. If ambiguity spans goals, actors, scope, or constraints, stop and recommend a realization pass instead of duplicating a full interview.

## Gate A — specification

1. Write `spec.md` with problem, outcomes, non-goals, actors, constraints, decisions, acceptance criteria, evidence, and highest available test seams. User stories are optional and must add clarity.
2. Record deferred decisions with owner and observable next action. Do not hide them in notes.
3. Author the spec as data (`scenario-spec.json`: scope, non-goals, acceptance criteria, assumptions, gate resolutions) and generate the Gate A instrument: `node <skill>/references/acta2/generate-instrument.mjs --scenario scenario-spec.json --out instrument-spec.html`. The gate stays open until the human explicitly approves or requests changes via the pasted candidate or chat.
4. Publish the approved spec only after a separate request and only through the project's documented tracker. Record the published revision for Gate B.

Gate A completes when `spec.md` is approved and every acceptance criterion has observable evidence.

## Gate B — implementation plan

1. Write `implementation-plan.md` against the approved spec revision. Include vertical slices, data flow, module/interface changes, riskiest code shape, migrations, failure behavior, security, rollout/rollback, and exact focused/full verification commands.
2. Prefer existing high seams. Introduce a seam only when the desired behavior cannot be observed correctly through an existing one.
3. Account for every acceptance criterion and every modified public behavior. Link risks to mitigations and tests.
4. Author the plan as data (`scenario-plan.json`: accepted-spec context, a `requiredPriorDecisions` entry identifying Gate A's approved selection plus the exact `spec.md` revision, slices, data-flow nodes/edges, riskiest code snippet, risks, tests, rollout/rollback, gate resolutions) and generate the Gate B instrument the same way (`--scenario scenario-plan.json --out instrument-plan.html`). After Gate B acceptance, preserve that same Gate A artifact path and revision in its canonical decision; `canonical.json` + `node <skill>/references/acta2/generate-record.mjs --canonical canonical.json --out record.html` emit the durable blueprint record. The generator rejects a missing, duplicated, unapproved, or revision-mismatched Gate A prerequisite.

Gate B completes when the plan is explicitly approved and an implementation agent needs no product or architecture decision.

## Handoff

Export both revisions plus `decisions.json`. Approval authorizes the contract, not publication, implementation, commit, or automatic invocation of another skill.
