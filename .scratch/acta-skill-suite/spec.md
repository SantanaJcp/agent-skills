# Spec: Acta Development Skill Suite

Status: ready-for-agent

## Problem Statement

The repository is a portable Agent Skills publisher with mature authoring, validation, catalog, installation, and release foundations, but it does not yet contain the development skills it exists to publish. The maintainer currently assembles a development cycle from personal skills and separate HTML-effectiveness patterns. Those pieces do not share an artifact protocol, visual language, state model, handoff contract, testing model, or public distribution story.

This fragmentation creates several recurring problems. Discovery and requirement clarification happen in conversation without a durable map of facts, decisions, and unknowns. Alternative approaches are difficult to compare at equal fidelity. Specifications, implementation plans, live implementation notes, and post-change understanding checks do not form one coherent chain. Visual HTML artifacts can make complex work easier to understand, but ad hoc HTML is inconsistent, may require network access, can lose state, and may not survive printing, accessibility review, or installation into both Codex and Claude Code. The existing personal skills also contain runtime-specific assumptions, external-skill dependencies, CDN usage, and mutation behavior that cannot be published unchanged under this repository's portable-core promise.

The maintainer needs one public product that matches the workflow they will personally use. It should install as a complete bundle, remain composed of clear independently discoverable skills, support automatic and explicit invocation, work from the same portable source in current Codex and Claude Code, and give every stage a predictable contract. The product must preserve human control: HTML may help people inspect and choose, but canonical state must remain explicit, text-based, reviewable, and publishable only after a human decision.

## Solution

Build a bundle-first portable suite of exactly fifteen Agent Skills, backed by the Acta design system and a shared artifact protocol. Six core skills form an advisory development cycle: reveal blind spots, compare three code paths, conditionally explore interface directions, create a two-gate change blueprint, implement with live notes, and diagnose the user's understanding after the change. Nine autonomous tools support prototyping, explanation, research, incidents, diagrams, architecture analysis, debugging, and long-lived learning.

The skills will remain separate Agent Skill directories so each has a focused trigger description, progressive disclosure, and a bounded process. The public installation experience will recommend installing all fifteen together, while generated self-contained resources preserve the ability to install and execute one skill alone. No router skill will be added, and no skill will silently advance the user to another stage. Each skill may recommend a next skill and export a compatible seed, but the human chooses the transition.

Acta will provide a consistent offline, print-first engineering-record shell for fourteen HTML-producing skills. `make-me-realize` will deliberately remain conversational and text-only. The publisher will own one canonical Acta source and materialize the common protocol and recipe-specific, fully inline HTML scaffolds into each installed skill. Runtime execution will not require a renderer, watcher, server, package installation, sibling skill, repository-root file, or network connection. The agent will use the installed scaffold as a structural contract and produce a self-contained HTML view from the same Markdown/JSON state it presents for export.

Working state will live under a locally excluded `.agent-work/<initiative>/<skill>/` workspace. Markdown with minimal YAML frontmatter will be canonical; JSON will exist only for genuinely structured state; HTML will be a regenerable human interface. Browser state will be ephemeral. Decisions may return through unambiguous natural language or an exported Markdown/JSON record. Publishing to a project tracker or durable project document will always require an explicit request and will follow the consuming project's documented rules.

All fifteen skills will begin in the incubator and will be promoted together only after deterministic repository checks, individual trigger/non-trigger trials in current Codex and Claude Code, a complete six-skill end-to-end scenario in both clients, and the agreed manual HTML quality matrix. Promotion will prepare the repository for `v1.0.0`, but release dispatch, tagging, and public release verification will remain a separate human action.

## User Stories

