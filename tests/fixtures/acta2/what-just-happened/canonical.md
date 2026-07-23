---
acta_protocol: "0.2"
artifact_kind: "incident-postmortem"
producer_skill: "what-just-happened"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "chat log 2026-07-21 — bug report thread"
  - "git log slice-4 deploy window"
  - "src/app.mjs — render glue at the incident revision"
  - "test/catalog.test.mjs — assertions added afterwards"
decisions:
  - id: "publish-postmortem"
    selection: "publish-record"
    rationale: "Timeline verified against the chat log; every claim is typed as fact, hypothesis, mitigation, or recovery."
    accepted_via: "chat 2026-07-23 — explicit confirmation"
supersedes: null
---

# INC-0721 — blank catalog on unknown-tag links

38 minutes of blank lists for shared ?tag= links after the slice-4 deploy.
Root cause: no branch between missing and unknown tags. Mitigated by a
temporary full-catalog fallback; durably fixed by the accepted empty state.
Contributing condition: the spec carried no unknown-tag criterion.
