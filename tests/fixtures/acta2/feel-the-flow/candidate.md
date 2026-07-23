---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "interaction-prototype"
producer_skill: "feel-the-flow"
initiative: "tag-filter"
instrument: "prototype"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
param_debounce: 100
param_minChars: 0
toggle_instantFirst: true
---

# Candidate — Feel the flow — type-ahead filtering

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: How should catalog filtering feel while typing?
Working status: Candidate ready — copy the export and confirm in chat

## Felt parameters

- Debounce: 100 ms
- Minimum characters: 0
- Instant first keystroke (debounce only after): on

## Felt conclusion

300 ms reads as broken — the pending marker is the only sign anything heard you. 100 ms with instant first keystroke feels immediate on this five-item list; minimum characters adds nothing at this scale.

The prototype itself is disposable; only these parameters and this
conclusion carry forward.

## Unresolved

- whether type-ahead filtering enters scope at all — this prototype informs, it does not decide

## Provenance inputs

- src/catalog.mjs — the dataset the playground filters
- spec.md — current navigation-based filtering (the baseline being questioned)
