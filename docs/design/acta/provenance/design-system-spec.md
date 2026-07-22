# Acta — design system specification

- **Version:** 0.1.0 (proposal)
- **Date:** 2026-07-21
- **For:** the public agent-skills publisher (`/Users/santana/Development/agent-skills`)
- **Status:** designed and prototyped outside the repository; not yet implemented
- **Companion artifacts:** `component-sheet.html` (living reference), `direcciones-comparador.html` (direction exploration), `research-findings.md` (upstream analysis), `qa-report.md`
- **Attribution:** principles adapted from “The unreasonable effectiveness of HTML” (Thariq Shihipar, Apache-2.0, `github.com/ThariqS/html-effectiveness` @ `1787245d94aa680edf18b52027e3f859032776ba`). The identity, token system, components, scaffolds, and contracts below are original.

---

## 1. Identity

### Name

**Acta** — the artifact as an engineering record. (Latin *acta*: recorded proceedings. Works unitalicized in English and Spanish.)

### Personality

Notarial, calm, typographic. An Acta artifact reads like a beautifully set engineering document that could be printed, filed, and signed. Paper first, screen second. Interaction is sober and secondary; nothing competes with the text.

### Principles

1. **Two layers.** A stable shell contract (provenance → title → summary → navigation → sections → export → sources → colophon) wraps a free instrument per job. The shell is recognizable across the collection; the instrument changes shape with the work.
2. **Print-first.** The printed page is the reference rendering. If it does not survive monochrome A4, it is not done.
3. **Provenance is front matter, not a footnote.** Every durable artifact opens with what it is, over what, from when, and from which inputs — and states when it goes stale.
4. **Evidence is cited, not asserted.** Load-bearing claims carry an epistemic label (Fact / Inference / Simplification), a location, and a register id `[En]` resolved in a source register at the foot.
5. **Decisions are registered, stamped, and signable.** Numbered rows (D-01…) with status, reversibility, change-conditions, folded alternatives at equal fidelity, and a one-line copyable reply to change them. Gates make “waiting for the human” a first-class visual state.
6. **Hierarchy by type, space, rules, and tint.** Hairlines divide; double rules open and close; tints fill; shadows never appear. Boxes are earned, not default.
7. **Three typographic voices with strict roles.** Serif reads, mono records, system-ui controls (rarely). Every number, identifier, path, and timestamp is mono.
8. **Disclosure follows decision value.** Fold what the reader is unlikely to change; never fold warnings, gates, or evidence for open decisions.
9. **Equal-fidelity alternatives; the recommendation arrives after.** Comparisons use identical structure per option and end at a gate.
10. **Overview before detail.** Documents summarize before they elaborate; diagrams show the whole before the part.
11. **Every interaction ends in text.** All interactive state exports to Markdown (always) and JSON/diff (when structured); preview and exports derive from the same state. HTML is the human interface, not the canonical source.
12. **Motion is color, not movement.** 90 ms linear color/border transitions at most; nothing essential depends on them.

### Deliberately avoided

- Warm clay/oat/ivory palettes and any hex from the upstream; window-bar mockup chrome; filled pill badges; rounded cards; decorative shadows; skeuomorphic paper textures.
- Webfonts, CDNs, frameworks, build steps, network requests of any kind.
- `innerHTML` with dynamic data; inline event handlers; color-only state.
- Universal grids: layout belongs to the problem (single column, split, columns, board — per recipe).
- HTML as the source of truth: Markdown/JSON stay canonical; the artifact is a view.

---

## 2. Semantic tokens

Prefix `--acta-`. Values are the cleared defaults; skills materialize them verbatim (see §6). All text pairs measured ≥ AA (see `qa-report.md`).

### Surfaces

| Token | Value | Use |
|---|---|---|
| `--acta-paper` | `#FDFDFB` | page background |
| `--acta-tint` | `#F4F3EC` | fills: schema code, decision ids, table heads |
| `--acta-tint-strong` | `#EAE8DE` | hover/active fills |
| `--acta-inverse` | `#23252B` | scarce emphasis: code, ≤ 1 TL;DR block per artifact |

### Text

| Token | Value | Contrast |
|---|---|---|
| `--acta-ink` | `#1D1F24` | 16.2:1 on paper |
| `--acta-ink-muted` | `#50545C` | 7.5:1 on paper |
| `--acta-ink-inverse` | `#E7E5DE` | 12.2:1 on inverse |
| `--acta-ink-inverse-muted` | `#A5A8A0` | 6.4:1 on inverse |

