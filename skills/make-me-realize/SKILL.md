---
name: make-me-realize
description: "Reveal blind spots in a vague plan or change request by researching facts and interviewing the full decision frontier. Use when requirements, constraints, ownership, or unknowns must be clarified before solution design; do not use to synthesize an already-settled specification."
license: Apache-2.0
metadata:
  tags: "discovery, planning, requirements"
---

# Make Me Realize

## Purpose

Turn a vague idea into an owned map of facts, constraints, decisions, and unknowns. This is discovery, not solution design or specification writing. It deliberately produces no HTML.

Read [the Acta artifact protocol](references/acta-protocol.md) before creating the record.

## Process

1. **Establish the initiative.** Infer and confirm the stable initiative slug, create this skill's workspace, and start `realization.md` with Acta frontmatter. Completion: the request and scope are faithfully restated.
2. **Separate facts from decisions.** Inspect the repository, project instructions, domain context, ADRs, issue tracker, and trusted external sources when needed. Never ask the user for a discoverable fact. Completion: every current statement is classified as fact, constraint, user decision, or unknown.
3. **Run the blind-spot pass.** Search across user value, scope, actors, data, interfaces, architecture, operations, security, failure, migration, rollout, testing, ownership, and reversibility. Record why each unknown matters. Completion: every material blind spot is visible in the record.
4. **Build the decision tree.** A decision may enter the frontier only after its prerequisites are settled. Group every currently answerable frontier question into one round, number the questions, and include a recommended choice with its trade-off. Wait for the answers before recomputing the frontier. Completion: no question depends on another still open in the same round.
5. **Own every remaining unknown.** Research new facts, record user decisions, or assign unresolved work to a named owner and observable next action. Do not treat “later” as ownership. Completion: the frontier is empty and every unknown is answered or explicitly owned.
6. **Close the realization.** Summarize constraints, decisions, open owned work, non-goals, and readiness for approach exploration. Mark the artifact `completed`; recommend a next skill without invoking it.

## Guardrails

- Do not propose three solutions, write the final spec, implement, or publish during realization.
- Reopen the frontier when a user answer introduces a new dependency.
- Prefer positive target behavior over long lists of prohibitions.
- The completion criterion is exhaustive ownership, not the number of questions asked.
