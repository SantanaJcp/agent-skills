---
acta_protocol: "0.2"
payload: "candidate"
artifact_kind: "concept-model"
producer_skill: "concept-lab"
initiative: "retry-backoff"
instrument: "model"
status: "candidate-ready"
source_revision: null
param_base: 200
param_factor: 2
param_retries: 6
param_cap: 2000
toggle_fullJitter: true
---

# Candidate — Concept lab

This payload is a candidate, not canonical state. Apply it only after
explicit acceptance in chat; silence is never approval.

Question: How do base delay, growth factor, retry count, cap, and jitter shape total retry wait?
Working status: Candidate ready — copy the export and confirm in chat

## Chosen parameters

- Base delay: 200ms
- Growth factor: 2×
- Max retries: 6
- Delay cap: 2000ms
- Full jitter (random 0…delay instead of delay/2…delay): on

## Derived consequence

Worst-case total wait across 6 attempts: 7000ms (expected ≈ 3500ms).

## Observed conclusion

Full jitter keeps the worst case at 7000 ms while the expected total drops to ≈3500 ms — half of the worst case, and one third below equal jitter's ≈5250 ms; the 2000 ms cap flattens growth from attempt 5 onward.

## Declared simplifications

- assumes an ideal clock and zero network transfer time
- treats jitter as a deterministic range band, not sampled randomness
- single client shown; aggregate-load effects are described, not simulated

## Unresolved

- mapping these parameters onto the project's actual HTTP client is a separate task

## Provenance inputs

- AWS Architecture Blog — Exponential Backoff and Jitter (Marc Brooker, 2015)
- Google SRE Book ch. 22 — Addressing Cascading Failures
