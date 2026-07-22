---
name: build-with-notes
description: "Implement an explicitly requested change test-first while maintaining live Acta notes, checks, deviations, and STOP gates. Use when the user asks to build from a spec, plan, ticket, or direct contract; do not activate for planning, diagnosis-only work, or read-only review."
license: Apache-2.0
metadata:
  tags: "implementation, tdd, review"
---

# Build With Notes

## Purpose

Implement the user's requested scope while keeping `implementation-notes.md` and `status.json` as an honest session record. An explicit implementation request authorizes edits in scope; commit still requires separate authorization.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Edit scaffold](references/acta-scaffold.html).

## Process

1. **Establish the contract.** Prefer an approved plan, then approved spec/ticket, then the current explicit request. If no blueprint exists, derive a minimal contract with scope, acceptance, constraints, and verification; ask only blocking ambiguities and record the provenance gap. Completion: each intended behavior has observable acceptance.
2. **Inspect before editing.** Read project instructions, domain context, ADRs, relevant modules, and prior tests. Preserve unrelated dirty work and identify the highest correct test seams. Completion: the first vertical slice and focused command are named.
3. **Run red → green by slice.** Write one behavior test at an agreed seam, run it red for the intended reason, implement only enough to pass, and run focused type/check commands. Do not bulk-write imagined tests or speculative abstractions. Completion: the slice is externally observable and green.
4. **Refresh live notes.** After every slice, deviation, failed/green check, and material discovery, append the event and regenerate `view.html`. Record current slice, tests, typecheck, changed files/modules, evidence, and next action. Do not require a watcher.
5. **Stop on contract changes.** Architecture, public API, data/schema, security, or scope changes open a visible STOP gate. Record the conflict and wait for an explicit decision before continuing. A new user instruction supersedes prior state only after it is recorded.
6. **Validate and review.** Run focused checks throughout, the full project acceptance seam once at the end, and an internal two-axis review: repository standards and approved contract. Fix verified findings and rerun affected checks.
7. **Distill decisions.** Prepare proposed updates for specs, ADRs, tickets, or docs. Publish them only after explicit approval. Remove temporary instrumentation and mark notes complete only when validation is green or an honest blocker is recorded.
8. **Commit gate.** Show the final scope, tests, review result, and proposed commit message. Create a commit only after explicit authorization. Never push or release unless separately requested.

## Guardrails

- Do not require another installed testing or review skill; use available capabilities as optional enhancements.
- Do not overwrite user changes, broaden scope to “clean things up,” or continue through a STOP gate.
- Keep notes append-only within the session and archive an approved prior revision before superseding it.