1. As the maintainer, I want one public product to represent the workflow I personally use, so that personal and public behavior do not drift into separate profiles.
2. As a new consumer, I want one recommended command to install the complete collection, so that I do not need to understand the dependency map before beginning.
3. As an advanced consumer, I want each skill to remain installable and usable alone, so that I can adopt only the capability I need.
4. As a Codex user, I want the same portable skill instructions used by Claude Code, so that behavior does not split by client.
5. As a Claude Code user, I want the same portable skill instructions used by Codex, so that fixes and improvements have one source.
6. As a consumer, I want every skill to support automatic activation and explicit invocation, so that I can rely on discovery without losing direct control.
7. As a consumer, I want concise, non-overlapping trigger descriptions, so that installing the whole bundle does not cause constant accidental activation.
8. As a consumer, I want every skill to remain autonomous, so that invoking one never fails because a sibling skill was not installed.
9. As the maintainer, I want exactly fifteen public skills in the initial suite, so that the product surface remains deliberate and testable.
10. As the maintainer, I do not want a sixteenth router skill, so that stage selection remains transparent rather than hidden inside orchestration.
11. As a user, I want a completed skill to recommend useful next steps without invoking them automatically, so that I decide when the workflow advances.
12. As a user with a vague idea, I want `make-me-realize` to find facts itself and expose the remaining decisions, so that I am not asked questions the agent could answer from the environment.
13. As a user, I want `make-me-realize` to combine a blind-spot pass with frontier-based grilling, so that every currently answerable decision is asked in coherent rounds.
14. As a user, I want unknowns assigned to an owner or answered before realization ends, so that uncertainty is explicit rather than silently assumed.
15. As a user, I want `make-me-realize` to remain text-only, so that HTML is not forced onto a conversation whose main value is clarification.
16. As an engineer evaluating an implementation, I want `three-code-paths` to present exactly three structurally different approaches, so that I compare real decisions rather than cosmetic variants.
17. As an engineer, I want each code path to explain the distinct question it answers, so that diversity is contextual rather than mechanically labeled minimal, balanced, and ambitious.
18. As an engineer, I want representative interfaces, snippets, or diffs for each path, so that the comparison is concrete enough to choose.
19. As an engineer facing irreducible uncertainty, I want `three-code-paths` to create an optional disposable prototype, so that the choice can be informed by evidence without beginning production implementation.
20. As a decision maker, I want all three paths shown at equal fidelity before the recommendation, so that presentation bias does not preselect an option.
21. As a decision maker, I want the chosen path recorded through a DecisionGate, so that downstream planning receives an explicit selection.
22. As a product developer, I want `interface-directions` used conditionally when a change includes a visual or interaction decision, so that backend and documentation work are not forced through UI exploration.
23. As a product developer, I want interface directions to differ in layout, density, hierarchy, tone, and behavior, so that the candidates are meaningfully distinct.
24. As a product developer, I want Acta to frame the comparison without styling the product candidates themselves, so that the report remains coherent while each mockup stays honest.
25. As a decision maker, I want `interface-directions` to end at an explicit choice, so that the implementation blueprint does not inherit an unresolved visual direction.
26. As a developer with mostly clarified requirements, I want `change-blueprint` to perform a readiness check and ask only blocking questions, so that it does not repeat an earlier discovery interview.
27. As a developer with broadly ambiguous requirements, I want `change-blueprint` to recommend `make-me-realize`, so that each skill retains a clear responsibility.
28. As a reviewer, I want Gate A to approve a compact specification containing the problem, outcomes, non-goals, decisions, acceptance criteria, and test seams, so that the change contract is complete without mandatory PRD ceremony.
29. As a reviewer, I want user stories included only when they improve clarity, so that every change is not forced into an exhaustive story format.
30. As a reviewer, I want Gate B to approve a separate implementation plan containing slices, data flow, risky code, risks, mitigations, tests, and rollout, so that execution can be reviewed independently from product intent.
31. As a project owner, I want an approved specification publishable before the implementation plan only when I explicitly request it, so that planning can continue without automatic project mutations.
32. As an implementation agent, I want the implementation plan to reference the approved specification revision, so that the two gates remain connected.
33. As a user explicitly requesting implementation, I want `build-with-notes` to treat that request as authorization to modify the repository, so that a redundant start confirmation is unnecessary.
34. As a user without an approved blueprint, I want `build-with-notes` to derive and record a minimal contract from the prompt, ticket, or existing spec, so that the skill remains independently usable.
35. As an engineer, I want `build-with-notes` to work test-first at the agreed seams and run focused checks throughout implementation, so that feedback remains tight.
36. As an engineer, I want implementation notes refreshed after every completed slice, deviation, STOP gate, and important check result, so that the live record reflects the actual work.
37. As an engineer, I do not want a runtime watcher to be required, so that implementation works in both supported clients and constrained environments.
38. As a reviewer, I want architecture, API, data, security, and scope deviations to trigger visible STOP gates, so that the agent does not silently exceed the approved contract.
39. As a reviewer, I want new implementation decisions proposed as updates to specs, ADRs, or tickets and published only after approval, so that durable records remain intentional.
40. As a repository owner, I want commit creation to require separate explicit authorization, so that implementation permission does not imply permission to commit.
41. As an engineer, I want `build-with-notes` to perform its own final diff review against the blueprint and repository rules, so that correctness does not depend on an external review skill.
42. As a user reviewing a completed change, I want `do-i-understand-this` to test causality, limits, failure, rollback, security, and operational understanding, so that the quiz measures comprehension rather than trivia.
43. As a user, I want the quiz grounded in the actual diff, blueprint, and implementation notes, so that questions are specific to the change.
44. As a user, I want understanding gaps exported as Markdown and structured JSON, so that they can guide later learning or review.
45. As a user, I want missed concepts explained briefly with an optional retry, so that diagnosis can improve understanding.
46. As a user, I do not want the quiz to become a merge or completion gate, so that an educational tool does not become process theater.
47. As a designer, I want `feel-the-flow` to create a self-contained HTML prototype first, so that interaction questions can be tested quickly and portably.
48. As a designer facing stack-dependent behavior, I want an optional disposable copy of the real stack, so that necessary fidelity is available without contaminating production work.
49. As a designer, I want every prototype parameter and conclusion exportable to text, so that a throwaway prototype still produces a durable decision.
50. As a maintainer learning an unfamiliar feature, I want `feature-xray` to explain the operational flow with file-and-line evidence, so that claims can be verified in the codebase.
51. As a maintainer, I want feature explanations to label facts, inferences, and gotchas, so that confidence is visible.
52. As a learner, I want `concept-lab` to build a manipulable model from trustworthy sources, so that I can explore consequences rather than only read prose.
53. As a learner, I want pedagogical simplifications labeled separately from production behavior, so that the model does not become misinformation.
54. As an incident participant, I want `what-just-happened` to capture a factual timeline while an incident is active, so that evidence is not lost.
55. As an incident commander, I do not want the reporting skill to direct mitigation, so that documentation does not compete with the response process.
56. As a reviewer, I want the incident report to remain a draft until stabilization, so that cause, impact, owners, and actions are not invented prematurely.
57. As a reviewer, I want every post-incident claim tied to evidence and every unknown owner shown as pending, so that the report is honest.
58. As an engineer explaining a process, I want `draw-the-flow` to show the overview before stage detail, so that the reader gains orientation before complexity.
59. As an engineer, I want normal, decision, failure, and recovery paths represented with a textual equivalent, so that the diagram remains understandable without vision or scripting.
60. As a designer needing vector artwork, I want `draw-it-in-svg` to produce standalone SVG figures with their own title and description, so that each figure remains reusable outside its sheet.
61. As a designer, I want each SVG source copyable from the report, so that reuse does not require extracting markup manually.
62. As an architect, I want `deepen-the-codebase` to find deepening opportunities using domain and module vocabulary, so that recommendations focus on meaningful seams and locality.
63. As an architect, I want the skill to compare candidates with before-and-after evidence and recommendation strength, so that I can choose an architectural direction.
64. As a repository owner, I do not want architecture analysis to refactor code, so that exploration remains separate from authorized implementation.
65. As a planner, I want a selected architecture direction exportable as a `change-blueprint` seed, so that analysis can hand off without automatic execution.
66. As a debugger, I want `find-the-cause` to begin by building a tight red-capable feedback loop, so that diagnosis is evidence-driven.
67. As a debugger, I want hypotheses to be falsifiable and tested one variable at a time, so that the investigation resists anchoring.
68. As a debugger, I want temporary repros, tests, and instrumentation allowed during diagnosis, so that hard bugs can be investigated realistically.
69. As a repository owner, I want temporary diagnostic changes cleaned before completion and production fixes excluded, so that diagnosis remains separate from remediation.
70. As a planner, I want the validated cause and fix direction exportable as a blueprint seed, so that a later implementation starts from evidence.
71. As a learner, I want `learning-workbench` to support any topic for which reliable sources and practice can be found, so that it preserves the breadth of the existing teaching workflow.
72. As a learner, I want a durable workspace chosen by me rather than a temporary `.agent-work` initiative, so that learning can continue across sessions.
73. As a learner, I want mission, resources, lessons, practice, retrieval attempts, and spaced review state preserved in Markdown/JSON, so that future sessions know what I have learned.
74. As a learner, I want every lesson tied to my mission and zone of proximal development, so that study remains relevant and appropriately difficult.
75. As a learner, I want factual teaching grounded in trustworthy sources instead of parametric memory alone, so that the material is reliable.
76. As a user, I want working technical artifacts stored under `.agent-work/<initiative>/<skill>/`, so that parallel skills do not collide.
77. As a user, I want the initiative slug inferred and confirmed once, so that paths are stable without repeated prompts.
78. As a Git user, I want `.agent-work/` added idempotently to the local Git exclude file, so that working artifacts do not modify the project's versioned ignore policy.
79. As a reviewer, I want every canonical artifact to carry the same small frontmatter contract, so that identity, status, inputs, decisions, and supersession are machine-readable.
80. As a reviewer, I want the shared state vocabulary to include draft, awaiting-decision, approved, completed, blocked, and superseded, so that stages communicate consistently.
81. As a user, I want only Markdown and genuinely structured JSON treated as canonical, so that the workflow remains inspectable and portable.
82. As a user, I want HTML views regenerated from canonical state and never allowed to rewrite project files, so that browser interactions cannot silently mutate the source of truth.
83. As a user, I want browser interaction state to remain ephemeral until I export it, so that no hidden localStorage state changes future runs.
84. As a user, I want DecisionGates to accept an unambiguous natural-language choice or an exported Markdown/JSON choice, so that the workflow remains usable with or without the HTML interface.
85. As a user, I want a gate to require the selection but not a rationale, so that simple decisions remain low-friction while optional rationale is still recorded when provided.
86. As a reviewer, I want timestamps used only for events where time is part of the fact, so that incident, session, quiz, and review records retain meaning without making build artifacts nondeterministic.
87. As a reviewer, I want approved Markdown/JSON revisions archived before supersession, so that load-bearing decisions remain auditable.
88. As a user, I do not want historical HTML copies retained, so that views remain regenerable rather than becoming a second archive.
89. As a project owner, I want new instructions that conflict with an approved artifact recorded as explicit supersession, so that the current contract is clear.
90. As an implementation reviewer, I want conflicting instructions during implementation to open a STOP gate, so that scope change is visible before further mutation.
91. As a project owner, I want publishing to follow project instructions and ask for a destination when none is documented, so that skills never invent a canonical tracker or path.
92. As a project owner, I want publishing to require an explicit request, so that approval inside a private workspace does not automatically modify durable project records.
93. As a user, I want a generated HTML view opened when the client can do so and otherwise receive its absolute path, so that inability to launch a browser does not block the skill.
94. As a user without JavaScript, I want every Acta artifact readable and its essential content complete, so that scripting remains progressive enhancement.
95. As a user working offline, I want zero runtime requests, webfonts, CDNs, or external scripts, so that artifacts work from `file://` and remain private.
96. As a keyboard user, I want native controls, visible focus, and no drag-only interaction, so that every decision remains operable.
97. As a print user, I want controls hidden, disclosures expanded, provenance visible, and meaning preserved in monochrome, so that the engineering record survives paper and PDF.
98. As a motion-sensitive user, I want reduced-motion preferences honored and no essential movement, so that the interface remains comfortable.
99. As a security-conscious user, I want dynamic content inserted through safe DOM APIs and secrets omitted from generated artifacts, so that a report does not become an injection or disclosure vector.
100. As the Acta maintainer, I want one canonical `0.1.0` source for tokens, behavior, protocol, components, and recipes, so that installed copies are generated rather than manually synchronized.
101. As the Acta maintainer, I want materialized copies stamped with the Acta version, recipe, and a SHA-256 of canonical inputs, so that freshness is deterministic without dates or circular Git hashes.
102. As a skill consumer, I want the installed protocol and scaffold contained inside every skill that needs them, so that a whole-bundle install is convenient without making sibling layout a runtime dependency.
103. As the maintainer, I want all five Claude design deliverables preserved in the repository as immutable provenance, so that the original research, alternatives, component baseline, spec, and QA remain inspectable.
104. As the maintainer, I want the copied component sheet used as a visual baseline rather than a runtime dependency, so that implementation can be checked against the chosen design without creating two executable sources.
105. As the maintainer, I want the executable Acta source to be authoritative over the copied provenance, so that future maintenance has one place to change behavior.
106. As a contributor, I want `npm run check` to verify materialization freshness, portable structure, HTML safety, protocol shape, catalogs, and installation, so that deterministic failures are caught before review.
107. As a contributor, I want CI to use static analysis rather than downloading headless browsers, so that the public acceptance seam remains smaller and cross-platform.
108. As a reviewer, I want visual validation based on component contracts and measurements rather than pixel screenshots, so that tests resist platform font noise.
109. As a reviewer, I want realistic recipe fixtures kept outside installed skill bundles, so that QA is thorough without bloating consumers.
110. As a reviewer, I want all fourteen recipes manually exercised in current stable Chrome, so that every HTML-producing skill receives direct browser evidence.
111. As a reviewer, I want representative Document, Compare, Explore, and Edit artifacts plus critical interactions checked in current Safari and Firefox, so that shared family behavior is portable across browser engines.
112. As an accessibility reviewer, I want manual keyboard, 400% zoom, VoiceOver, and NVDA evidence before stable promotion, so that the repository does not overclaim from static checks alone.
113. As the maintainer, I want Windows tooling CI to remain required but Windows font rendering not to block promotion, so that an acknowledged visual risk does not stop the initial suite.
114. As a reviewer, I want every skill's trigger and non-trigger cases executed in current Codex and Claude Code, so that automatic activation is evidence-based.
115. As a reviewer, I want a complete core-cycle scenario executed against a public synthetic fixture in both clients, so that handoffs are tested without relying on private repositories.
116. As a reviewer, I want manual versions, prompts, observations, browser results, and accessibility evidence captured in one versioned suite report, so that promotion claims remain auditable.
117. As a consumer, I want Codex presentation sidecars for all fifteen skills, so that the bundle is polished in Codex without changing portable behavior.
118. As a Claude Code user, I want sidecars to remain nonessential, so that ignoring Codex metadata does not change the workflow.
119. As the maintainer, I want all fifteen skills to remain incubating until the complete suite passes its joint gates, so that stable does not expose a partial development cycle.
120. As the release manager, I want successful joint promotion to prepare compatibility records, changelog, and release checks for `v1.0.0`, so that the final release can be dispatched deliberately.
121. As the release manager, I want tag creation and workflow dispatch to remain a separate human action, so that implementation completion does not automatically publish the first release.

