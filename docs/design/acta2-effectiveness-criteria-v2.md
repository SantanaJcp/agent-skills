# Acta effectiveness criteria v2

**Purpose:** evaluate whether an artifact helps a human understand, compare, decide, manipulate, monitor, or verify—not merely whether it is valid, safe HTML.

**Scope:** proposed rubric only. This audit does not implement it.

## Evaluation model

Use two separate gate sets:

1. **Technical integrity gates** protect portability, safety, accessibility, print, provenance, and durable state.
2. **Cognitive-effectiveness gates** test the artifact against its declared human question and cognitive action.

Do not average the sets into one score. A beautiful but unsafe artifact fails; a safe artifact that does not help the human perform the task also fails. Some criteria are conditional—for example, a static incident record does not need sliders, and a simple text realization should not be forced into HTML.

## Required preflight: the instrument brief

Before evaluation, the producing skill declares:

| Field | Required answer |
|---|---|
| Human question | The one primary question this artifact helps answer |
| Cognitive action | Compare, trace, locate, simulate, tune, prioritize, monitor, or verify |
| Primary representation | The visual/spatial/interactive structure chosen for that action |
| Relationships to externalize | Alternatives, dependencies, sequence, causality, ownership, state, risk, etc. |
| Human action | What the user inspects, changes, selects, filters, or answers |
| Consequence | What becomes visible or changes after the action |
| First-viewport job | What must be understood before scrolling |
| Durable closure | None, Markdown, JSON, diff, SVG, or prompt; candidate vs accepted state |
| No-JS equivalent | Native disclosure, static states, text map, print view, or a stated limitation |

**Preflight pass:** the representation directly serves the cognitive action. If the only answer is “render the Markdown attractively,” use Markdown unless a durable read/review view has a justified audience.

---

# Part I — Technical integrity gates

These preserve Acta’s genuine advances. Most are binary release gates.

| Criterion | Why it matters | How to test | Pass condition | Likely failure pattern | Review mode |
|---|---|---|---|---|---|
| **T1 Offline and portable** | Artifacts must work when copied, installed, or opened from `file://`. | Open with network disabled; inspect requests; move the file with its declared local evidence assets. | No required network request, build step, CDN, webfont, or sibling-skill dependency. | The page silently loses a library, font, image, or runtime when offline. | Automated + manual |
| **T2 Safe DOM and untrusted content** | Repo text, logs, prompts, and tickets are hostile inputs. | Static sink scan plus generated hostile-string fixture. | Dynamic content uses safe node/text APIs; no inline handlers, `eval`, document writes, or markup injection. | A code snippet or ticket title becomes executable HTML. | Automated + security review |
| **T3 Keyboard and semantic controls** | The task must not require a pointer or color perception. | Tab/Shift-Tab/Enter/Space/arrow pass; accessibility-tree inspection. | Every action is reachable, named, stateful, and has visible focus; no drag-only action. | Clickable SVG groups, fake buttons, missing labels, or trapped focus. | Automated where possible + manual |
| **T4 No-JS important-content access** | Offline or restricted environments still need the record and decisions. | Disable JS and perform the declared task’s read-only equivalent. | All important facts, alternatives, decision state, and textual equivalents remain reachable. They need not all be open simultaneously. | CSS tabs hide alternate panes; quiz questions disappear; “no-JS” is interpreted as “everything expanded.” | Manual + DOM assertions |
| **T5 Responsive reflow and zoom** | Visual instruments must survive narrow and magnified contexts. | 320/390 CSS px, 400% zoom, landscape/portrait; measure document overflow. | No document-level horizontal scroll; local graph/code/table scrolling is labeled and preserves context; no clipping or overlap. | Fixed-width SVG/table/code expands the page or shrinks text to illegibility. | Automated screenshots/metrics + manual |
| **T6 Print and durable review** | Records, evidence, and decisions may need archival review. | Print preview/PDF in color and grayscale. | Controls are replaced by their state; details needed for the record are expanded; provenance/sources print; semantics survive monochrome. | Empty controls, clipped figures, color-only status, or missing URLs. | Automated smoke + manual |
| **T7 Reduced motion** | Motion cannot be required or harmful. | Emulate `prefers-reduced-motion`; inspect animations/transitions. | Essential meaning and state change remain; motion is removed or reduced. | Model state is conveyed only through animation. | Automated + manual |
| **T8 Provenance integrity** | A durable claim needs scope, revision, inputs, and staleness. | Compare artifact metadata to the producing run and source files. | Provenance is complete and accurate in export/print; its screen placement may be compact. | “Not available” when a SHA exists; stale input list; provenance consumes space without trust value. | Automated + manual |
| **T9 Epistemic integrity** | Facts, inferences, and simplifications must not blur. | Sample every load-bearing claim and trace its source/label. | Claims are supported and labels resolve; diagrams distinguish pedagogical simplification from production behavior. | Decorative labels without evidence, or unlabeled invented transitions. | Manual + link/reference checks |
| **T10 Durable export and acceptance** | The human-agent loop depends on reliable return state. | Change/choose/answer in HTML; export; parse; compare with visible state and accepted record. | Export is complete, parseable, and semantically equal to visible working state; accepted canonical state changes only after an explicit acceptance step. | Stale hidden payload, visible “approved” but exported “awaiting,” or implied automatic file synchronization. | Automated semantic test + manual |
| **T11 Honest degradation** | A missing capability should not masquerade as success. | Deny clipboard, JS, and optional runtime capability. | The artifact reports the limitation and gives a usable fallback; it does not claim persistence. | “Copied” when clipboard failed; controls appear active but do nothing. | Automated fault injection + manual |
| **T12 Source/asset durability** | Evidence links must remain useful after relocation. | Move/open the audit bundle; test local paths and printed URLs. | Required evidence remains available or is clearly identified as external/source-relative. | Broken absolute temp links or omitted screenshot/source identity. | Automated link check + manual |

