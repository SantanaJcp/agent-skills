# Agent Instructions

## Repository contract

- Treat `skills/` as the stable public collection and `incubator/` as experimental work.
- Create new skills with `npm run new:skill -- <name>`; never import or scan personal skill directories.
- Keep every skill self-contained and portable across current stable Codex and Claude Code.
- Skill scripts must be `.mjs` files that use Node built-ins or relative bundled modules only.
- Do not add symlinks, opaque executables, secrets, hidden install-time behavior, or undeclared external tools.
- Edit canonical skill metadata, then regenerate catalogs with `npm run catalog`.
- Run `npm run check` before declaring work complete.

## Generated files

`CATALOG.md` and `INCUBATOR.md` are generated. Do not edit them directly.

## Agent skills

### Issue tracker

Public work is tracked in GitHub Issues. `.scratch/` is an optional ignored
local drafting area and is never repository state. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical triage labels without overrides. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository using root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
