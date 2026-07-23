---
acta_protocol: "0.2"
artifact_kind: "diagnosis"
producer_skill: "find-the-cause"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "qa notes 2026-07-23 — repro steps and frequency"
  - "src/app.mjs — popstate wiring"
  - "browser devtools traces from the repro session"
decisions:
  - id: "diagnosis"
    selection: "record-diagnosis"
    rationale: "H2 correlates perfectly across twenty traversals; the other three died to direct probes, not intuition."
    accepted_via: "chat 2026-07-23 — explicit confirmation"
supersedes: null
---

# Diagnosis — stale rows after back navigation

Validated: bfcache restore without popstate (exact correlation with
pageshow.persisted across twenty traversals). Falsified: missing popstate
wiring, filter instability, render race — each by a direct probe. The fix
is a separate decision; this record is the diagnosis only.
