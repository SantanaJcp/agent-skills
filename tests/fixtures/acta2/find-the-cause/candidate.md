---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "diagnosis"
producer_skill: "find-the-cause"
initiative: "tag-filter"
instrument: "checklist"
status: "candidate-ready"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
mark_h-popstate-missing: "falsified"
mark_h-bfcache: "validated"
mark_h-filter-order: "falsified"
mark_h-race: "falsified"
---

# Candidate — Find the cause — stale rows after back navigation

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: Why does back navigation intermittently show rows from the previous filter?
Working status: Candidate ready — copy the export and confirm in chat

## Item verdicts

- popstate never fires on back: Falsified
- bfcache restores the old DOM without any event: Validated
- filterByTag returns stale or reordered results: Falsified
- A render race lets the old list win: Falsified

## Conclusion

H2 is the cause: Safari bfcache restores the pre-navigation DOM with pageshow.persisted=true and no popstate, so renderFromUrl never re-runs. H1 falsified (handler fires everywhere else), H3 falsified (pure core property-tested stable), H4 falsified (synchronous render, nothing to race). Fix direction — pageshow listener vs bfcache opt-out — is deliberately out of scope here.

## Unresolved

- whether the eventual fix listens to pageshow or opts out of bfcache — a change-blueprint question, not a diagnosis one

## Provenance inputs

- qa notes 2026-07-23 — repro steps and frequency
- src/app.mjs — popstate wiring
- browser devtools traces from the repro session
