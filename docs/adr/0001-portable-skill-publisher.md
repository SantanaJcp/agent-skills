# ADR 0001: Publish one portable skill source

- **Status:** Accepted
- **Date:** 2026-07-21

## Context

The collection must support Codex and Claude Code, direct skill installation, public review, and a future path to native plugins without maintaining duplicate runtime-specific instructions.

## Decision

The repository publishes one canonical portable `SKILL.md` bundle per skill. Stable skills live in a flat `skills/` collection, experiments live in a flat `incubator/`, and every new skill starts incubating. Optional client sidecars may improve presentation but cannot control required behavior. The initial publisher contains no native plugin manifests.

The private Node package and its pinned dependencies are authoring infrastructure only. Installed skill scripts use cross-platform Node built-ins and bundled relative modules; they cannot require runtime packages or external command-line tools.

## Consequences

- A skill can be installed independently for both supported clients from the same source.
- Runtime-specific behavior stays incubating until it has a portable path.
- Native plugin manifests may later reuse the canonical collection without moving or duplicating skills.
- Strict repository validation and manual client trials are both required before promotion.
