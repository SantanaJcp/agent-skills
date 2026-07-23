---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "understanding-check"
producer_skill: "do-i-understand-this"
initiative: "tag-filter"
instrument: "quiz"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
score_correct: 5
score_total: 6
gaps: 1
---

# Candidate — Do I understand this

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: Do you understand what the tag-filter change actually did?
Working status: Candidate ready — copy the export and confirm in chat

## Self-check result

Score: 5 / 6. This check is diagnostic — never a merge gate.

## Answers

- ✓ Where does filterByTag run? (chose: b)
- ✓ With JavaScript disabled, what does ?tag=git show? (chose: a)
- ✗ What renders for ?tag=deploy (a tag no skill has)? (chose: a)
- ✓ What state does the page persist between visits? (chose: b)
- ✓ Why does popstate reuse renderFromUrl instead of its own handler? (chose: a)
- ✓ What was rejected at STOP-01 during the build? (chose: b)

## Gaps to close

- unknown-tag fallback

## Unresolved

- nothing recorded

## Provenance inputs

- src/catalog.mjs — filterByTag
- src/url-tag.mjs — parseTagFromSearch
- src/app.mjs — browser glue
- build-with-notes session record — STOP-01 resolution
