---
acta_protocol: "0.2"
artifact_kind: "concept-model"
producer_skill: "concept-lab"
initiative: "retry-backoff"
status: "completed"
phase: "accepted"
language: "en"
source_revision: null
inputs:
  - "AWS Architecture Blog — Exponential Backoff and Jitter (Marc Brooker, 2015)"
  - "Google SRE Book ch. 22 — Addressing Cascading Failures"
decisions:
  - id: "D-01"
    selection: "model-accepted"
    rationale: "The bench made the jitter trade-off legible: full jitter leaves the worst case untouched while cutting the expected total to half the worst case (one third below equal jitter), and the cap is what bounds the tail."
    accepted_via: "chat: \"accept the backoff model\" after reviewing the candidate export"
supersedes: null
---

The team explored exponential backoff with jitter as a shared mental model before touching the HTTP client. At the accepted parameters (base 200 ms, factor 2, 6 retries, 2000 ms cap, full jitter on) the worst-case aggregate wait is 7000 ms; the expected wait is ≈3500 ms — half of the worst case and one third below equal jitter's ≈5250 ms — with the cap binding from attempt 5. The model is a teaching device, not a client configuration: mapping these parameters onto the project's actual retry code is tracked separately.

## Accepted model state

- param base: 200
- param factor: 2
- param retries: 6
- param cap: 2000
- toggle fullJitter: true
- conclusion: Full jitter keeps the worst case at 7000 ms while the expected total drops to ≈3500 ms — half of the worst case, and one third below equal jitter's ≈5250 ms; the 2000 ms cap flattens growth from attempt 5 onward.