## Implementation Decisions

### Product and distribution

- The initial product contains exactly fifteen skills: six core cycle skills and nine autonomous tools. No router, mega-skill, native Codex plugin, or Claude plugin is added.
- Distribution is **bundle-first, standalone-capable**. Documentation leads with installing all fifteen for Codex and Claude Code. Interactive selection and single-skill installation remain supported but secondary.
- Each skill remains a flat, self-contained Agent Skill with a concise model-facing description that supports implicit activation and explicit invocation. Skills never require a sibling skill and never auto-invoke the next stage.
- Public skills, metadata, tests, and documentation are written canonically in English. Generated artifacts use the user's or project's language and record that language in canonical metadata.
- Every skill receives a nonessential Codex sidecar containing a display name, a 25–64-character short description, and a one-sentence default prompt that explicitly names the skill. Sidecars contain no icons, brand colors, MCP dependencies, or behavior required by Claude Code.
- All fifteen skills begin in the incubator. They may be implemented in reviewed slices, but none moves to stable until the entire suite and the complete core cycle have passed the joint acceptance gates.

### Common artifact protocol

- Technical working state uses `.agent-work/<initiative>/<skill>/`. The initiative slug is inferred from an issue, branch, or task name and confirmed once. In Git repositories, `.agent-work/` is added idempotently to `.git/info/exclude`; versioned `.gitignore` is not changed.
- Every skill directory has one or more predictably named canonical Markdown artifacts, optional JSON only for structured state, a current regenerable HTML view when applicable, and a `history/` directory. Learning workspaces are the only exception: they live in a durable user-selected directory.
- Canonical Markdown uses a minimal frontmatter interface: protocol version, artifact kind, producer skill, initiative, shared status, output language, source revision, inputs, decisions, and superseded artifact reference. Time fields are optional and appear only when time is semantically part of an incident, implementation session, quiz attempt, or learning review.
- Shared statuses are `draft`, `awaiting-decision`, `approved`, `completed`, `blocked`, and `superseded`. Skills may add a separate domain-specific phase field without redefining the shared status vocabulary.
- A current canonical file has a stable name. Replacing an approved revision first archives its Markdown and structured JSON under a monotonically increasing revision identifier. HTML is never archived and is regenerated from the current canonical state.
- Browser state is ephemeral and never stored in localStorage. HTML cannot write project files. Markdown export is always available; JSON or diff export is added only when the state is structured. An unambiguous choice in natural language and an exported Acta choice are equivalent inputs and normalize into the same decision record.
- DecisionGate validity requires an explicit selection, not a mandatory rationale. When the user supplies a rationale it is preserved. Gates never fold, auto-approve, infer approval from silence, or continue through a missing decision.
- A new user instruction may supersede an approved decision, but the skill records the supersession. During implementation, any change to architecture, API, data, security, or scope opens a STOP gate before work continues.
- Publication is a separate explicit action. The skill follows the consuming project's tracker and documentation rules; when no destination is discoverable, it asks rather than inventing one. Failed publication leaves the approved private artifact intact and reports the failure.
- After generating an HTML view, a skill tries a client-provided opening capability when available. Failure to open is nonfatal and returns the absolute path.

