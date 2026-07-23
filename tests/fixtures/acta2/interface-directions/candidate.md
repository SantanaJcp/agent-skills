---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "interface-direction-decision"
producer_skill: "interface-directions"
initiative: "tag-filter"
instrument: "decision"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
selected_option: "b"
---

# Candidate — Interface directions

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: Which visual direction should the empty tag-filter result take?
Working status: Candidate ready — copy the export and confirm in chat

## Working selection

Selected: **Explain and suggest** (`b`)
Rationale: B is the only direction that gives the user somewhere to go; chips derive from visibleSkills() so they cannot drift from the real tag set.

## Alternatives on the table

- Quiet text
- Explain and suggest ← selected
- Catalog stays visible

## Unresolved

- chip ordering (alphabetical vs frequency) once real usage exists
- whether the clear-filter action reads better as a link than a button

## Provenance inputs

- index.html — current catalog markup
- spec.md — tag-filter scope and non-goals
- STOP-01 resolution — unknown tags stay empty, no remote suggestions
