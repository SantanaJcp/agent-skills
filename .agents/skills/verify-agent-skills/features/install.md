# install

- **Reached by:** `bin/kitchen install [--backup]`
- **Observable result:** skills (chef-mode among them) linked into ~/.claude/skills and ~/.agents/skills, the chef agent into ~/.claude/agents and ~/.codex/agents; no global rules or hooks; what older installs left moved aside or removed
- **Proved by:** tests/test_kitchen.py (InstallTests, ChefAgentTests), tests/test_setup.py (LegacyHookTests)
