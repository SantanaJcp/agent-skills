# install

- **Reached by:** `bin/kitchen install [--backup]`
- **Observable result:** skills (chef-mode among them) linked into ~/.claude/skills and ~/.agents/skills; no global rules, hooks or agents; what older installs left moved aside or removed
- **Proved by:** tests/test_kitchen.py (InstallTests), tests/test_setup.py (LegacyHookTests)
