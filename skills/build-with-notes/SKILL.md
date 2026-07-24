---
name: build-with-notes
description: "Implement an explicitly requested code change test-first while maintaining live Acta notes, checks, deviations, and STOP gates. Use for direct mutation requests such as implement, build, fix, refactor this module now, or execute an approved spec, plan, ticket, or contract; do not activate for planning, diagnosis-only work, or read-only review."
license: Apache-2.0
metadata:
  tags: "implementation, tdd, review"
---

# Build With Notes

## Purpose

Implement the user's requested scope while keeping `implementation-notes.md` and `status.json` as an honest session record, and a session-board instrument as the human's monitoring and intervention surface. An explicit implementation request authorizes edits in scope; commit still requires separate authorization.

Read [the Acta v2 protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: maintain `scenario.json` and regenerate the board with [the bundled generator](references/acta2/generate-instrument.mjs); after the session closes, write `canonical.json` and run [the record generator](references/acta2/generate-record.mjs). [instrument.html](references/instrument.html) and [record.html](references/record.html) are rendered examples of the outputs.

HTML earns its place here as a **board, not a log**: the human monitoring a build needs "what is happening now, may work continue, what needs me" answered in one glance, and an open STOP gate needs response controls. When a session is short, linear, and gate-free, the Markdown notes alone are enough — skip the board rather than maintain an empty one.

## Process

1. **Establish the contract.** Prefer an approved plan, then approved spec/ticket, then the current explicit request. If no blueprint exists, derive a minimal contract with scope, acceptance, constraints, and verification; ask only blocking ambiguities and record the provenance gap. Completion: each intended behavior has observable acceptance.
2. **Write the instrument brief** into `implementation-notes.md`: human question (where does the build stand and what needs me?); cognitive action (monitor, intervene); representation (status tiles + gate panel + filterable typed timeline); what the human changes (a STOP resolution, a filter); what changes in response (gate status, candidate export, visible entries); first-viewport job (now / allowed to continue / needs attention / consequence of my choice); export payload; no-JS equivalent (board readable, decide in chat). Completion: the representation is justified before the session starts.
3. **Inspect before editing.** Read project instructions, domain context, ADRs, relevant modules, and prior tests. Preserve unrelated dirty work and identify the highest correct test seams. Completion: the first vertical slice and focused command are named.
4. **Run red → green by slice.** Write one behavior test at an agreed seam, run it red for the intended reason, implement only enough to pass, and run focused type/check commands. Completion: the slice is externally observable and green.
5. **Refresh the board with every event.** After each slice, deviation, failed/green check, and material discovery, append the typed entry (`plan-confirmed`, `deviation`, `check`, `discovery`, `stop`; flag `needsHuman` honestly) to `scenario.json` and the notes, then regenerate: `node <skill>/references/acta2/generate-instrument.mjs --scenario scenario.json --out instrument.html`. Completion: tiles, counts, filters, and timeline all derive from the entries — the HTML is never hand-edited.
6. **Stop on contract changes.** Architecture, public API, data/schema, security, or scope changes open a visible STOP gate in the board **before** further work: gate reason, response options with one-line consequences, no preselection. The human resolves it in the instrument (candidate export) or in chat. Work resumes only after you restate the resolution and receive explicit confirmation; then record it in canonical state and regenerate board and notes. Completion: no slice lands while a gate is open; silence never resumes work.
7. **Validate and review.** Run focused checks throughout, the full project acceptance seam once at the end, and an internal two-axis review: repository standards and approved contract. Fix verified findings and rerun affected checks.
8. **Distill decisions and emit the record.** Prepare proposed updates for specs, ADRs, tickets, or docs; publish only after explicit approval. Write `canonical.json` (`{ "scenario": …, "accepted": … }`) and generate the record from it alone: `node <skill>/references/acta2/generate-record.mjs --canonical canonical.json --out record.html` — resolved gates with how they were accepted, the full timeline, checks at close, changed files. Completion: notes are complete with validation green or an honest blocker recorded.
9. **Commit gate.** Show the final scope, tests, review result, and proposed commit message. Create a commit only after explicit authorization. Never push or release unless separately requested.

## Guardrails

- Do not require another installed testing or review skill; use available capabilities as optional enhancements.
- Do not overwrite user changes, broaden scope to “clean things up,” or continue through a STOP gate.
- Keep notes append-only within the session and archive an approved prior revision before superseding it.
- The board shows working state only: an open gate renders open, and a resolved gate appears only after the resolution is accepted in chat and recorded canonically.
