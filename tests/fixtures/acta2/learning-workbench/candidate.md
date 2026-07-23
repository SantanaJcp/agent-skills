---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "learning-session"
producer_skill: "learning-workbench"
initiative: "url-as-state"
instrument: "quiz"
status: "candidate-ready"
source_revision: null
score_correct: 3
score_total: 4
gaps: 1
---

# Candidate — Learning workbench — URL as state

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: Workbench: URL-as-state, session 2
Working status: Candidate ready — copy the export and confirm in chat

## Self-check result

Score: 3 / 4. This check is diagnostic — never a merge gate.

## Answers

- ✓ Where does the filter state live between two visits? (chose: a)
- ✓ Why do the two core functions stay free of DOM access? (chose: b)
- ✗ A user presses back and the page shows the old list under the new URL. First suspect? (chose: b)
- ✓ You are adding a second filterable surface. What is the first design commitment? (chose: b)

## Gaps to close

- 03 · History traversal is not a load

## Unresolved

- session 3 candidate topic: applying the pattern to multi-parameter state

## Provenance inputs

- feature-xray record — tag filtering, verified
- find-the-cause record — bfcache diagnosis
- MDN — History API and pageshow
- spec.md — tag-filter scope
