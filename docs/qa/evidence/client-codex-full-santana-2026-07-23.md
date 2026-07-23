# Acta v2 Codex client-activation evidence — final

Status: complete — assigned scope passed

## Provenance and supersession

| Revision | Evaluated scope | Outcome | Supersession |
| --- | --- | --- | --- |
| `74a3653240fe8272ae4d45c992831487d2580418` | Complete 97-case activation matrix: 60 committed skill cases, 7 collisions, and 30 sidecar-independent repeats | Routing 97/97; initial bounded behavior evidence collected | Base evidence |
| `f22954b63629d34bdf261e0c9f13bdca34220c39` | Six corrected alternative-skill boundaries and four long-behavior closures | 6/6 boundaries and 4/4 long behaviors passed | Supersedes the corresponding base boundaries and four earlier incomplete bounded runs |
| `b10e7d81ad150e37944ff99403d921bbc399a7dd` | `Find why this specific test is failing.` | `find-the-cause` activated; green baseline produced an honest STOP | Supersedes the earlier selection-only failing-test boundary |
| `c24c366a8ebebb1abfe7e0bb9906a7b0b29e74c3` | `Turn this explanation into a labeled vector diagram that must work outside the report.` | `draw-it-in-svg` activated; missing explanation produced an honest STOP | Supersedes the corresponding SVG boundary under the final description |

The final verdict uses the newest applicable observation for each affected case. Supplements replace cases; they do not increase the 97-case denominator.

## Environment and isolation

- Reviewer: Codex-directed local CLI automation.
- Operating system: macOS 26.5.2.
- Codex: `codex-cli 0.144.1`.
- Model: client default; the JSONL event stream did not expose a model identifier.
- Authentication: existing ChatGPT/Codex authentication from `CODEX_HOME=/Users/santana/.codex`; no credential or API key was copied into evidence.
- Every prompt was sent exactly as committed, without adding a skill name or evaluator instruction.
- Every case used a fresh disposable harness copy and `--ephemeral --ignore-user-config --skip-git-repo-check`.
- Each process received a fresh empty `HOME`; `CODEX_HOME` was retained only for authentication and client runtime.
- Selection runs used `-s read-only --json --color never` and stopped only after an event-level command directly targeted `.agents/skills/<name>/SKILL.md`.
- Material-behavior runs used `-s workspace-write`; unresolved bounded runs received fresh-copy retries rather than session continuation.

Commands:

```text
HOME=<fresh-empty-home> CODEX_HOME=/Users/santana/.codex codex exec \
  --ephemeral --ignore-user-config --skip-git-repo-check \
  -s read-only --json --color never -C <fresh-copy> <exact-prompt>

HOME=<fresh-empty-home> CODEX_HOME=/Users/santana/.codex codex exec \
  --ephemeral --ignore-user-config --skip-git-repo-check \
  -s workspace-write --json --color never -C <fresh-copy> <exact-prompt>
```

## Final summary

- Authoritative activation matrix: **97/97 PASS**.
- Failures: **0**.
- Incomplete: **0**.
- Setup-blocked: **0**.
- Corrected `f22954b` boundaries: **6/6 PASS**.
- Corrected `f22954b` long-behavior closures: **4/4 PASS**.
- Final `b10e7d8` diagnostic boundary: **1/1 PASS**.
- Final `c24c366` SVG boundary: **1/1 PASS**.

## Results by skill

Each row includes two positive triggers and two adjacent non-triggers with sidecars, plus one trigger and one adjacent non-trigger without sidecars.

| Skill | With sidecars | Without sidecars | Newest targeted evidence | Verdict |
| --- | ---: | ---: | --- | --- |
| `build-with-notes` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `change-blueprint` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `concept-lab` | 4/4 | 2/2 | f229: cache boundary + sidecarless long behavior | **PASS** |
| `deepen-the-codebase` | 4/4 | 2/2 | f229: both triggers + two boundaries; b10: green-baseline STOP | **PASS** |
| `do-i-understand-this` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `draw-it-in-svg` | 4/4 | 2/2 | f229: sidecarless long behavior; c24: missing-explanation STOP | **PASS** |
| `draw-the-flow` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `feature-xray` | 4/4 | 2/2 | f229: retry-architecture boundary | **PASS** |
| `feel-the-flow` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `find-the-cause` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `interface-directions` | 4/4 | 2/2 | f229: database-schema boundary | **PASS** |
| `learning-workbench` | 4/4 | 2/2 | f229: post-PR quiz boundary | **PASS** |
| `make-me-realize` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `three-code-paths` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |
| `what-just-happened` | 4/4 | 2/2 | Base matrix authoritative | **PASS** |

