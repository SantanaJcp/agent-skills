---
name: concept-lab
description: "Research and teach a concept through a manipulable model, trusted sources, declared simplifications, and optional retrieval practice. Use for focused conceptual understanding; do not use to document one repository feature or manage a long-term curriculum."
license: Apache-2.0
metadata:
  tags: "research, learning, visualization"
---

# Concept Lab

## Purpose

Turn a focused concept into an inspectable model that exposes consequences while keeping pedagogy distinct from production truth.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Explore scaffold](references/acta-scaffold.html).

## Process

1. Define the learner's question, current understanding, and the decision or skill the concept should support.
2. Research high-trust primary sources. Record source quality, date/version when relevant, and conflicting definitions. Never rely on parametric memory for load-bearing factual claims.
3. Write `concept-lab.md` with the model, vocabulary, invariants, consequences, limits, and citations. Label every reduced pedagogical model Simplification and state how production behavior differs.
4. Create one manipulable model whose controls change a derived consequence table. Write `model.json` only when the state is genuinely structured. Provide several static states and explanations for no-JS readers.
5. Generate `view.html` with waypoints, figures, controls, sources, and an optional retrieval check. Mark complete when the model is manipulable or fully described statically and every simplification is declared.

## Guardrails

- Do not pretend a general model documents the current repository; use feature-xray for that.
- Do not create a multi-session curriculum or spaced schedule; use learning-workbench.
- Cite claims near where they carry explanatory weight.