---

# Part II — Cognitive-effectiveness gates

## C1 First-viewport orientation

- **Why it matters:** The first screen establishes the question, current state, and expected human action. If it shows only system identity, the artifact feels like a document wrapper.
- **How to test:** Cold-open at the target desktop and mobile sizes. Ask the evaluator, without scrolling: “What is this?”, “What am I meant to understand or decide?”, and “What should I do next?” Record visible regions and target Y positions.
- **Pass condition:** The evaluator answers accurately, and at least the overview or first meaningful part of the task-specific instrument is visible. Full provenance may be accessible without dominating.
- **Likely failure:** Provenance + title + prompt + summary + TOC fill the viewport; the instrument starts around Y=900.
- **Mode:** Manual, supported by automated viewport screenshots/element positions.

## C2 30-second scan comprehension

- **Why it matters:** Effective HTML should improve rapid orientation, not merely reward exhaustive reading.
- **How to test:** Give a first-time representative user 30 seconds, then hide the artifact and ask three task-specific questions: purpose, main model/alternatives, and current decision/risk/next action. Predefine correct answers from the instrument brief.
- **Pass condition:** The user answers the critical questions correctly without relying on prose memory outside the artifact. Record errors, not only time.
- **Likely failure:** The user remembers the recommendation/status badge but cannot explain alternatives, causal flow, or why.
- **Mode:** Manual user test. Automated checks cannot prove comprehension.

## C3 Decision latency

- **Why it matters:** A comparison or gate exists to help a human reach a justified decision.
- **How to test:** From cold open, time until the evaluator can identify a preferred option *and cite the decisive dimension*. Compare with the current artifact or canonical Markdown baseline using the same scenario. For non-decision artifacts, use “time to identify the next action/critical risk.”
- **Pass condition:** The artifact meets a scenario-specific target declared before testing or materially improves the baseline without reducing correctness/confidence.
- **Likely failure:** The recommendation is immediate but evidence comes many screens later, creating fast acquiescence rather than fast judgment.
- **Mode:** Manual comparative test.

