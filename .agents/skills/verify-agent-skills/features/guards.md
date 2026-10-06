# guards

- **Reached by:** `kitchen guards [repo] [--check]`
- **Observable result:** `.kitchen/hooks/` copies run from the repo's `.claude/settings.json` and `.codex/hooks.json`; each tool's handler blocks a push to main in that repo; `--check` fails on drift
- **Proved by:** tests/test_guards.py (GuardsTests)
