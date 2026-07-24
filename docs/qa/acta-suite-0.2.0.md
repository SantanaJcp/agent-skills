# Acta v2 suite 0.2.0 promotion evidence

Status: promoted-with-deferred-browser-and-accessibility-evidence

Active artifact system: Acta v2 `0.2.0`. Acta `0.1.0` remains bundled as a
compatibility fallback; Acta v2 is authoritative.

This is the versioned promotion record for the initial fifteen-skill cohort.
Deterministic checks do not replace the evidence below, and the deferred rows
remain historical facts after publication.

## Evaluation preparation

Prepare isolated, revision-stamped projects with:

```bash
npm run qa:prepare -- --destination ../agent-skills-manual-qa
```

Follow [the evaluator runbook](evaluator-runbook.md). Each reviewer starts from
[the evidence template](evidence/template.md) and submits one sanitized final
summary under `docs/qa/evidence/`; raw logs and captures stay outside the
repository. The evidence integrator updates this report only after reviewing
those summaries. A code fix invalidates affected evidence until it is rerun
against the new full source revision.

## Client activation matrix

Record the exact stable client versions, every committed trigger/non-trigger case, observed activation, result against expectation, and confirmation that removing `agents/openai.yaml` does not change behavior.

Completed evidence:

- [Codex full client evidence](evidence/client-codex-full-santana-2026-07-23.md): `codex-cli 0.144.1`, 97/97 base cases plus corrected-revision supplements.
- [Claude Code full client evidence](evidence/client-claude-full-santana-2026-07-23.md): Claude Code `2.1.206` / `claude-sonnet-5`, 69/69 routing cases and 30/30 material trigger-behavior cases.
- Final corrected revision: `c24c366a8ebebb1abfe7e0bb9906a7b0b29e74c3`.
- Deterministic repository seam at the final revision: `npm run check` — 76/76 passing.

| Skill | Codex | Claude Code | Sidecar-independent | Verdict |
| --- | --- | --- | --- | --- |
| make-me-realize | Pass | Pass | Pass | Pass |
| three-code-paths | Pass | Pass | Pass | Pass |
| interface-directions | Pass | Pass | Pass | Pass |
| change-blueprint | Pass | Pass | Pass | Pass |
| build-with-notes | Pass | Pass | Pass | Pass |
| do-i-understand-this | Pass | Pass | Pass | Pass |
| feel-the-flow | Pass | Pass | Pass | Pass |
| feature-xray | Pass | Pass | Pass | Pass |
| concept-lab | Pass | Pass | Pass | Pass |
| what-just-happened | Pass | Pass | Pass | Pass |
| draw-the-flow | Pass | Pass | Pass | Pass |
| draw-it-in-svg | Pass | Pass | Pass | Pass |
| deepen-the-codebase | Pass | Pass | Pass | Pass |
| find-the-cause | Pass | Pass | Pass | Pass |
| learning-workbench | Pass | Pass | Pass | Pass |

All seven committed collision cases passed in both clients. Codex repeated one trigger and one adjacent non-trigger per skill without sidecars (30/30); Claude's portable trees were byte-identical and its two runtime spot checks passed. Superseded failures and the fixes that closed them remain documented in the client evidence files.

## Core-cycle end to end

Run the scenario in `tests/fixtures/core-cycle-project/SCENARIO.md` unchanged in current Codex and Claude Code. Record every canonical artifact, gate, handoff, publication boundary, STOP behavior, final diff, and understanding export.

- [Codex core-cycle evidence](evidence/core-cycle-codex-santana-2026-07-23.md):
  `codex-cli 0.144.1`, Pass — 25/25 final fixture tests.
- [Claude Code core-cycle evidence](evidence/core-cycle-claude-santana-2026-07-23.md):
  Claude Code `2.1.206` / `claude-sonnet-5`, Pass — 11/11 final fixture tests.

Both clients completed the full six-stage flow. The specification and plan gates
were explicitly approved only inside disposable synthetic projects; both STOP
gates explicitly rejected the remote-API expansion. No network behavior or new
dependency entered either implementation. Human diagnostic answer fields remain
blank, because `do-i-understand-this` is diagnostic rather than an approval gate.

## Browser matrix — explicitly deferred

- Current Chrome: all 13 instruments and all 13 records — Deferred
- Current Safari: every interactive kind, one representative record, and critical interactions — Deferred
- Current Firefox: every interactive kind, one representative record, and critical interactions — Deferred

Verify offline `file://`, no-JS reading, clipboard fallback, disclosures, quiz/editor controls, 320px reflow, actual 400% zoom, print/PDF, monochrome meaning, and reduced motion.

## Accessibility — explicitly deferred

- Keyboard-only traversal and focus order: Deferred
- VoiceOver representative family pass: Deferred
- NVDA representative family pass: Deferred

The owner explicitly deferred the browser and assistive-technology matrices for
the initial promotion on 2026-07-23. This is a transparent waiver, not a claim
that those surfaces passed. Windows authoring CI remains required and passed.
[GitHub Issue #8](https://github.com/SantanaJcp/agent-skills/issues/8) is the
public successor for this deferred work.

## Promotion verdict

**Pass under explicit owner waiver.** Client activation and the full core cycle
passed in Codex and Claude Code, deterministic checks passed on Linux and
Windows, and the owner authorized the initial cohort promotion while deferring
browser and accessibility evidence. All fifteen skills were subsequently moved
to `skills/`, release `v1.0.0` was published, and Acta v2 `0.2.0` became the
authoritative artifact system. The remote API expansion remains rejected.
