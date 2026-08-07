# Acta v2 suite evaluator runbook

Use this runbook to collect comparable manual evidence for the published
fifteen-skill Acta collection. Test the prepared harness; do not edit skill
source while evaluating it. The initial `v1.0.0` browser/accessibility rows were
explicitly deferred; [GitHub Issue #8](https://github.com/SantanaJcp/agent-skills/issues/8)
tracks their prospective completion.

## 1. Prepare from an exact source revision

Prerequisites: Git, Node `>=22.20.0`, current stable Codex and/or Claude Code, and the browsers or assistive technology assigned to you.

From a clean clone at the revision under test:

```bash
npm ci
npm run check
npm run qa:prepare -- --destination ../agent-skills-manual-qa
```

The command refuses an existing destination and a dirty source worktree. It
creates one `manual-only/` project root containing the complete bundles. Do not
remove `agents/openai.yaml`: its Codex policy is part of the supported
manual-invocation contract.

Confirm that `QA-MANIFEST.json` contains the expected full source revision, `active_artifact_system: "acta2"`, and the expected Acta v2 version before beginning. Never include credentials, private repositories, or production data in evidence.

## 2. Record the environment

Copy `docs/qa/evidence/template.md` into a new evidence file. Record reviewer,
operating system, hardware relevant to rendering, exact
client/browser/assistive-technology versions, source revision, harness variant,
and test date. Use `docs/qa/evidence/<surface>-<reviewer>-YYYY-MM-DD.md` when
contributing the result. Follow the [evidence policy](evidence/README.md): commit
only the sanitized final summary and keep raw logs/captures outside the repo.

A pass requires an observed result, not only the absence of an error. Screenshots may supplement the Markdown record but do not replace it.

## 3. Client activation

Open `manual-only/` as the project root in the assigned current stable client.
For every assigned skill:

1. Read its cases in `smoke-cases/<skill>.yaml`.
2. For each `trigger`, start a fresh conversation and send the bare prompt
   exactly as committed. Verify that none of the fifteen skills activates.
3. Start another fresh conversation, explicitly invoke the named skill, and
   append the committed prompt: use `$<skill-name>` in Codex and
   `/<skill-name>` in Claude Code. Verify that the requested skill activates and
   its material behavior matches `expected`.
4. For each `non-trigger`, explicitly invoke the case's named skill in a fresh
   conversation. Verify that it honors its boundary by declining or redirecting
   as described in `expected`, rather than executing the adjacent workflow.
5. Treat bare-prompt activation, failed explicit activation, or materially
   wrong behavior as a failure.

For each paired case in `smoke-cases/collisions.yaml`, first verify that its bare
prompt activates no suite skill. Then explicitly invoke the expected owner and
verify the stated boundary. Cross-skill descriptions remain catalog guidance;
they no longer authorize implicit routing.

### Automated CLI isolation

When collecting activation evidence through a CLI, run every prompt in a
**fresh disposable copy** of the selected harness. Remove prior `.agent-work`
state by discarding the copy, not by reusing a conversation. Keep project
skills enabled while excluding personal instructions, plugins, hooks, and
memory that could select a skill or leak prior answers:

- Codex: use `codex exec --ephemeral --ignore-user-config --skip-git-repo-check ...`.
- Claude Code: use `claude -p --no-session-persistence --setting-sources project ...`.

Give the client only the tool permissions required to read and write the
synthetic harness. A permission denial is invalid test setup, not a skill
failure. Record the complete command, client settings, activated skill, and
protocol/reference reads in the evidence file.

## 4. Six-stage core cycle

Open a fresh copy of the applicable harness and follow `SCENARIO.md` unchanged. Invoke the six core skills in order when the scenario calls for them. Record:

- canonical Markdown/JSON artifacts and `.agent-work` locations;
- every explicit DecisionGate and handoff;
- the separate spec and implementation-plan approvals;
- the remote-API scope probe and resulting STOP gate;
- focused/full test results and final diff;
- the post-change diagnostic and exported learning gaps;
- any publication or commit attempted without explicit authorization.

Run `npm test` before and after the cycle. The initial baseline contains one passing test; the completed scenario must preserve the Node-only setup.

## 5. Browser and interaction matrix

Open the assigned files from `acta-fixtures/` directly through `file://`.

- Chrome: all 13 Acta v2 instruments and all 13 Acta v2 records under `acta-fixtures/<skill>/`.
- Safari and Firefox: at least one instrument of every interactive kind (decision, STOP gate, model, prototype, quiz, and checklist), at least one record, plus every assigned critical interaction.

Record offline loading, source/summary order, DecisionGate readability, disclosures, quiz controls, copy success and manual-copy fallback, no-JavaScript reading, 320px reflow, actual 400% zoom, reduced motion, monochrome meaning, and print/PDF output. Essential information may not depend on JavaScript, hover, color, or horizontal page scrolling; code/table/flow wrappers may scroll locally.

## 6. Accessibility matrix

For assigned representative artifacts, test keyboard-only traversal and visible focus before screen-reader passes. Record control names, reading order, status announcements, disclosure state, quiz feedback, diagram text alternatives, and export access.

- macOS: current VoiceOver with Safari.
- Windows: current NVDA with a supported browser.

A failure in keyboard, 400% zoom, VoiceOver, or NVDA blocks promotion. Windows serif rendering differences alone are documented but nonblocking.

## 7. Submit and invalidate evidence correctly

Commit only your sanitized evidence summary on a `qa/<surface>-<reviewer>`
branch. Keep captures and raw command/model logs in a reviewer-controlled
location outside the repository unless a maintainer explicitly approves a
small, scrubbed artifact. Do not edit the central verdict table unless you are
the evidence integrator.

When a test finds a defect:

1. preserve the failing observation against its source revision;
2. fix the defect in a separate change;
3. prepare a new harness from the new clean revision;
4. rerun the affected cases and any dependent end-to-end path;
5. retain both records and mark the older verdict superseded.

For future promotions, all required evidence must pass unless a reviewed ADR
records a visible waiver and a public issue tracks the remaining work.
