<!-- acta2-materialized: v0.2.0 protocol sha256=f88a7bcf7bda43a15ed604182b8d38e489c43d5649498630843f6f85f2e67dc2; do not edit by hand -->
# Acta v2 protocol — instrument, candidate, acceptance, record

This protocol extends the Acta 0.1 artifact protocol for every HTML skill in
the suite manifest (`design/acta2/lib/suite.mjs`) — piloted by
`three-code-paths`, `build-with-notes`, and `concept-lab` (ADR 0003) and
generalized to the full suite (ADR 0004), and promoted (ADR 0005). Where this file
is silent, the Acta 0.1 protocol (workspace, canonical frontmatter, decisions,
publication) still applies. Markdown/JSON remain the only canonical state.
Record-only skills (`feature-xray`, `what-just-happened`) skip the instrument
half of the loop: their canonical state is accepted directly in chat and the
record is generated from it. `feel-the-flow` is instrument-only: its prototype
is disposable by design and leaves no durable record.

## The loop

```
ground → instrument brief → information topology → instrument.html (open)
      → human inspects/manipulates → candidate export
      → agent restates the change → explicit acceptance in chat
      → canonical Markdown/JSON updated → record.html regenerated
```

## Instrument brief (before any long prose)

Before drafting canonical content or generating HTML, record in the canonical
Markdown: the human question, the cognitive action (compare / monitor /
simulate), the primary representation, what the human can change, what changes
in response, the first-viewport job, the export payload, and the no-JS
equivalent. If the honest answer is "render prose attractively," skip the
instrument and produce Markdown plus, at most, a record view.

## Instruments

- While the decision, session, or exploration is **open**, write the complete
  structured scenario as `scenario.json` and generate the instrument with the
  bundled generator:

  ```
  node <skill>/references/acta2/generate-instrument.mjs \
    --scenario scenario.json \
    --out instrument.html
  ```

  The generator renders the static no-JS DOM, the data island, and the runtime
  from that one input. **Never edit the `acta2-data` island, the static DOM,
  or any generated HTML by hand** — change `scenario.json` and regenerate.
  The installed `instrument.html` is a rendered example, not a template to
  fill. After acceptance, generate the record the same way:
  `node <skill>/references/acta2/generate-record.mjs --canonical canonical.json --out record.html`.
- Give every single-decision scenario a durable identity. Decision and model
  scenarios declare `decisionId`; STOP scenarios use `gate.id`. Model
  scenarios also declare the one `acceptanceToken` that may appear in an
  accepted decision. The canonical decision must copy that identity and,
  for decision/STOP instruments, the accepted working rationale exactly.
  Contradictory duplicates are rejected before any record is written.
- A downstream gate that depends on an already accepted artifact declares
  `requiredPriorDecisions`: the prior decision id, allowed accepted selection,
  artifact path, and accepted revision. The canonical decision chain must
  carry those values exactly and exactly once. A missing, rejected, duplicated,
  or revision-mismatched prerequisite cannot produce a record.
- The instrument shows working state only. It must never display an approved,
  accepted, resolved, or completed stamp, and it must never embed a
  pre-authored export payload.
- All dynamic writes go through safe DOM APIs (`textContent`,
  `createElement(NS)`, attribute setters). No `innerHTML`-class sinks, inline
  handlers, storage, network resources, or file writes.
- Without JavaScript the question, the model/options, the open gate, and the
  instructions to decide in chat must remain readable. Use native
  `<details>` disclosure; print expands it.

## Candidate export and acceptance

- Interaction produces a **candidate** payload (Markdown with
  `payload: "candidate"` frontmatter, JSON equivalent) derived from live
  working state. The copy button copies exactly what is displayed; the runtime
  re-verifies displayed-vs-recomputed on every change and before copying.
- The browser never updates canonical files. The human carries the candidate
  into chat (paste, or an unambiguous natural-language selection).
- On receiving a candidate the agent must: restate exactly what will change;
  wait for explicit confirmation; only then update canonical Markdown/JSON
  (archiving the prior approved revision per Acta 0.1); then regenerate the
  record. Silence, a closed tab, or an exported file is never approval.
- A STOP gate resolution candidate authorizes nothing by itself; work resumes
  only after the conversational acceptance is recorded in canonical state.

## Records

- Generate `record.html` from **accepted canonical state only**, after
  acceptance — never from browser state and never while the gate is open.
- The record keeps the full Acta identity: complete provenance header, status
  stamps, epistemic labels, evidence register, print-first styling. It has no
  decision controls. It preserves rejected alternatives and their change
  conditions.
- If canonical state changes again, regenerate the record; the instrument for
  a resolved gate is stale and must be regenerated or removed.
