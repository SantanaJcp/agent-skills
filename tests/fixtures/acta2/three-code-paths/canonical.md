---
acta_protocol: "0.2"
artifact_kind: "code-path-decision"
producer_skill: "three-code-paths"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - ".agent-work/tag-filter/make-me-realize/realization.md"
  - "src/catalog.mjs"
  - "index.html"
  - "test/catalog.test.mjs"
decisions:
  - id: "D-01"
    selection: "a"
    rationale: "Only shape with no tension against the Node-only test constraint; matches the existing pure-function idiom."
    accepted_via: "chat: \"accept path A\" after reviewing the candidate export"
supersedes: null
---

DecisionGate D-01 resolved: Path A — functional core, thin imperative shell. Paths B (custom element) and C (pub/sub store) preserved as rejected alternatives with change conditions. See the comparison matrix in the instrument evidence; interface control decisions remain with interface-directions.