### Borders

| Token | Value | Use |
|---|---|---|
| `--acta-rule` | `#D8D6CC` | hairline dividers (decorative) |
| `--acta-rule-strong` | `#8E8B7E` | structural rules, double rules, citation bars (3.4:1 UI) |

### Semantic colors (each with a `-tint` companion surface)

| Token | Value | Tint | Meaning |
|---|---|---|---|
| `--acta-action` | `#2B4C7E` | `#E9EEF5` | links, primary actions, inference label, info |
| `--acta-positive` | `#276140` | `#E8F0E9` | verified, done, fact label |
| `--acta-warning` | `#7A5600` | `#F6EFDC` | caution, draft, simplification label |
| `--acta-danger` | `#8C2F23` | `#F6E9E6` | failure, blocking, deletions |

Code accents on inverse: `--acta-code-add #9CC8A9`, `--acta-code-del #E8A99C`, `--acta-code-dim #989C92`.

### Typography

| Token | Stack | Role |
|---|---|---|
| `--acta-font-text` | `Charter, "Iowan Old Style", "Palatino Linotype", Georgia, "Times New Roman", serif` | reading voice: body, titles, claims |
| `--acta-font-data` | `ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace` | record voice: provenance, metrics, paths, labels, code |
| `--acta-font-ui` | `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, sans-serif` | control voice (form controls only) |

Scale: display 36/1.15 · section 24/1.25 · subsection 17/1.35 · body 16/1.62 · small 14 · data 12–13 · labels 10–11 uppercase tracked .12–.14em. Reading measure ≤ 70ch (`--acta-measure`).

### Space, radius, border, motion, breakpoints

- Space: `--acta-s1…s8` = 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 px.
- Radius: `--acta-radius: 2px` — controls only; everything else square.
- Border grammar: 1px hairline divides; 2px left bar cites (evidence); 2px solid ink frames gates; 3px double rule opens/closes the record.
- Motion: `--acta-quick: 90ms linear`, color/border properties only. `prefers-reduced-motion` strips all transitions/animations globally.
- Breakpoints: **960** (rails collapse) and **720** (single column). Must reflow to **320** with horizontal scrolling only inside `.codewrap` / `.tablewrap` / `.flowwrap`.

### Print

- Body ~11.5pt serif on white; `.acta-*` controls hidden; details forced open (`beforeprint` + criticals never folded).
- Inverse surfaces flip to white with 1px #999 frame; diff signs (+/−) preserve meaning without color.
- External links print their URL after the text. Page-break avoidance on sections, figures, gates, evidence, quiz items.
- Provenance and source register always print.

---

## 3. Component contracts

Every component below exists in `component-sheet.html` with rendered markup. Class names are the contract; skills copy the materialized CSS (§6) and use these classes.

### 3.1 ArtifactShell (`.acta-shell`)
- **Purpose:** page frame and section rhythm; max-width 920px, side padding s5, end padding s8.
- **When:** every artifact. **When not:** never absent.
- **Required order:** ProvenanceHeader → ContextHeader → (SourcePrompt) → SummaryBand → SectionNavigator → sections → ExportBar → sources → colophon.
- **States:** none. **A11y:** one `h1`; sections are `<section>` with `h2`; skip link precedes.
- **Responsive:** fluid; padding shrinks via defaults. **Print:** max-width removed.

### 3.2 ProvenanceHeader (`.acta-prov` + `.acta-prov-note`)
- **Purpose:** legal front matter: artifact type, project@commit(or range), scope, ISO date, inputs; staleness note below.
- **When:** all durable artifacts. **When not:** throwaway prototypes may compress to a single `.acta-prov-note` line — never to zero.
- **States:** none. **A11y:** `<dl>` with `dt/dd`. **Responsive:** grid auto-fits ≥150px columns; borders drop at 720. **Print:** always printed.
- **Export:** serialized verbatim into Markdown front matter and JSON `provenance` object.

### 3.3 ContextHeader (`.acta-context`)
- **Purpose:** eyebrow (mono, uppercase: artifact kind · project) + `h1` + italic lede + status line of stamps.
- **Required:** eyebrow, title, lede ≤ 2 sentences, ≥ 1 lifecycle stamp.
- **When not:** never absent. **Print:** as-is.

