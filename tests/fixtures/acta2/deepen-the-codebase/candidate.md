---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "architecture-analysis"
producer_skill: "deepen-the-codebase"
initiative: "tag-filter"
instrument: "decision"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
selected_option: "b"
---

# Candidate — Deepen the codebase — catalog module

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: Where should the catalog architecture deepen next?
Working status: Candidate ready — copy the export and confirm in chat

## Working selection

Selected: **Give the empty state a home** (`b`)
Rationale: The empty state is the one accepted design living as untested glue; naming it turns chip drift into a test failure.

## Alternatives on the table

- Split data from filtering
- Give the empty state a home ← selected
- Fold url-tag into catalog

## Unresolved

- direction A becomes attractive the moment a second catalog source appears

## Provenance inputs

- src/catalog.mjs — data + filtering in one module
- src/app.mjs — glue owning empty-state markup
- test/catalog.test.mjs — tests reaching across seams
- feature-xray record — verified system map
