---
name: interface-directions
description: "Explore and compare genuinely distinct product interface directions in an Acta report. Use when a user-facing change needs a decision about layout, density, hierarchy, tone, or behavior; do not use for backend changes or code-architecture choices."
license: Apache-2.0
metadata:
  tags: "design, interface, comparison"
---

# Interface Directions

## Purpose

Resolve a product-interface direction before implementation planning. Acta frames the report; it must not make the candidate interfaces look alike.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Compare scaffold](references/acta-scaffold.html).

## Process

1. **Verify applicability.** Identify the unresolved user-facing decision and read product constraints, current UI, design tokens, accessibility rules, and prior code-path choice. Completion: the decision materially concerns layout, density, hierarchy, tone, or behavior. If not, stop without manufacturing UI work.
2. **Choose comparison axes.** State the audience, task, device/context, information priority, interaction model, and success criteria. Completion: axes can distinguish directions through behavior, not decoration alone.
3. **Create distinct directions.** Produce three target-product mini-mockups with equal fidelity. Each direction must differ on multiple declared axes; Acta styling stays in the surrounding report. Completion: removing colors still leaves distinct hierarchy or behavior.
4. **Compare honestly.** For each direction record the task flow, responsive behavior, accessibility implications, implementation consequences, risks, strengths, and change conditions. Completion: every candidate has the same evidence shape.
5. **Open DecisionGate D-01.** Write `interface-directions.md`, generate `view.html`, present the recommendation after the comparison, and accept an explicit selection through chat or export into `decision.json`. Completion: one direction is approved or the artifact remains awaiting decision.
6. **Handoff.** Export target behavior, hierarchy, responsive rules, reusable tokens/components, rejected directions, and unresolved details as blueprint input. Never implement or invoke the next skill automatically.

## Guardrails

- Do not apply Acta tokens to product candidates unless the product itself uses Acta.
- Do not present three cosmetic themes over the same structure.
- Keep candidate controls demonstrative; do not connect them to production data or services.
