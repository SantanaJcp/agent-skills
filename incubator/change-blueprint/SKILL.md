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

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Document scaffold](references/acta-scaffold.html).

## Readiness

Inspect the conversation, repository, domain context, ADRs, tracker, chosen code path, and optional interface direction. Ask only blocking questions whose answers cannot be discovered. If ambiguity spans goals, actors, scope, or constraints, stop and recommend a realization pass instead of duplicating a full interview.

## Gate A — specification

1. Write `spec.md` with problem, outcomes, non-goals, actors, constraints, decisions, acceptance criteria, evidence, and highest available test seams. User stories are optional and must add clarity.
2. Record deferred decisions with owner and observable next action. Do not hide them in notes.
3. Generate the Acta view with DecisionCards and Gate A. Remain `awaiting-decision` until the user explicitly approves or revises the spec.
4. Publish the approved spec only after a separate request and only through the project's documented tracker. Record the published revision for Gate B.

Gate A completes when `spec.md` is approved and every acceptance criterion has observable evidence.

## Gate B — implementation plan

1. Write `implementation-plan.md` against the approved spec revision. Include vertical slices, data flow, module/interface changes, riskiest code shape, migrations, failure behavior, security, rollout/rollback, and exact focused/full verification commands.
2. Prefer existing high seams. Introduce a seam only when the desired behavior cannot be observed correctly through an existing one.
3. Account for every acceptance criterion and every modified public behavior. Link risks to mitigations and tests.
4. Generate the updated Acta view with timeline, diagrams, code surface, risk table, and Gate B.

Gate B completes when the plan is explicitly approved and an implementation agent needs no product or architecture decision.

## Handoff

Export both revisions plus `decisions.json`. Approval authorizes the contract, not publication, implementation, commit, or automatic invocation of another skill.