### 3.4 SourcePrompt (`.acta-source`)
- **Purpose:** record the originating human request beside the output.
- **When:** explainers/reports shaped by the question (feature-xray, concept-lab, what-just-happened ad-hoc asks).
- **When not:** gate flows where spec.md records intent (change-blueprint), quizzes.
- **Security:** prompt text is untrusted → text nodes only. **Export:** included under `## Originating request`.

### 3.5 SummaryBand (`.acta-summary`)
- **Purpose:** the whole story in ≤ 5 lines before any section; contains MetricStrip.
- **Required:** decision-relevant summary (what, why it matters, what is asked of the reader).
- **Variant:** one inverse TL;DR block allowed for incident records. **Print:** always.

### 3.6 SectionNavigator (`.acta-toc` | `.acta-waymap`)
- **Index variant:** §-numbered column list; default for ≥ 3 sections; static anchors, no JS.
- **Waypoint variant:** numbered stations with dotted connectors; for guided explainers; JS adds `aria-current` station highlight via IntersectionObserver; works bare without it.
- **When not:** ≤ 2 sections. **A11y:** `<nav aria-label>`; current = `aria-current`; visited = `.done` + ✓. **Print:** index prints; waymap prints as list.

### 3.7 Disclosure (`.acta-disclosure`)
- **Purpose:** fold by decision value. Summary must state contents + size (“Mechanical work — safe to skip (4 tasks · ~0.5 d)”).
- **Never folds:** warnings, gates, open-decision evidence.
- **A11y:** native `<details>/<summary>`. **Print:** `beforeprint` opens all.

### 3.8 StatusBadge (`.acta-stamp`, `.acta-label`)
- **Stamps** (lifecycle): draft / approved / blocked / info / neutral. Bordered letterpress, uppercase mono; state text inside the stamp.
- **Labels** (epistemic): fact / inference / simplification; mandatory on evidence; defined again in colophon.
- **A11y:** meaning lives in text; color reinforces. Monochrome-safe.

### 3.9 MetricStrip (`.acta-metrics`)
- **Purpose:** 3–5 headline numbers (effort, files, risk, tests…); values mono; semantic value colors allowed with text intact.
- **When not:** more than ~5 metrics → DataTable instead. **Responsive:** wraps; dividers drop.

### 3.10 EvidenceBlock (`.acta-evidence`)
- **Required:** claim + epistemic label + `[En]` ref + location (file:line / log+date) + how verified (`.e-src`).
- **Pairs with:** CodeSurface snippet when the evidence is code.
- **Export:** all `[En]` entries appear in the source register and in exports. **Security:** repo content escaped, never linked off-host.

### 3.11 DecisionCard (`.acta-decisions` > `.acta-decision`)
- **Required:** ID, title, what/why, status, reversibility, change-if condition, folded equal-fidelity alternative, one-line copyable reply.
- **Rule:** decisions form a register (table-like rows), referenced by ID from code comments, timeline, and exports.
- **Export:** JSON `{id,title,status,reversible,changeIf}` + Markdown list.

### 3.12 DecisionGate (`.acta-gate`) — borrowed from «Consola», restated
- **Purpose:** first-class “waiting for the human” state; blocks progress visibly.
- **Required:** gate id, what approval unlocks, done/pending checklist, stamp, copyable approve/amend replies, note that the agent proceeds only after the reply lands in conversation.
- **When:** change-blueprint phase gates; three-code-paths/interface-directions final choice; build-with-notes stop conditions.
- **Never:** folded, auto-approved, or simulated as approved. **Print:** renders as a signature block.

### 3.13 ComparisonSet (`.acta-compare` + summary matrix)
- **Required:** identical per-option structure (numbered label · title · traits · choose-if); a summary DataTable that persists on mobile; recommendation after the set, outside any option; ends at a DecisionGate.
- **Responsive:** columns stack < 720; matrix remains the at-a-glance view.

### 3.14 CodeSurface (`.acta-code`, `.is-inverse`)
- **Variants:** inverse (source, diffs), tint (schema, config, export previews).
- **Required:** path header (+ optional right-side annotation: evidence/decision ids); adds/dels as color **plus** `+`/`−` characters; `.codewrap` scroll.
- **Print:** inverse flips light, bordered; signs survive monochrome.

### 3.15 DataTable (`.acta-table` in `.tablewrap`)
- **Required:** `caption`, `th scope` both axes, numbers right-aligned `.num`, every value states its basis where the table makes claims.
- **Rule:** always wrapped in `.tablewrap`; the page never scrolls horizontally.

