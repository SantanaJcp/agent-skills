# Working on this repo

This file is for agents editing the kitchen itself. `PRINCIPLES.md` says what the kitchen does and why; read it before you change a control. The owner's rules for every session live in `global/AGENTS.md`.

## Rules

- The repo is public. Never commit personal absolute paths, client or project names, credentials, or machine-specific config. Per-machine config lives in `~/.config/kitchen/`.
- `bin/kitchen` and `lib/`: Python 3.11+ standard library only. CLI code lives in `lib/kitchen/`; `bin/kitchen` only wires commands.
- `hooks/`: Python that also runs on the system `python3` (3.9+), or POSIX sh.
- `automation/`: bash and `lsof`. Its one package is `srt`, pinned in `automation/package.json` (Node.js; on Linux also bubblewrap, socat and ripgrep). Add no other dependency.
- A skill is a workflow, not a manual: `SKILL.md` stays under 150 lines (`bin/kitchen check` enforces it). Move mechanical steps into a script inside the skill and detail into a referenced file.
- Skill names and descriptions are English and kebab-case; the folder name equals the frontmatter `name`; descriptions are one line.
- Prefer the strongest fix for a recurring mistake: make it impossible in code, then a check in `bin/kitchen check`, then a rule here.
- Every control (a guard, a scheduled job, a CLI module that decides PASS, FAIL or unknown, a must-have of `kitchen init`, a skill) names the principles it enforces in a `Principles:` line, and a new one is added to the list in `tests/test_principles.py`. A new principle goes in `PRINCIPLES.md` with an `Enforced by:` line.

## Verify

- `bin/kitchen check` lints skills, scans for private data and runs `tests/`. The pre-commit hook runs `bin/kitchen check --fast` (only the tests the staged paths need); run the plain command before you push. Never bypass the hook with `--no-verify`.
- Every guard in `hooks/` has cases in `tests/corpus/hooks/cases.json`. An evasion a guard cannot catch goes in as a `known-limit` case.
- `bin/kitchen doctor` checks the real installation on this machine.
- Tests use a throwaway repo and `HOME` (`KITCHEN_REPO`, `HOME`, `KITCHEN_DENYLIST`, `KITCHEN_STATE`, `KITCHEN_CONFIG`); never let a test touch the real `~/.claude`, `~/.codex`, `~/.agents` or `~/.config/kitchen`.
- A behavior change ships with a test that fails without it.