### Acta system and provenance

- Acta begins at internal version `0.1.0`. The publisher owns one canonical authoring source containing the version, protocol, design tokens, shared JavaScript behavior, component contracts, and fourteen recipe sources.
- The five Claude deliverables—research findings, direction comparator, component sheet, design-system specification, and QA report—are copied unchanged into a versioned provenance area. Their checksums are recorded. They are evidence, not executable sources. The component sheet is the baseline for human visual review.
- The executable Acta source is authoritative. It preserves the chosen Acta identity, DecisionGate borrowing, WaypointMap borrowing, token prefix, shell order, component contracts, four artifact families, print rules, and upstream-principle attribution documented in the handoff.
- Publisher-only Node tooling materializes one shared protocol reference into all fifteen skills and one recipe-specific, fully inline HTML scaffold into the fourteen HTML-producing skills. `make-me-realize` receives the protocol but no forced HTML scaffold.
- Installed skills never load publisher files, network resources, runtime packages, sibling directories, a renderer, a watcher, or a server. The agent treats the scaffold as a structural contract and produces the final self-contained view by filling the recipe with canonical state.
- Every materialized file carries a deterministic marker containing Acta version, recipe or protocol identity, a SHA-256 of canonical materialization inputs, and a do-not-edit notice. Generation time and Git revision are excluded from this marker.
- `npm run check` includes a check-only materialization mode and fails when any installed protocol or scaffold differs from canonical Acta inputs.

