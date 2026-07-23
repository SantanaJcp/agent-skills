# Acta v2 suite 0.2.0 promotion evidence

Status: collecting-promotion-evidence

Active artifact system: Acta v2 `0.2.0-pilot`. Acta `0.1.0` remains bundled
only as the rollback path until this report passes and the migration is
explicitly promoted.

This report is the blocking manual record for the initial fifteen-skill promotion cohort. Deterministic checks do not replace the evidence below.

## Evaluation preparation

Prepare isolated, revision-stamped projects with:

```bash
npm run qa:prepare -- --destination ../agent-skills-manual-qa
```

Follow [the evaluator runbook](evaluator-runbook.md). Each reviewer starts from [the evidence template](evidence/template.md) and submits one raw record under `docs/qa/evidence/`; the evidence integrator updates this report only after reviewing those records. A code fix invalidates affected evidence until it is rerun against the new full source revision.

## Client activation matrix

Record the exact stable client versions, every committed trigger/non-trigger case, observed activation, result against expectation, and confirmation that removing `agents/openai.yaml` does not change behavior.

| Skill | Codex | Claude Code | Sidecar-independent | Verdict |
| --- | --- | --- | --- | --- |
| make-me-realize | Pending | Pending | Pending | Pending |
| three-code-paths | Pending | Pending | Pending | Pending |
| interface-directions | Pending | Pending | Pending | Pending |
| change-blueprint | Pending | Pending | Pending | Pending |
| build-with-notes | Pending | Pending | Pending | Pending |
| do-i-understand-this | Pending | Pending | Pending | Pending |
| feel-the-flow | Pending | Pending | Pending | Pending |
| feature-xray | Pending | Pending | Pending | Pending |
| concept-lab | Pending | Pending | Pending | Pending |
| what-just-happened | Pending | Pending | Pending | Pending |
| draw-the-flow | Pending | Pending | Pending | Pending |
| draw-it-in-svg | Pending | Pending | Pending | Pending |
| deepen-the-codebase | Pending | Pending | Pending | Pending |
| find-the-cause | Pending | Pending | Pending | Pending |
| learning-workbench | Pending | Pending | Pending | Pending |

## Core-cycle end to end

Run the scenario in `tests/fixtures/core-cycle-project/SCENARIO.md` unchanged in current Codex and Claude Code. Record every canonical artifact, gate, handoff, publication boundary, STOP behavior, final diff, and understanding export.

- Codex version and result: Pending
- Claude Code version and result: Pending

## Browser matrix

- Current Chrome: all 13 instruments and all 13 records — Pending
- Current Safari: every interactive kind, one representative record, and critical interactions — Pending
- Current Firefox: every interactive kind, one representative record, and critical interactions — Pending

Verify offline `file://`, no-JS reading, clipboard fallback, disclosures, quiz/editor controls, 320px reflow, actual 400% zoom, print/PDF, monochrome meaning, and reduced motion.

## Accessibility

- Keyboard-only traversal and focus order: Pending
- VoiceOver representative family pass: Pending
- NVDA representative family pass: Pending

Failures block promotion. Windows authoring CI remains required; real-Windows serif rendering is a documented nonblocking risk.

## Promotion verdict

Pending. Do not move any cohort skill to `skills/` or prepare the v1.0.0 release candidate until every blocking row passes.
