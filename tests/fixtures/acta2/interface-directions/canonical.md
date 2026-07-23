---
acta_protocol: "0.2"
artifact_kind: "interface-direction-decision"
producer_skill: "interface-directions"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "index.html — current catalog markup"
  - "spec.md — tag-filter scope and non-goals"
  - "STOP-01 resolution — unknown tags stay empty, no remote suggestions"
decisions:
  - id: "empty-state-direction"
    selection: "b"
    rationale: "B is the only direction that gives the user somewhere to go; chips derive from visibleSkills() so they cannot drift from the real tag set."
    accepted_via: "chat 2026-07-23 — explicit confirmation of the pasted candidate"
supersedes: null
---

# Empty tag-filter result — accepted direction

Direction B (Explain and suggest) is accepted for the empty tag-filter state.
The empty state names the missing tag, states the catalog's real tag set as
chips that are live filters, and offers a clear-filter exit. Directions A
(Quiet text) and C (Catalog stays visible) are preserved with their change
conditions in the decision record.
