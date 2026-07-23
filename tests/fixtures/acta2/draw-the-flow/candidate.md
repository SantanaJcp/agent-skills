---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "process-flow"
producer_skill: "draw-the-flow"
initiative: "tag-filter"
instrument: "decision"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
selected_option: "confirm-accurate"
---

# Candidate — Draw the flow — tag-filter navigation

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: How does a tag-filter navigation actually flow, end to end?
Working status: Candidate ready — copy the export and confirm in chat

## Working selection

Selected: **The flow is accurate** (`confirm-accurate`)
Rationale: Walked each edge against the glue code; the branch and both exits match.

## Alternatives on the table

- The flow is accurate ← selected
- Needs correction
- Wrong question

## Unresolved

- whether chip-click interception (slice 5 open question) changes the recovery path

## Provenance inputs

- src/app.mjs — renderFromUrl and popstate wiring
- src/catalog.mjs — filterByTag
- src/url-tag.mjs — parseTagFromSearch
- interface-directions record — accepted empty state
