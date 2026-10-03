# agent-skills

My personal agent kitchen: small, owned skills plus the tooling that keeps them honest, shared by Claude Code and Codex from one source.

> Built on ideas from [Poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack) and [Matt Pocock's skills](https://github.com/mattpocock/skills), rewritten small and owned. The previous Acta v2 suite is preserved at tag `acta-v2-final`.

## Layout

| Path | What lives there |
|---|---|
| `global/AGENTS.md` | Rules every session follows, in every project and tool |
| `skills/<name>/` | One skill per folder: a short `SKILL.md`, plus scripts when a step is mechanical |
| `bin/kitchen` | The CLI that installs and checks everything |
| `templates/` | Starting points for per-project pieces, such as a `verify-<repo>` skill |
| `automation/` | Scheduled jobs (nightly guard, weekly gardener) |
| `tests/` | The repo verifies itself |

Project-specific skills (deploy, verification for one app) stay in that project's `.agents/skills/`.

## Install

Requires Python 3.10+ and git. No other dependencies.

```bash
git clone https://github.com/SantanaJcp/agent-skills.git
cd agent-skills
bin/kitchen install   # symlinks skills and global rules into Claude Code and Codex
bin/kitchen doctor    # proves every link resolves and the pre-commit hook is active
```

`install` links each `skills/<name>` into `~/.claude/skills/` and `~/.agents/skills/`, and `global/AGENTS.md` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. It refuses to replace anything it does not manage; `--backup` moves those paths to `~/.kitchen-backups/` first.

## Check

```bash
bin/kitchen check     # lint skills, scan for private data, run the tests
```

The pre-commit hook runs the same command. Because this repo is public, `check` rejects personal absolute paths and any term listed in `~/.config/kitchen/denylist.txt` (one term per line, kept outside the repo).

## License

Apache-2.0