### Core cycle contracts

- **`make-me-realize`** integrates blind-spot discovery and batch frontier grilling. It distinguishes discoverable facts from user decisions, researches facts itself, records constraints and unknown ownership, produces structured Markdown only, and completes when every unknown is answered or explicitly owned.
- **`three-code-paths`** reads the project and prior realization, presents exactly three contextually distinct structural approaches at equal fidelity, includes representative code/interfaces/diffs, may create a disposable prototype only when reading cannot answer the decision, recommends after comparison, and completes on an explicit choice exported as Markdown plus decision JSON.
- **`interface-directions`** is conditional for visual or interaction work. It presents genuinely distinct product mockups inside an Acta comparison report, keeps Acta out of the candidate product styles, and completes on an explicit direction choice.
- **`change-blueprint`** performs a readiness check and delegates broad ambiguity back to realization. Gate A owns a compact `spec.md`; Gate B owns a separate `implementation-plan.md`. Each can be approved and historized independently. Gate A may be published before Gate B only after a separate request. The plan references the approved spec revision.
- **`build-with-notes`** treats an explicit implementation request as mutation authorization. Without an approved blueprint it derives a minimal contract from the prompt, ticket, or spec and records the provenance gap. It works test-first, refreshes append-only notes after slices and events, enforces STOP gates, performs internal diff review, proposes durable record updates for approval, and requires separate authorization before committing.
- **`do-i-understand-this`** builds a diagnostic quiz from the actual spec, plan, diff, and notes. It covers causality, limits, failure, rollback, security, and operations, exports gaps in Markdown/JSON with semantically meaningful attempt time and change revision, explains missed concepts, offers a retry, and never gates merge or cycle completion.

