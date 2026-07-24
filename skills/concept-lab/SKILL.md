---
name: concept-lab
description: "Research and teach a concept through a manipulable model, trusted sources, declared simplifications, and optional retrieval practice. Use for focused conceptual understanding; do not use to document one repository feature or manage a long-term curriculum."
license: Apache-2.0
metadata:
  tags: "research, learning, visualization"
---

# Concept Lab

## Purpose

Turn a focused concept into a manipulable model the learner drives, keeping pedagogy distinct from production truth.

Read [the Acta v2 protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: write `scenario.json` and run [the bundled generator](references/acta2/generate-instrument.mjs); after acceptance, write `canonical.json` and run [the record generator](references/acta2/generate-record.mjs). [instrument.html](references/instrument.html) and [record.html](references/record.html) are rendered examples of the outputs.

HTML earns its place here when the concept has parameters whose consequences must be **felt**: the learner moves a control and watches a derived consequence change, which no paragraph can substitute. If the concept has no meaningful parameter or derived behavior, teach it in Markdown with a figure — a dead slider is worse than no slider.

## Process

1. **Define the learning target.** Record the learner's question, current understanding, and the decision or skill the concept should support. Completion: you can state what the learner will be able to do afterwards.
2. **Research high-trust primary sources.** Record source quality, date/version when relevant, and conflicting definitions. Never rely on parametric memory for load-bearing factual claims.
3. **Write the instrument brief** into `concept-lab.md` before drafting teaching prose: human question; cognitive action (simulate/tune); representation (which spatial visualization, which parameters, which derived consequence); what the human changes; what updates in response; first-viewport job (model + controls + consequence, before any prose); export payload (chosen parameters + observed conclusion); no-JS equivalent (default state fully rendered statically). Completion: every control named in the brief changes a consequence the learner can see.
4. **Build the model as data.** Write `scenario.json` (parameters, toggles, sourced facts, declared simplifications) and generate the instrument: `node <skill>/references/acta2/generate-instrument.mjs --scenario scenario.json --out instrument.html`. The generator renders the default state statically (visualization, legend, consequence table) so the no-JS baseline can never diverge; controls re-derive both live. Label every reduced pedagogical model **Simplification** and state how production behavior differs, next to sourced **Facts**. Completion: the generator ran clean, the model is manipulable and deterministic, and every simplification is declared beside the model, not in a footnote.
5. **Close the loop.** The learner explores, records an observed conclusion in the instrument, and exports the candidate (parameters + conclusion) — or states it in chat. Restate it, obtain explicit confirmation, then write `canonical.json` (`{ "scenario": …, "accepted": … }` including the accepted parameters, conclusion, and derived consequences) plus `concept-lab.md`, and generate the record from the canonical state alone: `node <skill>/references/acta2/generate-record.mjs --canonical canonical.json --out record.html`. Completion: the record preserves the accepted model state and its epistemic labels, and every number in the conclusion matches the derived model.

## Guardrails

- Do not pretend a general model documents the current repository; use feature-xray for that.
- Do not create a multi-session curriculum or spaced schedule; use learning-workbench.
- Cite claims near where they carry explanatory weight.
- The model must respond to its controls before you ship it; a static fallback is a degradation path, not the deliverable.
