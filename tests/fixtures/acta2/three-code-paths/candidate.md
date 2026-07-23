---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "code-path-decision"
producer_skill: "three-code-paths"
initiative: "tag-filter"
instrument: "decision"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
selected_option: "a"
---

# Candidate — Three code paths

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: Where should tag filtering and URL-state logic live, and which way should the DOM depend on it?
Working status: Candidate ready — copy the export and confirm in chat

## Working selection

Selected: **Functional core, thin shell** (`a`)
Rationale: Only shape with no tension against the Node-only test constraint; matches the existing pure-function idiom.

## Alternatives on the table

- Functional core, thin shell ← selected
- Encapsulated custom element
- Pub/sub URL-state store

## Unresolved

- control style, density, and empty-state copy belong to interface-directions

## Provenance inputs

- .agent-work/tag-filter/make-me-realize/realization.md
- src/catalog.mjs
- index.html
- test/catalog.test.mjs
