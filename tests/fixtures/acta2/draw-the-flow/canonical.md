---
acta_protocol: "0.2"
artifact_kind: "process-flow"
producer_skill: "draw-the-flow"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "src/app.mjs — renderFromUrl and popstate wiring"
  - "src/catalog.mjs — filterByTag"
  - "src/url-tag.mjs — parseTagFromSearch"
  - "interface-directions record — accepted empty state"
decisions:
  - id: "flow-verification"
    selection: "confirm-accurate"
    rationale: "Walked each edge against the glue code; the branch and both exits match."
    accepted_via: "chat 2026-07-23 — explicit confirmation"
supersedes: null
---

# Tag-filter navigation flow — verified

navigation → parse → (tag known?) → filter → rows, with unknown tags
routing to the accepted empty state and clear-filter recovering to the
full catalog. Textual equivalent recorded alongside the drawing.
