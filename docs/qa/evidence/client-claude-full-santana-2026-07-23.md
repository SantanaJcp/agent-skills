# Acta v2 — Claude Code routing and trigger-behavior evidence

Status: **PASS for the scope recorded here**  
Reviewer: Codex-orchestrated local Claude Code evaluation for Santana  
Test date: 2026-07-23

## Scope verdict

| Matrix | Final result | Notes |
| --- | ---: | --- |
| Skill routing | **69/69 PASS** | 60 per-skill trigger/non-trigger cases, 7 collisions, 2 sidecarless spot checks; earlier failures are superseded below. |
| Trigger behavior | **30/30 PASS** | Two triggers for each of 15 skills; PASS required material behavior, not invocation alone. |
| Collisions | **7/7 PASS** | Expected owner selected in every paired boundary. |
| Sidecarless runtime spot checks | **2/2 PASS** | One positive trigger and one adjacent non-trigger preserved selection without `agents/openai.yaml`. |

**Verdict:** the tested Claude Code routing and isolated trigger-behavior scope passes.

## Provenance and environment

- Initial routing revision: `74a3653240fe8272ae4d45c992831487d2580418`.
- Routing fixes: `f22954b63629d34bdf261e0c9f13bdca34220c39`, then `b10e7d81ad150e37944ff99403d921bbc399a7dd`.
- Primary trigger-behavior revision: `b10e7d81ad150e37944ff99403d921bbc399a7dd`.
- Behavior supplements: `c24c366a8ebebb1abfe7e0bb9906a7b0b29e74c3`.
- Client: Claude Code `2.1.206`; requested model `claude-sonnet-5`.
- Host: macOS `26.5.2` (`25F84`), Apple Silicon (`arm64`).
- Isolation command shape:

  ```text
  claude -p --no-session-persistence --setting-sources project \
    --model sonnet --permission-mode bypassPermissions \
    --dangerously-skip-permissions --output-format stream-json --verbose \
    <exact-committed-prompt>
  ```

- Every case used a fresh disposable copy of the synthetic public harness. Personal settings, plugins, hooks, MCP servers, prior conversation state, and `.agent-work` state were excluded.
- Every selected init reported `apiKeySource: none`; selected rate events were `five_hour: allowed`; `isUsingOverage: false`; no fallback model was configured. No API-key or usage-credit fallback was used.

## Per-skill result

Routing counts below are the committed two triggers plus two adjacent non-triggers. Trigger behavior is the separate full-response/material-evidence pass.

| Skill | Routing | Trigger behavior | Material evidence boundary |
| --- | ---: | ---: | --- |
| `build-with-notes` | **4/4 PASS** | **2/2 PASS** | Honest missing-blueprint STOP; separate run demonstrated red/green slices, code/tests, and live notes. |
| `change-blueprint` | **4/4 PASS** | **2/2 PASS** | Separate specification/plan artifacts and explicit Gate A/Gate B state; no implementation. |
| `concept-lab` | **4/4 PASS** | **2/2 PASS** | Specific scoping question before fabrication; separate manipulable cache-invalidation lab with sources/simplifications. |
| `deepen-the-codebase` | **4/4 PASS** | **2/2 PASS** | Honest no-hotspot STOP; separate architecture directions and rendered comparison. |
| `do-i-understand-this` | **4/4 PASS** | **2/2 PASS** | Evidence-backed STOP when no change existed; no fabricated quiz. |
| `draw-it-in-svg` | **4/4 PASS** | **2/2 PASS** | Honest source/audience questions when the requested explanation or architecture was absent. |
| `draw-the-flow` | **4/4 PASS** | **2/2 PASS** | Clarification boundary plus completed `flow.md`, structured scenario, and accessible instrument. |
| `feature-xray` | **4/4 PASS** | **2/2 PASS** | Source-backed STOP rather than inventing password-reset/job-retry features absent from the fixture. |
| `feel-the-flow` | **4/4 PASS** | **2/2 PASS** | Asked for the concrete retry/animation decision before creating a misleading prototype. |
| `find-the-cause` | **4/4 PASS** | **2/2 PASS** | Established the available baseline and stopped before unsupported diagnosis when no endpoint/regression existed. |
| `interface-directions` | **4/4 PASS** | **2/2 PASS** | Three-direction comparison instrument with trade-offs and an open human choice; honest missing-dashboard question. |
| `learning-workbench` | **4/4 PASS** | **2/2 PASS** | Requested the durable workspace/location instead of fabricating prior learning state. |
| `make-me-realize` | **4/4 PASS** | **2/2 PASS** | `realization.md`, blind-spot pass, and dependency-ordered frontier questions before design. |
| `three-code-paths` | **4/4 PASS** | **2/2 PASS** | Honest requirement/structural-seam questions rather than fake alternatives; comparison artifact where context existed. |
| `what-just-happened` | **4/4 PASS** | **2/2 PASS** | Requested real impact/log/timeline evidence instead of fabricating an incident record. |

