---
name: do-i-understand-this
description: "Diagnose a user's understanding of an actual completed change with an evidence-grounded quiz, gap export, explanation, and retry. Use after implementation or review for requests such as quiz me on the pull request or change we just implemented; never use as a merge gate or generic code review."
license: Apache-2.0
metadata:
  tags: "learning, review, quiz"
---

# Do I Understand This

## Purpose

Test whether the user understands why a real change works, where it stops working, and how to operate or reverse it. This is diagnostic learning, never approval or merge policy.

Read [the Acta v2 protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: write `scenario.json` (diff facts, before/after mental-model flows, evidence cards, questions with answers/explanations/gap names) and run [the bundled generator](references/acta2/generate-instrument.mjs); after the gaps export is confirmed, write `canonical.json` and run [the record generator](references/acta2/generate-record.mjs). The Acta 0.1 recipe ([acta-protocol.md](references/acta-protocol.md), [acta-scaffold.html](references/acta-scaffold.html)) remains bundled as the published compatibility fallback; Acta v2 is authoritative.

## Process

1. **Ground the quiz.** Read the approved spec/plan when available, implementation notes, final diff, tests, and operational docs. Write `understanding.md` with the change revision and factual summary. Completion: every question can cite change evidence.
2. **Design diagnostic questions.** Cover causality, invariants/limits, failure behavior, rollback, security, and operations in proportion to actual risk. Use plausible answer choices with comparable length and no formatting clues. Avoid syntax trivia. Completion: each question distinguishes a meaningful misconception.
3. **Generate the instrument.** `node <skill>/references/acta2/generate-instrument.mjs --scenario scenario.json --out instrument.html` — the mental model renders before any question, explanations live in per-question disclosures so the no-JS page stays complete, and the page states prominently that the check is never a gate.
4. **Score as gaps, not pass/fail.** The candidate export carries answers, score, and named gaps; after explicit confirmation in chat, write `canonical.json` and generate the record (`node <skill>/references/acta2/generate-record.mjs --canonical canonical.json --out record.html`). Completion: the user can name what to revisit.
5. **Remediate and retry.** Explain missed concepts briefly from the real change, point to evidence, and offer a fresh attempt that tests the concept rather than repeating wording. Stop when the user declines or the requested retry completes.

## Guardrails

- Do not block merge, release, cycle completion, or commit.
- Do not expose secrets or turn the quiz into an exhaustive implementation review.
- Do not claim understanding from a score alone; report the specific remaining gaps.
