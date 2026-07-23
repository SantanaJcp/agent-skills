# Agent Skills Library Context

## Purpose

This repository publishes one bundle-first development system of portable Agent Skills. It owns authoring policy, Acta, validation, catalogs, and releases; it is not a backup or synchronization target for personal skill directories.

## Ubiquitous language

- **Agent Skill** — a self-contained directory whose canonical portable instruction document is `SKILL.md`.
- **Portable core** — instructions and metadata that work unchanged in current stable Codex and Claude Code.
- **Bundle-first** — the complete collection is the recommended install, while each skill remains standalone-capable.
- **Stable collection** — reviewed skills under `skills/` carrying the compatibility promise.
- **Incubator** — experimental skills under `incubator/` without the stable promise.
- **Promotion cohort** — skills that must pass a shared gate before any member moves to stable.
- **Acta** — the print-first artifact design and protocol system materialized into installed skills.
- **Canonical artifact** — Markdown, plus JSON only when structured, that owns working state.
- **HTML view** — a regenerable offline human interface derived from canonical state.
- **DecisionGate** — a visible unresolved human choice that never folds or auto-approves.
- **STOP gate** — an implementation pause caused by architecture, API, data, security, or scope change.
- **Initiative workspace** — locally excluded `.agent-work/<initiative>/<skill>/` state.
- **Materialization** — deterministic publisher-time generation of self-contained installed references.
- **Sidecar** — optional client presentation metadata that cannot be required for portable behavior.
- **Smoke case** — a committed trigger or non-trigger prompt plus expected behavior.

## Invariants

1. Stable and incubating skills are flat, globally name-unique, self-contained bundles.
2. The initial product has exactly fifteen skills and no router.
3. New skills begin in the incubator; promotion is never implicit.
4. Stable behavior cannot require sibling skills, publisher files, runtime packages, external tools, or a client sidecar.
5. Markdown/JSON owns state; HTML never writes canonical files or hides persistent browser state.
6. Human stage transitions, decisions, publication, and commit remain explicit.
7. Installed bundles remain auditable: no symlinks, secrets, opaque executables, remote runtime assets, or unattributed media.
8. `npm run check` is the deterministic acceptance seam; manual client/browser/accessibility evidence remains a promotion gate.

The portable publisher decision is [ADR 0001](docs/adr/0001-portable-skill-publisher.md). The Acta suite decision is [ADR 0002](docs/adr/0002-acta-development-suite.md). The Acta v2 instrument/record pilot is preserved in [ADR 0003](docs/adr/0003-acta-v2-instrument-record-pilot.md); its complete-suite promotion candidate is [ADR 0004](docs/adr/0004-acta-v2-suite-generalization.md).