## Collision matrix

| Boundary | Expected owner | Observed | Verdict |
| --- | --- | --- | ---: |
| `make-me-realize` vs `change-blueprint` | `make-me-realize` | `make-me-realize` | **PASS** |
| `three-code-paths` vs `interface-directions` | `three-code-paths` | `three-code-paths` | **PASS** |
| `feel-the-flow` vs `build-with-notes` | `feel-the-flow` | `feel-the-flow` | **PASS** |
| `feature-xray` vs `concept-lab` | `feature-xray` | `feature-xray` | **PASS** |
| `what-just-happened` vs `find-the-cause` | `what-just-happened` | `what-just-happened` | **PASS** |
| `deepen-the-codebase` vs `build-with-notes` | `deepen-the-codebase` | `deepen-the-codebase` | **PASS** |
| `draw-the-flow` vs `draw-it-in-svg` | `draw-the-flow` | `draw-the-flow` | **PASS** |

## Sidecar independence

- At revision `b10e7d8`, the `with-sidecars` and `without-sidecars` Claude skill trees contain **283 byte-identical portable files** after excluding `agents/openai.yaml`.
- The harness contains 30 `agents/openai.yaml` copies with sidecars and zero without; those files are Codex presentation metadata, not Claude skill instructions.
- Runtime spot checks without sidecars:
  - `make-me-realize` positive trigger → `make-me-realize` (**PASS**).
  - `build-with-notes` adjacent non-trigger → `three-code-paths`, not `build-with-notes` (**PASS**).

## Superseded findings

Preserved failures remain valid observations against their recorded revisions, but they do not represent the final selected evidence.

| Earlier observation | Superseding evidence | Final |
| --- | --- | ---: |
| Initial `learning-workbench` trigger 2 timed out before activation. | Fresh full rerun activated `learning-workbench` and stopped honestly because the claimed Spanish workspace did not exist. | **PASS** |
| Five adjacent non-triggers failed to select `feature-xray`, `build-with-notes`, `three-code-paths` (two cases), or `do-i-understand-this`. | Revision `f22954b` reruns selected all five expected owners. | **PASS** |
| “Find why this specific test is failing” did not select `find-the-cause`, including the first `f22954b` rerun. | Revision `b10e7d8` selected `find-the-cause`, ran the green baseline twice, and opened the correct no-red-reproduction STOP. | **PASS** |
| `draw-it-in-svg` trigger 2 did not invoke the skill in the primary behavior sweep. | `c24c366` supplement selected `draw-it-in-svg` and asked for the missing explanation/audience/style before drawing. | **PASS** |
| `concept-lab` trigger 1 timed out during research. | `c24c366` supplement asked specific domain, purpose, and learner-level scoping questions before fabricating a model. | **PASS** |
| `do-i-understand-this` trigger 1 timed out during inspection. | `c24c366` supplement verified no implementation/diff existed and produced an evidence-backed STOP. | **PASS** |
| `draw-the-flow` trigger 1 timed out after only a textual draft. | `c24c366` supplement produced `flow.md`, `scenario.json`, and `instrument.html`. | **PASS** |

## Evidence index

- Initial 69-case routing record: `/tmp/acta-claude-full-activation.md`
- Initial routing raw state/logs: `/tmp/acta-claude-full-logs/state.json`, `/tmp/acta-claude-full-logs/`
- Seven ambiguous-case full rerun: `/tmp/acta-claude-issue-reruns.md`, `/tmp/acta-claude-issue-rerun-logs/`
- `f22954b` routing-fix validation: `/tmp/acta-claude-routing-f22954b.md`, `/tmp/acta-claude-routing-f22954b-logs/`
- `b10e7d8` final routing case: `/tmp/acta-claude-routing-b10e7d8.md`, `/tmp/acta-claude-routing-b10e7d8-logs/`
- Consolidated 30-case behavior audit: `/tmp/acta-claude-trigger-behavior-consolidated.md`, `/tmp/acta-claude-trigger-behavior-consolidated.json`
- `c24c366` supplements:
  - `/tmp/acta-claude-c24c366-svg-logs/`
  - `/tmp/acta-claude-concept-lab-long-c24c366-logs/`
  - `/tmp/acta-claude-do-i-understand-this-long-c24c366-logs/`
  - `/tmp/acta-claude-draw-the-flow-long-c24c366-logs/`

## Scope limitations

This record does **not** claim completion of:

- the six-stage end-to-end core cycle;
- browser/offline/interaction/print/PDF testing;
- keyboard, 400% zoom, reduced-motion, monochrome, VoiceOver, or NVDA accessibility testing.

Those remain separate promotion gates. The PASS verdict here is limited to Claude Code skill routing, collision handling, sidecar independence, and isolated trigger behavior.