### Autonomous tool contracts

- **`feel-the-flow`** creates a disposable self-contained HTML prototype first, may use a disposable copy of the real stack only when required for fidelity, clearly marks nonproduction code, and completes when parameters and conclusions are exported.
- **`feature-xray`** explains an existing feature from source evidence, uses project domain vocabulary, cites file and line locations for load-bearing claims, distinguishes facts/inferences/gotchas, and produces a durable Markdown explanation plus Acta view without modifying code.
- **`concept-lab`** researches trusted sources, creates a manipulable conceptual model with a static no-JS equivalent, labels pedagogical simplifications separately from production behavior, cites sources, and may add a diagnostic quiz station.
- **`what-just-happened`** may begin during an active incident as a factual draft, records timeline and evidence without directing mitigation, and completes only after stabilization when cause, impact, hypotheses, and real or pending ownership can be stated honestly.
- **`draw-the-flow`** produces an overview-first flow artifact covering normal, decision, failure, and recovery paths, includes a complete textual equivalent, and optionally exports a standalone SVG.
- **`draw-it-in-svg`** produces an Acta figure sheet and individually reusable SVG files. Every SVG has its own title, description, caption, declared dimensions/palette, and copyable source.
- **`deepen-the-codebase`** reads the domain model and ADRs, scopes exploration by user direction or repository hot spots, compares evidence-backed deepening candidates using module/interface/depth/seam/leverage/locality vocabulary, never refactors, and exports the selected direction as a blueprint seed.
- **`find-the-cause`** builds a tight red-capable feedback loop, minimizes the reproduction, ranks falsifiable hypotheses, tests one variable at a time, permits temporary diagnostic harnesses/tests/instrumentation, cleans temporary changes, never applies the production fix, and exports the validated cause and fix direction as a blueprint seed.
- **`learning-workbench`** supports any topic in a durable user-selected workspace. It maintains mission, trusted resources, learning records, lessons, practice history, retrieval results, and spaced-review state in Markdown/JSON; Acta lessons remain self-contained and adapt to the learner's zone of proximal development.

