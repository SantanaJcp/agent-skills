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

Requires Python 3.11+ and git; `gh` for pull-request status. No other dependencies.

```bash
git clone https://github.com/SantanaJcp/agent-skills.git
cd agent-skills
bin/kitchen install   # symlinks skills and global rules into Claude Code and Codex
bin/kitchen doctor    # proves every link resolves and the pre-commit hook is active
```

`install` links each `skills/<name>` into `~/.claude/skills/` and `~/.agents/skills/`, and `global/AGENTS.md` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. It refuses to replace anything it does not manage; `--backup` moves those paths to `~/.kitchen-backups/` first.

## Daily use

```bash
kitchen status              # every project: branch, upstream, PRs, nightly guard, agent checkpoints, owed decisions
kitchen log "msg" --status done|blocked|decision|note   # agents leave checkpoints during autonomous runs
kitchen inventory           # skills, rule files and Codex automations the agents can see, and where copies drift
kitchen retro --since 7d    # my prompts from Claude Code and Codex, for the retro skill
kitchen integrate fix/a fix/b --base main   # merge in order in a disposable clone, run the project's checks after each merge
```

`integrate` reads check commands from `~/.config/kitchen/integrate.toml` (`[projects.<repo folder>]` with `checks = [...]`, optional `base` and `path`), prints PASS or FAIL bound to the exact SHA vector, and records it in `~/.local/state/kitchen/integrate/`. `kitchen integrate <refs> --recorded` runs nothing and passes only if a recorded PASS matches the refs' current SHAs, so any moved HEAD invalidates it. Nothing it runs inherits `GIT_*`.

`status` shows `unknown` whenever a git read fails, never a zero; it groups `kitchen log` checkpoints by repository, so a checkpoint logged from a worktree shows under its repo. `retro` keeps only messages I typed: it classifies each one by provenance (Claude `origin`, `promptSource`, `entrypoint`, synthetic replays and agent-launched `claude -p` sessions; Codex `originator`, `source`, `thread_source` and heartbeat automations), ends with one coverage line of included and excluded counts by reason, and `--include-automated` shows the excluded ones tagged with their reason.

Per-machine config lives outside the repo, in `~/.config/kitchen/`: `projects.txt` (one project path per line) and `denylist.txt`. State (journal, nightly history, retro reports) lives in `~/.local/state/kitchen/`.

## Skills

| Skill | Use it when | Invocation |
|---|---|---|
| `make-me-realize` | Before designing: settle open decisions through numbered questions | manual |
| `feature-xray` | "Primero analicemos": read-only investigation that ends in decisions | automatic |
| `find-the-cause` | Something is broken and the cause is unknown | automatic |
| `second-opinion` | Before merging: cross-model review with triaged findings | automatic |
| `handoff` | Passing work to another agent, tool or session | manual |
| `retro` | Weekly: turn repeated corrections into environment fixes | manual |
| `wait-what` | The last answer did not land | manual |
| `audit-verification` | Periodically: prove a project's verify skill still tells the truth | manual |

Manual skills are invoked with `/name` in Claude Code and `$name` in Codex; `kitchen check` keeps that flag identical in both.

## Check

```bash
bin/kitchen check     # lint skills, scan for private data, run the tests
```

The pre-commit hook runs the same command. Because this repo is public, `check` rejects personal absolute paths, credential shapes (GitHub, Slack, AWS and OpenAI-style tokens, JWTs, private key blocks, literal password or secret assignments) and any term listed in `~/.config/kitchen/denylist.txt` (one term per line, kept outside the repo). It scans the working tree and the exact staged blobs, so a secret staged and then deleted from the working file still fails.

Each detector (credentials, private terms, retro provenance) is tested against its attack corpus in `tests/corpus/<detector>/cases.json`: positive, negative and bypass cases, read by detection and redaction alike. A miss found in review becomes a new bypass case.

## License

Apache-2.0
