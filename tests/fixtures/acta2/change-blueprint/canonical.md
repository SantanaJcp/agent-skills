---
acta_protocol: "0.2"
artifact_kind: "implementation-plan"
producer_skill: "change-blueprint"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "spec.md — accepted at Gate A"
  - "src/catalog.mjs — visibleSkills() idiom"
  - "three-code-paths record — functional core, thin shell"
decisions:
  - id: "gate-b-plan"
    selection: "approve-plan"
    rationale: "Slices are independently green, the flow direction matches the accepted code-path decision, rollback is one revert."
    accepted_via: "chat 2026-07-23 — explicit confirmation of the pasted candidate"
  - id: "gate-a-spec"
    selection: "approve-spec"
    rationale: "Scope and non-goals mirror the interview frontier; all six criteria are mechanically checkable."
    accepted_via: "chat 2026-07-22 — explicit confirmation of the pasted candidate"
supersedes: null
---

# Tag-filter change blueprint — accepted

Gate A locked scope (single ?tag= filter, pure core, no-JS parity) and
non-goals (no search, no network, no persistence). Gate B accepted the
five-slice plan: pure filterByTag, pure parseTagFromSearch, static chips,
browser glue, back/forward wiring — DOM depends on pure functions, never
the reverse. Rollback is a single revert of the slice-4 commit.