### Publisher integration and rollout

- First publish this spec to the configured local Markdown tracker with `ready-for-agent` status, then split implementation into focused tracker issues for protocol/provenance, Acta materialization, core skills, autonomous tools, publisher validation/docs, manual evaluation, joint promotion, and release preparation.
- Extend repository architecture and domain documentation with Acta, the artifact protocol, bundle-first positioning, explicit stage transitions, and initial joint-promotion policy. Record the durable architectural decision separately from the development spec.
- Update public installation documentation to lead with the complete bundle. Keep interactive and single-skill installation documented as advanced capabilities and retain isolated-install acceptance.
- Generate all fifteen incubator entries and smoke definitions through the repository generator, replace every placeholder, generate the Codex sidecars, regenerate catalogs, and keep every skill portable from its first incubator revision.
- Promotion is one final gated change that moves all fifteen skills to stable together, regenerates catalogs, replaces compatibility placeholders with tested client versions, records the suite QA report, updates the changelog, and prepares release checks for `v1.0.0`. It does not dispatch the release workflow or create the tag.

## Testing Decisions

- The highest automated acceptance seam remains `npm run check`. Implementation extends this seam rather than introducing a competing root command.
- CI remains deterministic, credential-free, Linux/Windows, and static-only for HTML. It does not install Playwright, Axe, browsers, or screenshot infrastructure.
- Materializer tests verify deterministic output, exact Acta `0.1.0` markers, protocol/scaffold freshness, stable ordering, cross-platform line endings, rejection of unknown recipes, and unchanged output across repeated runs.
- Repository validation requires the canonical Acta source, all fifteen unique incubator skills, the shared protocol copy in each bundle, the correct scaffold in fourteen bundles, and absence of an HTML scaffold in `make-me-realize`.
- HTML static analysis uses a pinned authoring-only parser and checks well-formed structure, required shell/components, unique identifiers, native controls, noscript content, safe external-link attributes, no network resources, no webfonts/CDNs, no inline event handlers, no `innerHTML`/`document.write`/`eval`-style sinks, clipboard fallback, status region, print/reduced-motion rules, epistemic labels, provenance, export controls, and required responsive wrapper/breakpoint contracts.
- CSS/token tests verify the Acta token set, contrast calculations for declared text and UI pairs, 320px-oriented reflow rules, print transformations, zero shadows, radius restrictions, and motion constraints. These tests validate declared contracts, not real browser rendering.
- Sidecar tests parse all fifteen Codex metadata files and verify display name, short-description length, `$skill-name` mention in the default prompt, absence of required dependencies, and consistency with canonical skill metadata.
- Every skill has multiple committed trigger and adjacent non-trigger prompts where needed to exercise collisions with neighboring skills. Static validation verifies case completeness; model-backed activation is reserved for manual evidence.
- A cross-skill collision matrix covers realization versus blueprint, code paths versus interface directions, prototype versus implementation, feature explanation versus concept teaching, incident reporting versus debugging, architecture analysis versus implementation, and flow diagrams versus general SVG illustration.
- Installation tests continue to prove both the recommended whole-bundle install and isolated single-skill install into clean Codex and Claude Code destinations. Installed bundles are inspected for root/sibling dependencies and undeclared runtime requirements.
- Realistic filled artifacts for all fourteen recipes live only in repository test fixtures. Pixel screenshots are not versioned; visual changes are reviewed against component contracts and the copied component-sheet baseline.
- Manual browser promotion evidence exercises all fourteen recipes in current stable Chrome. Current stable Safari and Firefox exercise one representative Document, Compare, Explore, and Edit artifact plus DecisionGate, export/clipboard, quiz, disclosure, diagram, and editor interactions.
- Manual accessibility evidence covers keyboard-only operation, focus order, native control naming, 320px reflow, actual 400% zoom, print/PDF, no-JS reading, reduced-motion behavior, VoiceOver, and NVDA. Failures block promotion. Windows font rendering remains a documented risk rather than a blocking gate.
- Manual client evidence executes every committed trigger and non-trigger case in current stable Codex and Claude Code and records exact versions, activation behavior, observed result, and sidecar independence.
- The joint acceptance scenario uses a committed public synthetic project that contains a small user-facing feature, tests, and enough architecture to exercise all six core stages including conditional interface directions. The exact same scenario runs end to end in both clients, with every artifact, gate, publication boundary, STOP rule, and handoff compared against this spec.
- One versioned suite report records all fifteen skill trials, both client versions, the end-to-end results, browser matrix, accessibility results, known risks, and promotion verdict. Promotion cannot proceed with missing or pending required evidence.
- Release preparation runs the existing release check after promotion with concrete compatibility records and an updated changelog, but no tag, GitHub Release, or workflow dispatch occurs in this effort.