### 3.16 Timeline (`.acta-timeline`)
- **Required:** mono timestamp + STATE keyword in the label text; dot color (done/now/impact) reinforces only.
- **When:** incidents, sequenced plans, build logs. **Print:** dots render as outlined/filled squares — meaning stays in text.

### 3.17 StickyRail (`.acta-cols` + `.acta-rail`)
- **Purpose:** desktop-only orientation (mini-index, per-section annotations).
- **Rule:** duplicates, never sole-carries content. **Responsive:** static below 960. **Print:** hidden.

### 3.18 DiagramNode / DiagramEdge (SVG conventions inside `.acta-figure`)
- **Node:** `rect` ink/1.2; new = tint fill; emphasized = action/2; failure = danger dashed.
- **Edge:** ink/1.2 + arrowhead; failure = danger dashed; labels 10.5 muted.
- **Required:** `role="img"` + `title` + `desc` (full textual equivalent); numbered `figcaption` (**Fig. n —**); `.acta-legend` mapping shape+color; `min-width` inside `.flowwrap`.
- **Overview→detail:** big flows get a whole-system figure first, then per-stage figures or a detail list; click-to-inspect is enhancement only.

### 3.19 EditorControl (`.acta-control`, `.acta-seg`)
- **Rule:** native inputs only; label states what the control decides; current value mirrored as text; derived consequence visible (table/preview) and exportable.
- **A11y:** real `<label for>`; segmented buttons use `aria-pressed`; drag interactions always have a control equivalent (no drag-only).
- **No-JS:** default state meaningful; controls degrade to their static values.

### 3.20 ExportBar (`.acta-export`) + StatusRegion (`.acta-status`)
- **Required:** “Copy as Markdown” always; “Copy JSON” / “Copy diff” when structured state exists; hidden `<pre>` blocks hold the payloads; a note that the canonical source is the .md/.json file when one exists.
- **Behavior:** async clipboard → `execCommand` fallback → honest failure message; StatusRegion `role="status" aria-live="polite"` announces every outcome; button text flashes.
- **Rule:** preview, Markdown, and JSON derive from the same state object. **Print:** buttons hidden.

### 3.21 Quiz (`.acta-quiz`, `.acta-score`)
- **Rule:** diagnostic, never a merge gate. Questions probe causality, behavior, limits, failure, rollback, security, operations — no file trivia. Wrong answers link the evidence/section that teaches it.
- **Required:** fieldset+legend per question; radio options; check button; good/bad feedback blocks; running score; export of gaps + timestamp + change version.
- **No-JS:** options readable; answer key in `<noscript><details>`.

### 3.22 NoScriptFallback (`.acta-noscript`)
- **Purpose:** inside `<noscript>`, states exactly which enhancements are off and where their content lives as text.
- **Rule:** essential content never requires JS; this block proves the artifact knows it.

---

## 4. Recipes per skill

Family legend: **Document** (read/review), **Compare** (choose), **Explore** (understand), **Edit** (operate live). “Shell” = full shell contract from §3.1.

### 4.1 make-me-realize — no HTML
Structured text output (facts vs user-only decisions, constraints, open unknowns). Interview via AskUserQuestion when available. **Do not force HTML.** Completion: every unknown owned or answered.

### 4.2 three-code-paths — Compare
Shell + ComparisonSet (3 options, code via CodeSurface inside each) + summary matrix + recommendation block + **DecisionGate (choice)**. Interactions: copy replies, optional seg toggle side-by-side/matrix. Export: Markdown of options+choice, JSON decision. No-JS: fully readable. Print: options sequential, matrix intact. Completion: gate resolved with rationale in conversation.

### 4.3 interface-directions — Compare
Same skeleton as 4.2; options are directions with token samples and mini-mockups built from Acta primitives (no window chrome). Must expose layout, density, tone, hierarchy, behavior differences. Completion: explicit choice; no cosmetic-variant sets.

### 4.4 change-blueprint — Document (two gated phases)
Phase A `spec.md` canonical → HTML view: Shell + SummaryBand + EvidenceBlocks + DecisionCards + acceptance-criteria DataTable + **Gate A**. Phase B plan: adds Timeline (slices), DiagramNode/Edge (data flow), CodeSurface (riskiest code), risk DataTable, mitigations, test strategy, rollout + **Gate B**. Exports: Markdown (canonical), JSON decisions. Deferred decisions carry owner+deadline in the gate checklist. Completion: both gates signed.

