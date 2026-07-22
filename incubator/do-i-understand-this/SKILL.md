---
name: do-i-understand-this
description: "Diagnose a user's understanding of an actual completed change with an evidence-grounded quiz, gap export, explanation, and retry. Use after implementation or review when comprehension matters; never use as a merge gate or generic code review."
license: Apache-2.0
metadata:
  tags: "learning, review, quiz"
---

# Do I Understand This

## Purpose

Test whether the user understands why a real change works, where it stops working, and how to operate or reverse it. This is diagnostic learning, never approval or merge policy.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Quiz scaffold](references/acta-scaffold.html).

## Process

1. **Ground the quiz.** Read the approved spec/plan when available, implementation notes, final diff, tests, and operational docs. Write `understanding.md` with the change revision and factual summary. Completion: every question can cite change evidence.
2. **Design diagnostic questions.** Cover causality, invariants/limits, failure behavior, rollback, security, and operations in proportion to actual risk. Use plausible answer choices with comparable length and no formatting clues. Avoid syntax trivia. Completion: each question distinguishes a meaningful misconception.
3. **Generate `view.html`.** Keep essential context and answer explanations available without JavaScript while making the interactive path useful. State prominently that the quiz is not a gate.
4. **Score as gaps, not pass/fail.** Record the attempt time because it is a real learning event. Export answered concepts, evidence, gaps, and confidence into Markdown and `gaps.json`. Completion: the user can name what to revisit.
5. **Remediate and retry.** Explain missed concepts briefly from the real change, point to evidence, and offer a fresh attempt that tests the concept rather than repeating wording. Stop when the user declines or the requested retry completes.

## Guardrails

- Do not block merge, release, cycle completion, or commit.
- Do not expose secrets or turn the quiz into an exhaustive implementation review.
- Do not claim understanding from a score alone; report the specific remaining gaps.
