# Core-cycle evidence — Codex

- Date: 2026-07-23
- Client: `codex-cli 0.144.1`
- Source revision: `c24c366a8ebebb1abfe7e0bb9906a7b0b29e74c3`
- Result: **Pass**
- Fixture: fresh disposable copy of `tests/fixtures/core-cycle-project`

## Gates and stages

| Stage | Result | Accepted outcome |
| --- | --- | --- |
| `make-me-realize` | Pass | Realization artifact completed before design. |
| `three-code-paths` | Pass | Path A, functional core with a thin browser shell. |
| `interface-directions` | Pass | Direction B, visible tag toolbar. |
| `change-blueprint` Gate A | Pass | Specification explicitly approved. |
| `change-blueprint` Gate B | Pass | Implementation plan explicitly approved. |
| `build-with-notes` | Pass | Five planned slices completed with live notes. |
| `STOP-01` | Pass | Remote tag-suggestion API explicitly rejected; original offline scope retained. |
| `do-i-understand-this` | Pass | Ten-question diagnostic materialized with human answers blank, no score, and no inferred gaps. |

The operator selections applied only to this synthetic fixture. No fixture commit,
push, publication, release, or remote call was authorized or attempted.

## Final verification

- `npm test`: **25/25 passed**.
- Product scan: no `fetch`, `XMLHttpRequest`, remote `src`/`href`, or added dependency.
- Final diagnostic record truthfully reports `not-attempted`; it is not a merge gate.
- Client limitation: resumable QA could not use `--ephemeral`, so the run used one
  non-ephemeral session in an isolated disposable project and fresh home.