### 4.5 build-with-notes — Edit (live view)
`notes.md` append-only canonical → HTML live view: ContextHeader stamps (progress), MetricStrip (typecheck/tests/deviations), deviation log as EvidenceBlocks, **STOP gates** for architecture/API/data/security/scope changes, Timeline of steps, ExportBar (Markdown notes, JSON status). Read-only self-contained fallback when no subagent/watch capability exists. Print: session record. Completion: final validation green + decisions distilled to spec/ADR/tickets; commit only after explicit authorization.

### 4.6 do-i-understand-this — Edit
Shell + SummaryBand (what changed) + optional before/after figure + **Quiz** (causality/limits/failure/rollback/security/ops) + score + ExportBar (Markdown + JSON gaps/timestamp/change-version). Diagnostic framing in the lede: *not a merge gate*. No-JS: answer keys in noscript.

### 4.7 feel-the-flow — Explore (throwaway)
Reduced shell (one-line provenance note allowed). EditorControls + live preview region + parameter readout; every parameter lands in text and ExportBar (JSON params + Markdown decision note). Banner: *prototype code — not for production reuse by default*. Completion: exported parameters/decisions.

### 4.8 feature-xray — Document
Shell + SourcePrompt + SummaryBand (TL;DR) + waypoint or index nav + operational walkthrough (Timeline or numbered sections) + EvidenceBlocks with CodeSurface snippets (file:line everywhere) + gotchas as warning Callouts + FAQ (Disclosures). Export: Markdown. Completion: every claim labeled + located.

### 4.9 concept-lab — Explore
Shell + **waypoint navigator** + model figure(s) + one manipulable EditorControl model with derived-consequence table + **Simplification labels separating pedagogy from production behavior** + sources (trusted, allowlisted, printed) + optional Quiz station. No-JS: static model states rendered. Completion: model manipulable or fully described statically; simplifications declared.

### 4.10 what-just-happened — Document
Shell + inverse TL;DR (the one allowed inverse block) + severity/duration stamps + **Timeline (semantic dots)** + root cause (EvidenceBlocks + diff CodeSurface) + impact DataTable (values with basis) + hypotheses considered (Disclosure) + action items with owner/date *only if real* — never invented (pending = “owner pending” warning Callout). Export: Markdown postmortem. Completion: after mitigation; every claim evidence-backed.

### 4.11 draw-the-flow — Explore
Shell + overview figure first, then per-stage detail figures or annotated list; normal/decision/failure/recovery paths per SVG grammar; timings as edge labels; legend + full textual equivalent (`desc` + optional Disclosure transcript). Click-to-inspect rail is enhancement. Export: Markdown description; optional standalone SVG. Completion: textual equivalent complete.

### 4.12 draw-it-in-svg — Explore (figure sheet)
Shell + one `.acta-figure` per figure: purpose line, palette/dimensions in mono meta, the SVG, caption. Each SVG self-contained (own title/desc, no shared defs) and exportable: “Copy SVG source” per figure via tint CodeSurface + copy button. Completion: every figure works outside the sheet.

### 4.13 deepen-the-codebase — Compare (analysis only)
Shell + module map figure + candidates as ComparisonSet entries (before/after mini-figures, depth/seam/leverage vocabulary as mono labels) + evidence per candidate + **handoff gate**: chosen direction exports as a change-blueprint seed (Markdown). Never refactors. Completion: choice exported.

### 4.14 find-the-cause — Document (diagnosis record)
Shell + feedback-loop note (how red was reproduced, EvidenceBlock) + minimization Timeline + falsifiable hypotheses DataTable (hypothesis / prediction / test / verdict) + one-variable instrumentation log + validated cause (fact-labeled evidence) + fix direction → change-blueprint seed export. Read-only badge in eyebrow (“diagnosis — no production changes”). Completion: cause validated with evidence.

### 4.15 learning-workbench — Explore (stateful)
Canonical state in Markdown records (mission, resources, lessons, practice log). HTML lesson views: Shell + waypoint navigator + concept figures + practice Quiz (retrieval) + spaced-review DataTable (next-review dates from JSON state) + ExportBar (Markdown record + JSON learning state). Completion per lesson: quiz attempted, record exported.

---

## 5. QA gates (verifiable)

Ship an artifact only when all pass:

