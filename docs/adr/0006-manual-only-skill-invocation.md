# ADR 0006: Require explicit skill invocation

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

The initial suite exposed precise descriptions for model-driven routing. That
made every installed skill eligible for automatic selection and spent context
on discovery even when the user did not intend to enter one of the suite's
structured workflows. The owner now wants skill choice and timing to remain a
human action, just like stage transitions, decisions, publication, and commit.

Codex and Claude Code expose different invocation-policy controls. Claude Code
reads `disable-model-invocation` from `SKILL.md`; Codex reads
`policy.allow_implicit_invocation` from `agents/openai.yaml`.

## Decision

Every stable and incubating skill is manual-only:

- `SKILL.md` declares `disable-model-invocation: true` for Claude Code;
- `agents/openai.yaml` declares
  `policy.allow_implicit_invocation: false` for Codex;
- the publisher validator requires both declarations and the new-skill
  generator creates them by default.

Users invoke a chosen skill explicitly with `$skill-name` in Codex or
`/skill-name` in Claude Code. Descriptions remain marketplace and catalog copy
that helps humans choose a skill; they are no longer implicit-routing
contracts. The task workflow remains canonical in the portable `SKILL.md`.
The Codex sidecar is now a required compatibility adapter for invocation policy
as well as interface metadata.

This decision supersedes the presentation-only sidecar clause in ADR 0001 and
the implicit-invocation clause in ADR 0002. Their remaining decisions stand.

## Consequences

- Natural-language prompts do not activate suite skills, even when they match a
  skill's advertised use case.
- Explicit invocation remains available and preserves isolated installation of
  every self-contained skill.
- Removing `agents/openai.yaml` is no longer a supported Codex configuration for
  the manual-only promise.
- Manual client QA must verify both negative bare-prompt behavior and positive
  explicit invocation in each supported client.
- Historical `v1.0.0` implicit-routing evidence remains a valid record of that
  release, but it is not evidence for this new policy.
