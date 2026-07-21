# Architecture

## One portable source

Each skill is one self-contained Agent Skills directory with a canonical `SKILL.md`. Stable skills use only the portable core fields needed by this repository. Optional client presentation sidecars may enhance discovery or appearance, but correct behavior cannot depend on them.

Codex and Claude Code use different native discovery locations and expose different extensions. The stable contract deliberately sits above those client-specific surfaces: every stable skill must be manually exercised in both current clients.

## Maturity model

The source tree has two flat collections:

- **Stable** — published skills covered by the dual-client compatibility promise.
- **Incubator** — new, experimental, or fundamentally nonportable skills.

All skills begin in the incubator. Promotion moves a completed skill into stable after deterministic checks and recorded client trials. Tags create topical catalog views without category subdirectories.

## Distribution boundary

The publisher exposes conventional skill directories to `npx skills add`. The CLI can install one skill or the collection for Codex and Claude Code. Project installs may create consumer lock state; that state is not publisher metadata and is ignored at the repository root.

Native Codex and Claude plugins are different products. They can package hooks, MCP servers, agents, and lifecycle behavior that the skills CLI does not install. Plugin manifests are intentionally absent from the initial architecture.

## Dependency boundary

Installed skill directories are self-contained. Repository authoring tooling, development dependencies, catalogs, tests, and release automation remain outside installed skills.

Skill scripts use `.mjs`, Node built-ins, and bundled relative modules only. They do not launch external processes or require runtime packages. Network modules are possible only after explicit manual review.

## Trust boundary

Skills run with the invoking agent's permissions. Deterministic checks enforce auditable file types, containment, dependency rules, metadata, and catalog freshness. Human review remains responsible for instruction safety, semantics, third-party provenance, and any network data flow.
