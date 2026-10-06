# install

- **Reached by:** `bin/kitchen install [--rules …] [--backup]`
- **Observable result:** skills linked into ~/.claude/skills and ~/.agents/skills, the generated rules file, the hooks merged
- **Proved by:** tests/test_kitchen.py (InstallTests), tests/test_setup.py