**Why no universal seconds quota:** complexity, reader expertise, and consequence vary. A five-second security decision may be reckless; a 90-second microcopy choice may be excessive. Define the target per task and compare against a baseline.

## C4 Visual compression

- **Why it matters:** The point of structure is to reduce serial reading and working-memory demand while preserving important distinctions.
- **How to test:** Identify the facts/relations the user must hold simultaneously. Verify that alignment, grouping, sequence, or graphical mapping makes them inspectable in one region. Compare how many page transitions or cross-references are required.
- **Pass condition:** The representation lets the user perceive a relevant pattern or relation that would otherwise require remembering multiple paragraphs.
- **Likely failure:** Cards merely surround prose; every option repeats the same headings vertically; the “visual” adds area without reducing memory load.
- **Mode:** Manual expert review, supported by DOM/layout metrics.

## C5 Prose-to-structure balance

- **Why it matters:** Prose explains nuance; structure supports scanning and relations. Either can be overused.
- **How to test:** For each paragraph, ask whether it introduces nuance/evidence or restates what the structure could show. For each table/card/diagram, ask whether it changes comprehension or only decorates text.
- **Pass condition:** Prose carries interpretation and caveats; structure carries comparison, sequence, state, dependency, or consequence. Repeated narration is removed or disclosed.
- **Likely failure:** A table repeats the preceding paragraphs, or a diagram is followed by a complete prose duplicate with both open.
- **Mode:** Manual.

**Why no universal word ratio:** a legal incident record may need dense prose; a visual exploration may need very little. Judge redundancy and cognitive role, not a fixed percentage.

## C6 Semantic visual encoding

- **Why it matters:** Visual elements should encode domain meaning, not add “visual interest.”
- **How to test:** Inventory every non-text visual variable—position, line, shape, color, size, enclosure, motion. Name the domain variable it represents and verify a legend/text equivalent where needed.
- **Pass condition:** Every major visual mark has a cognitive job; semantics survive grayscale and are not contradicted by prose.
- **Likely failure:** Icons, colored cards, or decorative graphs with no mapping; one accent color means brand, warning, and selection.
- **Mode:** Manual + contrast/monochrome automation.

## C7 Spatial representation of relationships

- **Why it matters:** Dependencies, causality, sequence, hierarchy, and before/after change are difficult to reconstruct from paragraphs.
- **How to test:** From the artifact alone, ask the evaluator to trace one normal path, one failure/alternative path, and one dependency/change. Compare answers to source evidence.
- **Pass condition:** Relevant relations are visible in adjacency, alignment, connection, or a semantic table; the user does not need to search multiple sections.
- **Likely failure:** A `<pre>` arrow diagram is clipped or relationships are embedded in sentence order only.
- **Mode:** Manual + structural checks for required task types.

## C8 Task-specificity

- **Why it matters:** A purpose-built artifact should look and behave like its job, not like every other report.
- **How to test:** Remove title/skill labels and show first viewports from several families. Ask evaluators to identify which is compare, monitor, explain, simulate, or quiz and what action is possible.
- **Pass condition:** Family/cognitive action is inferable from topology and affordances, not only labels.
- **Likely failure:** All pages begin with the same provenance/title/prompt/summary stack and differ below the fold.
- **Mode:** Manual blind review, supported by screenshot similarity/layout metrics.

## C9 Interaction usefulness

- **Why it matters:** Interaction is justified only when it helps answer the question, change the model, focus attention, or produce a decision.
- **How to test:** Perform every control action and state: (a) what input changed, (b) what consequence became visible, (c) what the user learned or decided, and (d) what exports.
- **Pass condition:** Each primary interaction has an observable, task-relevant consequence. Static artifacts pass when interaction would add no value.
- **Likely failure:** Disabled demo controls, theme switches presented as core work, copy as the only interaction in a decision artifact, or sliders with no explanatory consequence.
- **Mode:** Manual + automated behavior/state assertions.

