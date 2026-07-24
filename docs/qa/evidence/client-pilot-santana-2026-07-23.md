# Acta v2 client activation pilot — Santana — 2026-07-23

Status: complete — partial scope passed

## Provenance

- Reviewer: Codex-directed local client automation for Santana
- Source revision: `74a3653240fe8272ae4d45c992831487d2580418`
- Harness variant: `with-sidecars`
- Harness policy: a fresh disposable copy per client; no prior `.agent-work`
- Test date: 2026-07-23
- Operating system: macOS 26.5.2
- Codex: `codex-cli 0.144.1`
- Claude Code: `2.1.206`, model `claude-sonnet-5`
- Browser and assistive technology: not tested in this record

Both clients received the exact committed prompt without a skill name. Codex
ran with `--ephemeral --ignore-user-config`; Claude Code ran with
`--no-session-persistence --setting-sources project`. Claude reported no MCP
servers, no plugins, and no permission denials. The disposable harness allowed
normal synthetic artifact writes.

## Client activation results

| Case | Client | Expected | Observed | Verdict |
| --- | --- | --- | --- | --- |
| `make-me-realize` trigger 1 | Codex | Activate `make-me-realize`, inspect the protocol, and begin discovery rather than design | Named and read `make-me-realize/SKILL.md`, read `references/acta-protocol.md`, created a draft `realization.md`, and opened a dependency-ordered first question round | Pass |
| `make-me-realize` trigger 1 | Claude Code | Activate `make-me-realize`, inspect the protocol, and begin discovery rather than design | Invoked the `Skill` tool with `make-me-realize`, read `references/acta-protocol.md`, and opened grounding questions without proposing a solution | Pass |

Exact prompt:

> I have a fuzzy idea for changing our onboarding. Help me uncover what I have not considered before we design it.

Claude Code cost for the clean pilot was US$0.1785854. This value is recorded
for budgeting only and is not a quality metric.

## Defects and supersession

- Defects found in the skill behavior: none in this assigned pilot.
- Evidence superseded: none.
- New source revision required: no.

An earlier exploratory invocation loaded personal plugins and denied required
writes; it was rejected as invalid test setup and led to the CLI-isolation
requirements now committed in the evaluator runbook. It is not counted as
skill evidence.

## Reviewer verdict

The assigned two-client pilot passes. This record proves only one positive
trigger in each client. It is not sufficient for suite promotion: the remaining
trigger/non-trigger cases, collisions, portable variant, core cycle, browsers,
and accessibility remain pending.
