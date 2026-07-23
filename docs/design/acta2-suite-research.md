# Acta v2 suite generalization — upstream research matrix

Date: 2026-07-23 · Live site: https://thariqs.github.io/html-effectiveness/ (index + `unknowns/` verified by fetch; every reference below returned its expected title and was screenshotted at 1440px into `acta-v2-pilot-evaluation/research/upstream/`).

Depth legend — **studied**: full visual read completed; **captured**: screenshot archived, deep read scheduled at the owning cohort's start.

| Acta skill | Cognitive job | Closest upstream peer(s) | Reference URL(s) | What works visually | What to adapt | What not to copy |
|---|---|---|---|---|---|---|
| interface-directions | react to genuinely different UI directions and choose one | 02 visual designs (studied) + unknowns/03 design directions (studied) | /02-exploration-visual-designs.html · /unknowns/03-design-directions.html | Same-data-different-philosophy framing; per-direction thesis line ("this direction says…"); browser-chrome frames around genuinely rendered mockups; critique caption under each stage; A–D label tabs | Full-width stacked directions, each rendering the *identical* scenario dataset; thesis + honest tradeoffs; equal fidelity; selection gate + comparison matrix (tcp-style decision layer) | Steal/skip chip gimmick as the decision model (ours is select-a-direction + rationale); fake URL text; upstream palette |
| change-blueprint | review a specification (Gate A) then an implementation plan (Gate B) before any code | 16 implementation plan (studied) + unknowns/08 implementation plan (captured) | /16-implementation-plan.html · /unknowns/08-implementation-plan.html | Fact strip of real key-values (effort, surfaces, flag); numbered section chips; milestone timeline with dots + package chips; data-flow node diagram with encoded edge meanings and a single dark persistence node; mockup stages; risk table | Two instruments from one generator: Gate A (scope/non-goals/acceptance criteria) and Gate B (slices timeline, data-flow diagram, risky code island, risks, tests, rollout/rollback) each ending in an approve/request-changes gate | Cramming both gates into one moment; invented metrics; upstream content |
| do-i-understand-this | verify one's own understanding of a completed change | unknowns/11 change quiz (studied) | /unknowns/11-change-quiz.html | Mental model rendered *before* questions (before/after mini-flows, new nodes accented); WHAT/WHY/WHERE evidence cards with file:line chips; diff-stat cards; live score chip | Model-first composition; evidence-grounded questions with reveal + explanation; score + gap export; per-gap record | "Quiz you must pass" merge-gate framing — ours is diagnostic and never a gate |
| feature-xray | understand how an existing feature actually works | 14 feature explainer (captured) + 04 code understanding (captured) | /14-research-feature-explainer.html · /04-code-understanding.html | System map + operational flow + evidence-located claims | Durable record: system map, flow, evidence locations (file:line chips), gotchas/FAQ | Any interactive control — nothing here changes with human action; record-only |
| what-just-happened | reconstruct an incident into an evidence-backed postmortem | 12 incident report (captured) | /12-incident-report.html | Impact stat strip; phased timeline; clear epistemic separation | Durable record: impact, phased timeline with fact/hypothesis/mitigation typing, contributing conditions, recovery | Fake active-incident controls, invented owners; record-only |
| draw-the-flow | see how a process moves, including failure/recovery | 13 flowchart diagram (captured) | /13-flowchart-diagram.html | Overview-first flow; encoded path kinds | Instrument: SVG flow with normal/decision/failure/recovery path focus (ephemeral view state) + accuracy gate (confirm / needs-correction); record with full textual equivalent | Decorative arrows without meaning; view state leaking into exports |
| draw-it-in-svg | approve authored, reusable figures | 10 SVG illustrations (captured) | /10-svg-illustrations.html | Authored figure sheet, per-figure identity | Instrument: per-figure verdict checklist (approve/revise) + copyable source; record = accepted figure sheet; every SVG carries title/desc | Generic boxes-and-arrows styling; single global "looks good" button |
| feel-the-flow | feel a behavior before committing to build it | 08 prototype interaction (captured) + 07 prototype animation (captured) | /08-prototype-interaction.html · /07-prototype-animation.html | Live manipulable prototype with felt parameters | Model-kind instrument: parameter bench + live behavioral consequence + felt conclusion; candidate export only | A durable record — the prototype is deliberately disposable (documented) |
| deepen-the-codebase | compare architecture/seam directions without refactoring | 01 code approaches (studied, tcp peer) + 16 implementation plan (studied) | /01-exploration-code-approaches.html · /16-implementation-plan.html | Equal-fidelity approach comparison; module/dependency diagrams | Decision instrument: current module map + N seam directions with dependency-direction diagrams and evidence; chosen direction exports a change-blueprint seed | Any implementation; code-level fidelity that belongs to three-code-paths |
| find-the-cause | falsify hypotheses until a diagnosis survives | 12 incident report (captured) + 13 flowchart (captured) | /12-incident-report.html · /13-flowchart-diagram.html | Evidence timeline; causal-path encoding | Checklist-kind hypothesis board: suspected/falsified/validated verdicts per hypothesis, evidence links, causal map, diagnosis conclusion; record when evidence suffices | Pretending elimination is automatic; auto-validating hypotheses |
| learning-workbench | maintain a durable learning workspace | 15 concept explainer (studied, clab peer) + unknowns/11 change quiz (studied) + unknowns/02 color-grading explainer (captured) | /15-research-concept-explainer.html · /unknowns/11-change-quiz.html · /unknowns/02-color-grading-explainer.html | Glossary rail; model card; quiz with score | Lesson workspace: mission header, waypoint nav, lesson sections, inspectable model figure, retrieval-practice quiz (quiz kind), durable learning record | One-off explainer framing (workbench is multi-session); merge-gate quiz framing |

No-direct-peer notes: `learning-workbench` and `find-the-cause` have no single upstream peer; both derive original topologies from the referenced combinations. `make-me-realize` stays text-only (no HTML artifact) by design.

Role decisions (all fifteen):

| Skill | Role |
|---|---|
| three-code-paths | Instrument + Record (pilot, approved) |
| build-with-notes | Instrument + Record (pilot, approved) |
| concept-lab | Instrument + Record (pilot, approved) |
| make-me-realize | Text-only (no HTML) |
| interface-directions | Instrument + Record |
| change-blueprint | Two instruments (Gate A spec, Gate B plan) + Record |
| do-i-understand-this | Instrument + Record (gaps) — never a merge gate |
| feel-the-flow | Instrument only (disposable prototype; no durable record by design) |
| feature-xray | Record only (no meaningful human action inside the page) |
| what-just-happened | Record only (no fake active-incident controls) |
| draw-the-flow | Instrument (path focus + accuracy gate) + Record |
| draw-it-in-svg | Instrument (per-figure verdicts) + Record |
| deepen-the-codebase | Instrument + Record (exports change-blueprint seed) |
| find-the-cause | Instrument + Record (diagnosis) |
| learning-workbench | Instrument + Record (learning state) |

State-machine kinds: existing `decision` (interface-directions, deepen-the-codebase, change-blueprint gates, draw-the-flow accuracy gate), existing `model` (feel-the-flow), new `quiz` (do-i-understand-this, learning-workbench retrieval), new `checklist` (draw-it-in-svg figures, find-the-cause hypotheses). Record-only skills add no working state.
