# Architecture

## One portable source

Each skill is one self-contained Agent Skills directory with a canonical `SKILL.md`. The fifteen-skill product is **bundle-first, standalone-capable**: documentation recommends installing the complete suite, while each directory remains independently discoverable and executable. Codex sidecars improve presentation but never control required behavior.

Codex and Claude Code expose different extensions. Stable behavior sits above those client surfaces and must be manually exercised in current versions of both clients.

## Suite topology

Six core skills form an advisory development cycle. Nine autonomous tools can be used anywhere. There is no router skill and no automatic stage transition. A skill may export a seed and recommend another named skill; the human explicitly chooses the next stage.

The initial fifteen skills were promoted together to `skills/` after their individual activation trials and complete core-cycle trials passed in both clients. The owner explicitly deferred the browser and accessibility matrices for this first promotion; the waiver is recorded in the suite report and ADR 0005. Later additions still begin in the incubator under the normal reviewed promotion process.

## Acta

Acta 0.1.0 is the publisher-owned design and artifact system. Its canonical authoring source includes the protocol, tokens, component contracts, shared progressive-enhancement behavior, and fourteen recipe instruments. The copied design-phase deliverables are immutable provenance and a visual baseline, not runtime sources.

Publisher tooling deterministically materializes:

- one identical protocol reference into all fifteen skills;
- one fully inline recipe scaffold into each of the fourteen HTML-producing skills.

Materialized files carry Acta version and a SHA-256 of canonical inputs. Dates and Git hashes are excluded from build markers. Installed skills never read the canonical authoring source or sibling directories.

### Acta v2 (promoted)

All fourteen HTML skills use the authoritative Acta v2 instrument/record split — piloted by `three-code-paths`, `build-with-notes`, and `concept-lab` ([ADR 0003](adr/0003-acta-v2-instrument-record-pilot.md)), generalized to the complete suite ([ADR 0004](adr/0004-acta-v2-suite-generalization.md)), and promoted in [ADR 0005](adr/0005-promote-acta-v2-suite.md). The suite manifest `design/acta2/lib/suite.mjs` is the single source of truth for each skill's role (instrument + record, record-only, or instrument-only); canonical v2 sources live in `design/acta2/`, and `npm run acta2` deterministically materializes, per skill, a self-contained generator bundle (`references/acta2/`), rendered scaffold examples, and realistic open-scenario test fixtures. Installed skills generate `instrument.html` from `scenario.json` and `record.html` from `canonical.json` with the bundled generators (Node built-ins only) — HTML artifacts are never hand-edited. State machines cover six kinds (decision, stop-gate, model, prototype, quiz, checklist) plus record-only dossiers; shared Node-side renderers supply syntax-highlighted code islands (`lib/highlight.mjs`), node/edge flow diagrams (`lib/flow.mjs`), and constrained vector figures (`lib/figure.mjs`). Static v2 gates run in `npm run validate:acta2`; state/export invariants and round-trips live in `tests/acta2.test.mjs`. Every skill retains its Acta 0.1 references as a compatibility fallback; `make-me-realize` stays deliberately text-only.

## Artifact authority

Technical working state lives under `.agent-work/<initiative>/<skill>/`, locally excluded through `.git/info/exclude`. Learning workspaces use a durable user-selected directory.

Markdown is canonical. JSON is canonical only for genuinely structured state. HTML is a regenerable, self-contained, offline interface. Browser state is ephemeral; HTML cannot write project files. Decisions and publication require explicit human actions.

Approved Markdown/JSON revisions are archived before supersession. HTML is regenerated rather than archived. Shared statuses are draft, awaiting-decision, approved, completed, blocked, and superseded.

## Distribution boundary

`npx skills add` installs separate skill directories even for a whole-collection selection. Generated duplication is therefore intentional: the publisher maintains one Acta source and consumers receive self-contained bundles. Native plugins, hooks, agents, and MCP dependencies remain outside the initial architecture.

## Dependency and trust boundaries

Installed skill scripts, when present, use `.mjs`, Node built-ins, and bundled relative modules only. They do not launch external processes or require runtime packages. Repository authoring tooling may use exact lockfile-pinned dependencies.

Skills execute with the invoking agent's permissions. Deterministic checks enforce auditable files, containment, metadata, materialization freshness, HTML safety contracts, sidecar presentation-only behavior, and catalogs. Human review remains responsible for semantics, client activation, real browser rendering, assistive technology, provenance, and network data flow.