**Why no universal interaction requirement:** reports, incidents, and simple figures can be more effective when static. Interaction is a means, not a score booster.

## C10 Progressive disclosure

- **Why it matters:** Complete information need not compete for attention simultaneously.
- **How to test:** Classify content as overview, active decision, evidence for an open decision, reference detail, or archive. Inspect default open/closed state with JS on/off and in print.
- **Pass condition:** Active warnings/gates and the primary model are visible; secondary mechanics/evidence are reachable; print can expand the record.
- **Likely failure:** Everything is open because “no-JS readable,” or critical risk is hidden because it is long.
- **Mode:** Manual + DOM/default-state assertions.

## C11 Overview before detail

- **Why it matters:** The reader needs a stable mental model before local facts.
- **How to test:** Ask the evaluator to explain the whole system/change before opening details. Verify that the overview is accurate and links to detail.
- **Pass condition:** A compact model/status/summary answers what/why/current state and locates major parts; detail refines rather than replaces it.
- **Likely failure:** A prose summary states the recommendation but not the option space or causal model.
- **Mode:** Manual.

## C12 Comparison fidelity

- **Why it matters:** Unequal detail or different scenarios biases decisions.
- **How to test:** Check each option against the same declared dimensions, scenario/data, scale, viewport, code depth, responsive states, and known caveats. Temporarily hide option names/recommendation and ask whether any is privileged by presentation.
- **Pass condition:** Differences arise from the options, not fidelity. Recommendation appears after or separate from the comparison.
- **Likely failure:** Path A has code while B/C have paragraphs; B/C duplicate; one mockup is larger; summary recommends A before inspection.
- **Mode:** Automated schema/content-shape checks + manual visual review.

## C13 Human-in-the-loop engagement

- **Why it matters:** The method’s goal is active review of agent choices.
- **How to test:** During a realistic task, record whether the human challenges an assumption, explores an alternative, changes a parameter, selects a path, or identifies a gap *through the artifact*. Compare with a terminal/Markdown run.
- **Pass condition:** The artifact creates at least one meaningful inspection or intervention opportunity appropriate to the task, or explicitly justifies why the artifact is a read-only record.
- **Likely failure:** The human only scrolls to an agent recommendation and says yes in chat.
- **Mode:** Manual workflow observation.

## C14 State-to-export closure

- **Why it matters:** Interaction that does not return accurately to the agent is a dead end or a hazard.
- **How to test:** Set a non-default state, export, parse, reload/re-import when supported, and compare every visible choice/status/gap/parameter. Then accept into canonical state and compare revisions.
- **Pass condition:** Working state = candidate export; accepted record changes only after explicit acceptance; discrepancies are visible and intentional.
- **Likely failure:** Static hidden export payload, empty `decisions`, old gate status, missing annotations, or copy-only success message without persisted change.
- **Mode:** Automated semantic round-trip + manual acceptance check.

## C15 Accessibility without flattening

- **Why it matters:** Accessibility is not equivalent to converting every visual into always-visible prose.
- **How to test:** Keyboard and screen-reader pass plus a sighted scan test. Confirm semantic structure, textual equivalents, native disclosure, announced state changes, and non-redundant reading order.
- **Pass condition:** Assistive-technology users can perform the same cognitive task; sighted users retain spatial compression; neither is forced through duplicated content.
- **Likely failure:** Huge repeated `aria-label`/visible prose, controls without relationships, or diagrams removed instead of made accessible.
- **Mode:** Manual AT review + automated semantics.

## C16 Visual distinction between artifact families

