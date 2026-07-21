# Compatibility

## Policy

Every stable skill supports the current stable Codex and Claude Code versions tested during promotion and release. The repository does not promise long-term support for obsolete clients.

Fundamentally client-specific skills remain in the incubator. Optional presentation sidecars cannot be required for correct behavior.

## Pre-release baseline

| Surface | Tested version |
| --- | --- |
| Node authoring runtime | `>=22.20.0` |
| CI Node line | `24` |
| skills CLI | `1.5.19` |
| Codex | Not yet recorded; no stable skill exists |
| Claude Code | Not yet recorded; no stable skill exists |

## Tested versions

Before a public release, replace this pre-release section with concrete rows for Codex, Claude Code, and the skills CLI. The release check rejects missing or placeholder client versions.

## Installation locations

The skills CLI currently uses `.agents/skills` as the canonical Codex-compatible location and `.claude/skills` for Claude Code. Treat those as tested client behavior rather than part of the portable Agent Skills specification.

## Tooling drift

The shared specification, client documentation, and locally installed helpers may evolve at different speeds. The repository-owned validator defines the accepted publisher contract; CLI discovery testing proves install compatibility but is not a strict specification validator.
