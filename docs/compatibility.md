# Compatibility

## Policy

Every stable skill supports the current stable Codex and Claude Code versions tested during promotion and release. The repository does not promise long-term support for obsolete clients.

The initial fifteen skills are stable. Optional Codex sidecars improve presentation but were removed during part of manual testing to prove the portable core behaves identically in Claude Code and Codex.

## v1.0.0 baseline

| Surface | Tested version |
| --- | --- |
| Node authoring runtime | `>=22.20.0` |
| CI Node line | `24` |
| skills CLI | 1.5.19 |
| Acta authoring system | `0.2.0` (`0.1.0` compatibility fallback retained) |
| Codex | 0.144.1 |
| Claude Code | 2.1.206 |

The tested promotion evidence is recorded in [the Acta v2 suite report](qa/acta-suite-0.2.0.md).

## Installation locations

The skills CLI currently uses `.agents/skills` as the canonical Codex-compatible location and `.claude/skills` for Claude Code. These are tested client behavior, not timeless specification guarantees.

A whole-collection install still creates separate skill directories. Materialized protocol and scaffolds therefore remain inside each skill so isolated installation works too.

## HTML surfaces

Acta artifacts target current stable Chrome, Safari, and Firefox through offline
standards-based HTML, native controls, progressive enhancement, and system font
stacks. The `v1.0.0` release did not claim manual browser or assistive-technology
validation: ADR 0005 records the explicit deferral, and
[GitHub Issue #8](https://github.com/SantanaJcp/agent-skills/issues/8) tracks the
versioned matrix. Static HTML checks are not a substitute for that evidence.
Real-Windows serif rendering is not part of the initial blocking promise.

## Tooling drift

The Agent Skills specification, client discovery, skills CLI, and browser behavior may evolve independently. Repository validation defines the accepted publisher contract; manual trials provide current compatibility evidence.
