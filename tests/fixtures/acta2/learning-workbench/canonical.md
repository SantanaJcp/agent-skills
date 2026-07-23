---
acta_protocol: "0.2"
artifact_kind: "learning-session"
producer_skill: "learning-workbench"
initiative: "url-as-state"
status: "approved"
phase: "accepted"
language: "en"
source_revision: null
inputs:
  - "feature-xray record — tag filtering, verified"
  - "find-the-cause record — bfcache diagnosis"
  - "MDN — History API and pageshow"
  - "spec.md — tag-filter scope"
decisions:
  - id: "session-close"
    selection: "record-session"
    rationale: "The miss was q3 — I still reach for a render race before remembering restore semantics."
    accepted_via: "chat 2026-07-23 — explicit confirmation"
supersedes: null
---

# URL-as-state — session 2

Score 3/4. Review next session: waypoint 03 (history traversal is not a
load — bfcache restores fire pageshow, not popstate). Sessions remain
diagnostic learning state; nothing here gates anything.
