# Agent Skills Library Context

## Purpose

This repository is a curated publisher of independently installable Agent Skills. It owns authoring policy, validation, catalogs, and releases; it is not a backup or synchronization target for personal skill directories.

## Ubiquitous language

- **Agent Skill** — a self-contained directory whose canonical portable instruction document is `SKILL.md`.
- **Portable core** — the instructions and metadata that must work unchanged in current stable Codex and Claude Code.
- **Stable collection** — reviewed skills under `skills/` that carry the repository compatibility promise.
- **Incubator** — experimental skills under `incubator/` that do not carry the stable promise.
- **Promotion** — an explicit reviewed move from the incubator to the stable collection after deterministic and manual evidence gates pass.
- **Publisher** — this repository and its committed source; it must not contain consumer installation state.
- **Consumer** — a user or project that installs one or more skills and may own a `skills-lock.json`.
- **Sidecar** — optional client presentation metadata that cannot be required for portable behavior.
- **Smoke case** — a committed trigger or non-trigger prompt plus its expected activation behavior.

## Invariants

1. Stable and incubating skills are flat, globally name-unique, self-contained bundles.
2. New skills begin in the incubator; promotion is never implicit.
3. Stable behavior cannot require sibling skills, repository files, runtime packages, external tools, or a client-specific sidecar.
4. Installed bundles remain auditable: no symlinks, secrets, opaque executables, or unattributed assets.
5. `npm run check` is the single deterministic acceptance seam used locally and in CI.

The foundational architecture decision is recorded in [ADR 0001](docs/adr/0001-portable-skill-publisher.md).
