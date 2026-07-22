# Compatibility

## Policy

Every stable skill supports the current stable Codex and Claude Code versions tested during promotion and release. The repository does not promise long-term support for obsolete clients.

The initial fifteen skills remain incubating until joint evidence is complete. Optional Codex sidecars improve presentation but are removed during part of manual testing to prove the portable core behaves identically in Claude Code and Codex.

## Pre-release baseline

| Surface | Tested version |
| --- | --- |
| Node authoring runtime | `>=22.20.0` |
| CI Node line | `24` |
| skills CLI | `1.5.19` |
| Acta authoring system | `0.1.0` |
| Codex | Pending initial cohort evidence |
| Claude Code | Pending initial cohort evidence |

Before promotion and `v1.0.0` preparation, replace pending client rows with exact tested stable versions and link the versioned suite report.

## Installation locations

The skills CLI currently uses `.agents/skills` as the canonical Codex-compatible location and `.claude/skills` for Claude Code. These are tested client behavior, not timeless specification guarantees.

A whole-collection install still creates separate skill directories. Materialized protocol and scaffolds therefore remain inside each skill so isolated installation works too.

## HTML surfaces

Acta artifacts target current stable Chrome, Safari, and Firefox through offline standards-based HTML, native controls, progressive enhancement, and system font stacks. Promotion evidence is time-bound to recorded browser versions. Real-Windows serif rendering is not part of the initial blocking promise.

## Tooling drift

The Agent Skills specification, client discovery, skills CLI, and browser behavior may evolve independently. Repository validation defines the accepted publisher contract; manual trials provide current compatibility evidence.
