---
name: deepen-the-codebase
description: "Analyze a codebase for evidence-backed module-deepening opportunities and compare candidates without refactoring. Use when architecture, seams, locality, testability, or AI navigability need improvement; do not use for immediate implementation or generic code cleanup."
license: Apache-2.0
metadata:
  tags: "architecture, analysis, refactoring"
---

# Deepen The Codebase

## Purpose

Find module changes that concentrate complexity behind simpler interfaces, then export one chosen direction for later blueprinting. This skill never refactors.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Compare scaffold](references/acta-scaffold.html).

## Vocabulary

Use **module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, and **locality** precisely. Use the project's domain terms; do not replace them with generic “service,” “component,” or “boundary” language when the domain already names the concept.

## Process

1. Read project context and relevant ADRs. If the user named a scope, use it. Otherwise inspect meaningful commit history to identify hot spots before widening the scan.
2. Explore organically for navigation friction, shallow modules, leaked decisions, scattered callers, missing locality, and tests forced onto artificial seams. Apply the deletion test: deleting a useful module should concentrate complexity, not merely move it.
3. Write `architecture-directions.md` with evidence-backed candidates. Each candidate includes involved modules, current interface, problem, before/after map, depth gain, locality/leverage, test-seam effect, ADR interaction, risks, and recommendation strength.
4. Present candidates at equal fidelity in `view.html`, then state the top recommendation. Do not design detailed interfaces before the user chooses a direction.
5. Open the handoff DecisionGate. When the user chooses, export `blueprint-seed.md` with evidence, target module, intended interface pressure, constraints, rejected candidates, and open questions. Completion: the choice is exported; the codebase is unchanged.

## Guardrails

- Do not equate more files, abstractions, or indirection with depth.
- Surface ADR conflicts only when real friction justifies reopening the decision.
- Do not implement, refactor, or update the domain model without a separate explicit request.
