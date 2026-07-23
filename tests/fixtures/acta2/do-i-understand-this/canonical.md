---
acta_protocol: "0.2"
artifact_kind: "understanding-check"
producer_skill: "do-i-understand-this"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "src/catalog.mjs — filterByTag"
  - "src/url-tag.mjs — parseTagFromSearch"
  - "src/app.mjs — browser glue"
  - "build-with-notes session record — STOP-01 resolution"
decisions:
  - id: "understanding-check"
    selection: "record-gaps"
    rationale: "Score 5/6; the unknown-tag fallback gap is real — I expected a blank list."
    accepted_via: "chat 2026-07-23 — explicit confirmation of the pasted candidate"
supersedes: null
---

# Understanding check — tag-filter change

Score 5/6. Named gap: unknown-tag fallback (expected a blank list; the
accepted behavior is the explain-and-suggest empty state, src/app.mjs:19).
Follow-up: re-read the STOP-01 resolution and the interface-directions
record. This check is diagnostic and never gates a merge.