- **Why it matters:** Topology should signal whether the user is reading, comparing, exploring, or operating.
- **How to test:** Blind first-viewport sorting and interaction inventory across realistic fixtures.
- **Pass condition:** Compare artifacts foreground alternatives; Explore foregrounds model/controls; Edit foregrounds current state/action; Document foregrounds overview/evidence. Shared brand tokens do not erase topology.
- **Likely failure:** Family is known only from an eyebrow label.
- **Mode:** Manual + screenshot/layout analysis.

## C17 Risk noticeability

- **Why it matters:** Users must detect blocking uncertainty and operational danger quickly.
- **How to test:** Seed known critical/medium risks and ask evaluators to locate and rank them during the 30-second scan. Test grayscale and screen reader.
- **Pass condition:** Blocking risk is prominent through position, label, and shape—not color alone—and linked to mitigation/decision.
- **Likely failure:** Risk is one paragraph in a long section or every metadata badge has equal visual weight.
- **Mode:** Manual + structural assertions.

## C18 Monitoring usefulness

- **Why it matters:** Live implementation/incident artifacts must answer “now, next, blocked, changed.”
- **How to test:** Give a mixed event log and ask for current status, latest failure, deviations, human decisions, and next action. Exercise filters.
- **Pass condition:** These answers are visible or obtainable in one action without scanning the entire log.
- **Likely failure:** Beautiful chronological archive with no attention view.
- **Mode:** Manual + behavior tests.

---

# Conditional requirements by cognitive action

| Cognitive action | Normally required | Harmful when forced |
|---|---|---|
| Compare | Equal-fidelity aligned views, shared dimensions, recommendation after comparison | Three options are trivial or only one is feasible; a fake comparison wastes attention |
| Trace | Whole path, branch/failure/recovery, linked evidence | The process is strictly linear and already obvious in a short list |
| Simulate/tune | Controls, consequence, reset/default, export | No meaningful parameter or derived behavior exists |
| Monitor | Current state, typed events, filters, “needs human,” next action | The record is closed and has no changing state |
| Verify understanding | Mental model, diagnostic questions, feedback, gap export | The content is simple recall or no real change evidence exists |
| Durable record | Complete provenance/evidence/print | Used as the opening topology for an active, rapidly changing workspace |

## Word, viewport, diagram, and interaction guidance

- **Word limits:** do not set a universal quota. Apply a *redundancy test*: if a paragraph merely narrates a visible structure, collapse or disclose it. Use a scenario-specific reading budget for the primary path.
- **Viewport budget:** do not require an entire complex artifact above the fold. Require first-viewport orientation plus the overview or beginning of the instrument. Record target Y and page-downs.
- **Diagram requirement:** require a diagram when spatial relations are load-bearing and prose would make the reader reconstruct them. Do not require diagrams for decoration or strictly linear/simple content.
- **Interaction requirement:** require it only when changing/selecting/filtering/answering improves the task. A static aligned comparison can be more effective than a gratuitous control panel.
- **Progressive disclosure:** preserve availability, not simultaneous visibility. Critical warnings/gates remain open; reference evidence can fold; print can expand.

---

# Release protocol

1. **Pass all applicable technical integrity gates.** T10 state/export mismatch is always blocking.
2. **Pass C1, C2, C8, C11, C14, and C15** for every HTML artifact family fixture.
3. Pass action-specific gates: C12 for Compare; C9 for interactive Explore/Edit; C17 for risk/gate artifacts; C18 for monitoring artifacts.
4. Use at least one realistic, non-placeholder fixture per skill. Component sheets do not substitute for task fixtures.
5. Record evaluator answers, time, errors, screenshots, and exported payload—not only PASS/FAIL.
6. A failed cognitive gate returns to **method/representation selection first**, not immediately to CSS polish.

## Minimum evidence bundle per realistic fixture

- Instrument brief.
- Desktop/mobile first-viewport screenshots.
- Full-page topology capture.
- 30-second comprehension answers from at least one target evaluator during development; more for release confidence.
- Keyboard/no-JS/print results.
- Visible-state vs export semantic comparison.
- One sentence explaining the cognitive job of every major visual structure and interaction.

