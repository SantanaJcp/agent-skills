---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "implementation-plan"
producer_skill: "change-blueprint"
initiative: "tag-filter"
instrument: "decision"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
selected_option: "approve-plan"
---

# Candidate — Change blueprint — implementation plan

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: Will this plan build the accepted specification safely?
Working status: Candidate ready — copy the export and confirm in chat

## Working selection

Selected: **Approve the plan** (`approve-plan`)
Rationale: Slices are independently green, the flow direction matches the accepted code-path decision, rollback is one revert.

## Alternatives on the table

- Approve the plan ← selected
- Request changes
- Reject the plan

## Unresolved

- whether slice 5 intercepts chip clicks or lets them navigate (decided during build)

## Provenance inputs

- spec.md — accepted at Gate A
- src/catalog.mjs — visibleSkills() idiom
- three-code-paths record — functional core, thin shell
