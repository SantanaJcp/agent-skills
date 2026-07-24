# ADR 0005 — Promote Acta v2 and the initial stable cohort

Date: 2026-07-23 · Status: accepted

## Context

All fifteen skills passed current Codex and Claude Code activation trials. The
full six-stage synthetic core cycle passed in both clients, including explicit
specification and plan gates, implementation notes, the remote-scope STOP gate,
and the post-change diagnostic. Deterministic repository checks passed on Linux
and Windows. Browser and assistive-technology matrices remained unexecuted.

## Decision

Promote all fifteen skills together from `incubator/` to `skills/`, promote
Acta v2 from `0.2.0-pilot` to `0.2.0`, and prepare the first public collection
release as `v1.0.0`.

For this initial promotion only, the owner explicitly defers the Chrome,
Safari, Firefox, VoiceOver, and NVDA evidence. The suite report records those
rows as deferred rather than passed. Future promotions continue to follow the
normal evidence policy unless another explicit decision changes it.

The rejected remote tag-suggestion API remains out of scope. Promotion adds no
network behavior or runtime dependency.

## Consequences

- Stable installation paths resolve from `skills/` and the generated stable
  catalog lists the complete suite.
- Acta v2 is authoritative; Acta 0.1 references remain bundled only as a
  compatibility fallback.
- The deferred browser and accessibility risk is visible and may be closed by
  later evidence without undoing this release.