## Collision results

| Pair | Expected owner | Observed owner | Verdict |
| --- | --- | --- | --- |
| `make-me-realize` vs `change-blueprint` | `make-me-realize` | `make-me-realize` | **PASS** |
| `three-code-paths` vs `interface-directions` | `three-code-paths` | `three-code-paths` | **PASS** |
| `feel-the-flow` vs `build-with-notes` | `feel-the-flow` | `feel-the-flow` | **PASS** |
| `feature-xray` vs `concept-lab` | `feature-xray` | `feature-xray` | **PASS** |
| `what-just-happened` vs `find-the-cause` | `what-just-happened` | `what-just-happened` | **PASS** |
| `deepen-the-codebase` vs `build-with-notes` | `deepen-the-codebase` | `deepen-the-codebase` | **PASS** |
| `draw-the-flow` vs `draw-it-in-svg` | `draw-the-flow` | `draw-the-flow` | **PASS** |

All seven losing skills remained inactive in their collision case.

## Sidecar independence

- `without-sidecars/` removes `agents/openai.yaml` while keeping the portable skill bundle unchanged.
- One trigger and one adjacent non-trigger per skill were repeated from this variant: **30/30 PASS**.
- Positive cases selected the same intended skill; adjacent cases preserved the same routing boundary.
- The four portable behaviors that initially needed more time were rerun in fresh corrected-revision copies; all reached their required artifact or gate.
- Codex therefore did not require presentation sidecars for activation or portable behavior in the assigned sample.

## Corrected boundaries

| Prompt boundary | Authoritative observation | Verdict |
| --- | --- | --- |
| Caching implementation vs general concept | `feature-xray` | **PASS** |
| Immediate refactor vs architecture analysis | `build-with-notes` | **PASS** |
| Failing test vs architecture analysis | `find-the-cause`; final revision stopped honestly because the baseline stayed green | **PASS** |
| New retry architecture vs feature explanation | `three-code-paths` | **PASS** |
| Database schemas vs visual interface directions | `three-code-paths` | **PASS** |
| Post-PR quiz vs long-term learning | `do-i-understand-this` | **PASS** |
| Standalone SVG request without its source explanation | `draw-it-in-svg`; final revision requested the missing explanation and did not fabricate a diagram | **PASS** |

## Discarded setup evidence

- A preliminary invocation used the real `HOME` and exposed a personal skill despite `--ignore-user-config`. It was invalidated; every counted run used a fresh empty `HOME`.
- An early parser treated paths printed by `find`/`rg` as skill reads. It was replaced with event-level parsing of concrete `command_execution.item.command` values; affected partial observations were discarded and rerun.
- Permission-denied or unauthenticated dry-run observations were treated as invalid setup, never as skill failures.
- Raw evidence preserves these corrections separately; none contributes to the verdict.

## Defects and supersession

- Product/skill defects found in the final authoritative activation scope: none.
- Superseded evidence: the targeted 74a/f229 observations listed in the revision table above.
- Remaining activation rerun required: no.

## Scope not covered by this record

- Six-stage core-cycle execution from `SCENARIO.md`.
- Browser and interaction matrix.
- Keyboard, zoom, reduced-motion, print, VoiceOver, and NVDA accessibility passes.
- Human visual-quality review.

These are separate evaluator-runbook phases; this activation PASS does not assert their completion.

## Reviewer verdict

**Verdict: PASS for Codex client activation, routing, collisions, and required sidecar-independence scope.**

The evidence is suitable for integration with the separate core-cycle, browser, accessibility, and human-evaluation records.

## Evidence locations

- Consolidated structured evidence: `/tmp/acta-codex-consolidated-results.json`
- Full raw-oriented evidence: `/tmp/acta-codex-full-activation.md`
- Long-behavior supplement: `/tmp/acta-codex-f22954b-long-behavior.md`
- Final SVG supplement: `/tmp/acta-codex-c24c366-svg.md`
- Raw JSONL and disposable copies: `/tmp/acta-codex-full-logs/`