## Out of Scope

- Adding a public or private router skill to the initial package.
- Collapsing the collection into one mega-skill.
- Native Codex or Claude plugin manifests, hooks, packaged agents, MCP dependencies, or client-specific workflow behavior.
- Runtime rendering scripts, browser servers, file watchers, package installation, CDN access, webfonts, or shared sibling runtime directories.
- Browser localStorage, automatic downloads on every interaction, or direct HTML writes to canonical project files.
- Automatic stage transitions, inferred approval, mandatory decision rationale, or automatic publication after a gate.
- Requiring an approved blueprint before `build-with-notes` can implement an explicitly requested change.
- Letting `deepen-the-codebase` perform refactors or `find-the-cause` apply production fixes.
- Letting `what-just-happened` coordinate active incident mitigation.
- Treating `do-i-understand-this` as a merge gate.
- Pixel-perfect screenshot regression testing or headless-browser dependencies in public CI.
- Blocking the initial stable promotion on real-Windows font rendering, while still documenting the unverified fallback risk.
- Partial stable promotion, batch promotion, or declaring any one skill stable before the complete suite passes joint validation.
- Dispatching the `v1.0.0` release workflow, creating the tag, or performing post-release public installation verification.
- Copying the external Codex handoff as a sixth provenance deliverable; the five substantive design artifacts are the preserved source record.

## Further Notes

- The repository currently has no stable or incubating skills and already provides the generator, portable validator, catalogs, isolated install smoke tests, Linux/Windows CI, local Markdown tracker, domain context, and one accepted portable-publisher ADR.
- The existing portable-source ADR remains valid: bundle-first changes product emphasis, not the self-contained installation guarantee. A new decision record should add Acta, generated duplication, the common artifact protocol, and the initial suite-wide promotion gate.
- Acta's visual identity and implementation are original. Principles adapted from Thariq Shihipar's Apache-2.0 HTML-effectiveness work remain attributed, but upstream palette, layouts, tokens, and text are not copied.
- The copied Claude artifacts are immutable provenance. Future Acta changes update canonical authoring sources and create new decision/QA records rather than silently rewriting the original research package.
- The suite intentionally accepts generated duplication inside installed skills because installation tools copy skill directories independently. Maintenance duplication is avoided by materializing every shared copy from one publisher source.
- Automatic invocation makes description quality and collision testing load-bearing. Descriptions should lead with a precise action, enumerate distinct trigger branches once, and avoid repeating body identity or synonyms.
- Skill bodies should use progressive disclosure: ordered behavior and completion criteria stay in `SKILL.md`; the shared protocol and HTML scaffold remain shallow direct references. No skill reference may chain to another Markdown reference.
