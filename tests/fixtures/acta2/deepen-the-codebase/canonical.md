---
acta_protocol: "0.2"
artifact_kind: "architecture-analysis"
producer_skill: "deepen-the-codebase"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "src/catalog.mjs — data + filtering in one module"
  - "src/app.mjs — glue owning empty-state markup"
  - "test/catalog.test.mjs — tests reaching across seams"
  - "feature-xray record — verified system map"
decisions:
  - id: "deepening-direction"
    selection: "b"
    rationale: "The empty state is the one accepted design living as untested glue; naming it turns chip drift into a test failure."
    accepted_via: "chat 2026-07-23 — explicit confirmation"
supersedes: null
---

# Catalog deepening — accepted direction

Direction B: extract emptyState(tag) into empty-state.mjs with direct
tests asserting the chip set equals the real tag set. Blueprint seed
handed to change-blueprint. Directions A (data/behavior split) and C
(fold url-tag) preserved with change conditions.