1. **Offline/file://** — zero network requests (DevTools); opens from `file://` clean.
2. **No-JS** — with JS disabled: all prose, evidence, decisions, tables, figures readable; NoScriptFallback present; quiz keys reachable.
3. **Keyboard** — full tab order, visible focus (`:focus-visible` 2px action outline), no traps; details/quiz/controls operable; no drag-only interaction.
4. **WCAG 2.2 AA** — text ≥ 4.5:1, large/UI ≥ 3:1 (token pairs pre-cleared; verify new combinations); zoom 400% and reflow at 320px lose nothing.
5. **Safe DOM** — no `innerHTML`/`insertAdjacentHTML` with dynamic data; `textContent`/`createElement` only; no inline handlers; untrusted content (code, git, tickets, logs, prompts, web) always text.
6. **Secrets** — scan for tokens/keys/PII/signed URLs before save; provenance carries no credentials.
7. **Responsive 320** — `scrollWidth ≤ viewport`; horizontal scroll only inside `.codewrap`/`.tablewrap`/`.flowwrap`.
8. **Print** — controls hidden, disclosures expanded, monochrome meaning intact (labels/shapes carry state), provenance+sources+URLs printed, no card splits.
9. **Reduced motion** — media query leaves zero transitions/animations.
10. **Clipboard** — API + fallback + honest failure; StatusRegion announces all outcomes.
11. **Exports** — Markdown always; JSON/diff when structured; all derived from one state; canonical file named when one exists.
12. **Provenance** — type, project, scope, date, commit/range, inputs, staleness note.
13. **Epistemic labels** — every load-bearing claim labeled; register resolves all `[En]`.
14. **External links** — allowlisted hosts only, `rel="noopener noreferrer"`, URL printed in print.

Suggested automated checks (publisher tooling, not runtime): grep gates (5, 6, 14), headless overflow measurement (7), headless print smoke (8), tag-balance parse, and a token-pair contrast table (4) — all implementable with Node built-ins + headless Chrome when available locally; none required at artifact runtime.

---

## 6. Distribution & materialization

### Source of truth

The publisher owns one canonical design-system source, versioned in-repo (suggested location: `design/acta/` at repository root — *authoring infrastructure, not a skill*):

- `design/acta/acta.css` — tokens + components (the `<style>` block of the component sheet, unchanged).
- `design/acta/acta.js` — the enhancement runtime (copy/status/quiz/waymap/beforeprint), safe-DOM only.
- `design/acta/scaffolds/<family-or-skill>.html` — per-recipe skeletons (document, compare, explore, edit variants) with `{{PLACEHOLDER}}` slots for provenance, title, sections.
- `design/acta/VERSION` — semver of the system.

### Materialization

An authoring tool (repo `scripts/`, Node built-ins only — **not implemented yet, per this engagement**) copies, per skill:

```
skills/<name>/assets/acta/acta.css
skills/<name>/assets/acta/acta.js        (only if the recipe uses enhancements)
skills/<name>/references/scaffold-*.html (the recipe’s skeletons, CSS+JS inlined)
```

- Scaffolds are materialized **with CSS and JS already inlined** — a skill’s SKILL.md instructs the agent to start from its own bundled scaffold and keep everything inline. Installed skills never reference `design/acta/`, sibling skills, or any URL.
- `THIRD_PARTY_NOTICES.md` needs no entry (original, Apache-2.0, project-owned) unless future assets change that.

### Markers & versioning

Each materialized file carries a header comment:

```
/* acta v0.1.0 · materialized 2026-07-21 · source design/acta @ <git hash> · do not edit by hand */
```

### Freshness validation

`npm run check` gains a deterministic rule: for every skill bundling Acta assets, the materialized content hash must equal the current `design/acta` build for the version the skill pins. Drift → check fails with “re-run materializer”. Skills may pin older majors intentionally (recorded in the marker); the check then validates against that tag, keeping bundles auditable and reproducible.

### What lives in each bundle vs never at runtime

| In the installed bundle | Never required at runtime |
|---|---|
| Inlined CSS/JS inside scaffolds; the scaffold HTML; recipe notes in SKILL.md/references | `design/acta/` source; the materializer; npm/dev deps; network fetches; sibling skills; the publisher repo itself |

Artifacts produced by an installed skill are single-file HTML with everything inline — the bundle’s scaffold already satisfies file://, no-CDN, and no-build constraints by construction.
