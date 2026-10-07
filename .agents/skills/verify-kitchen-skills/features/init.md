# init

- **Reached by:** `kitchen init [repo]`, or `/chef-mode init` in the repo
- **Observable result:** the init playbook printed for the person's agent, with the repo and the kitchen path; nothing written
- **Proved by:** tests/test_guards.py (InitTests, RealPlaybookTests)
