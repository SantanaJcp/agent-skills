---
acta_protocol: "0.2"
artifact_kind: "figure-sheet"
producer_skill: "draw-it-in-svg"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "feature-xray record — verified system map"
  - "interface-directions record — accepted empty state"
  - "docs/architecture.md — module boundaries"
decisions:
  - id: "figure-sheet"
    selection: "accept-figures"
    rationale: "Data-flow and decision read at a glance; the seams arrow annotation needs less weight."
    accepted_via: "chat 2026-07-23 — explicit confirmation"
supersedes: null
---

# Tag-filter figure sheet

Approved: URL-to-DOM data flow; the one branch (unknown tags are a state,
not an error). Revision: module seams — dependency annotation reads heavier
than the layers it describes.
