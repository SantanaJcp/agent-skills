# Working on this repo

This file is for agents editing the kitchen itself. The rules every session follows everywhere live in `global/AGENTS.md`.

## Rules

- The repo is public. Never commit personal absolute paths, client or project names, credentials, or machine-specific config. Per-machine config lives in `~/.config/kitchen/`.
- Python 3.11+ standard library and POSIX sh only. No package managers, no Node. CLI code lives in `lib/kitchen/`; `bin/kitchen` only wires commands.
- A skill is a workflow, not a manual: `SKILL.md` stays under 150 lines (`bin/kitchen check` enforces it). Move mechanical steps into a script inside the skill and detail into a referenced file.
- Skill names and descriptions are English and kebab-case; the folder name equals the frontmatter `name`; descriptions are one line.
- Prefer the strongest fix for a recurring mistake: make it impossible in code, then a check in `bin/kitchen check`, then a rule here.

## Verify

- `bin/kitchen check` lints skills, scans for private data and runs `tests/`. The pre-commit hook runs it; never bypass it with `--no-verify`.
- `bin/kitchen doctor` checks the real installation on this machine.
- Tests use a throwaway repo and `HOME` (`KITCHEN_REPO`, `HOME`, `KITCHEN_DENYLIST`, `KITCHEN_STATE`, `KITCHEN_CONFIG`); never let a test touch the real `~/.claude`, `~/.codex`, `~/.agents` or `~/.config/kitchen`.
- A behavior change ships with a test that fails without it.
