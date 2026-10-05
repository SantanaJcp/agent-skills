# agent-skills

My personal agent kitchen: small, owned skills plus the tooling that keeps them honest, shared by Claude Code and Codex from one source.

> Built on ideas from [Poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack) and [Matt Pocock's skills](https://github.com/mattpocock/skills), rewritten small and owned. The previous Acta v2 suite is preserved at tag `acta-v2-final`.

## Layout

| Path | What lives there |
|---|---|
| `global/AGENTS.md` | Rules every session follows, in every project and tool |
| `skills/<name>/` | One skill per folder: a short `SKILL.md`, plus scripts when a step is mechanical |
| `bin/kitchen` | The CLI that installs and checks everything |
| `hooks/` | Agent guards, run by Claude Code and Codex before every shell command |
| `templates/` | Starting points for per-project pieces, such as a `verify-<repo>` skill |
| `automation/` | Scheduled jobs (nightly guard, weekly gardener) |
| `tests/` | The repo verifies itself |

Project-specific skills (deploy, verification for one app) stay in that project's `.agents/skills/`.

## Install

What each part needs:

| Part | Needs |
|---|---|
| `bin/kitchen`, `lib/` | Python 3.11+ (standard library only) and git; `gh` for pull-request status |
| `hooks/` | `python3` on PATH (3.9+; macOS's `/usr/bin/python3` works) |
| `automation/` | bash and `lsof`; launchd on macOS, systemd user timers on Linux. The gardener's sandbox is `srt`, a Node package pinned in `automation/package.json`: Node.js, then `npm ci --ignore-scripts --prefix automation`. On Linux `srt` also needs bubblewrap, socat and ripgrep |

The automation tests need `srt` too: without it `kitchen check` stops with that one `npm ci` line.

```bash
git clone https://github.com/SantanaJcp/agent-skills.git
cd agent-skills
bin/kitchen install   # symlinks skills and global rules into Claude Code and Codex
bin/kitchen doctor    # proves links, agent hooks, agent CLIs, automation tools and schedules
```

`install` links each `skills/<name>` into `~/.claude/skills/` and `~/.agents/skills/`, and `global/AGENTS.md` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. It refuses to replace anything it does not manage; `--backup` moves those paths to `~/.kitchen-backups/` first.

It also merges the agent hooks into `~/.claude/settings.json` and `~/.codex/hooks.json`: it adds one `PreToolUse` group on Bash that runs each script in `hooks/`, and keeps every other setting and hook in those files. A file it cannot parse is refused; `--backup` moves it aside and writes one with only the kitchen hooks. Codex runs a new hook only after you trust it in `/hooks`.

`doctor` fails when a link or a hook is missing, a hook is disabled, or a guard does not block its probe command. It warns when `claude` or `codex` is not on PATH, when automation is configured but `node` or `srt` is missing, and when a kitchen LaunchAgent plist is present but not loaded (macOS) or a kitchen timer is not active (Linux).

## Agent hooks

Three rules that used to be text are now guards. Each one blocks with a message that says what to do instead:

| Guard | Blocks |
|---|---|
| `deny-no-verify` | `git commit --no-verify` or `-n`, `--no-verify` on push, merge and other hooked commands, and a `core.hooksPath` override on the command line |
| `deny-shared-push` | `git push` to `dev`, `main`, `master` or a branch listed in `~/.config/kitchen/shared-branches.txt` (names or globs), including a bare `git push` from such a branch, `--all` and `--mirror` |
| `deny-recursive-rm` | recursive `rm` on anything outside `/tmp` or `$TMPDIR`; use `trash <path>` instead |

They read through `VAR=x` prefixes, `command`, `env`, `sudo`, `xargs`, `find -exec`, `sh -c`, `eval`, subshells, `$(...)` and heredocs. The attack corpus in `tests/corpus/hooks/cases.json` lists what each guard blocks, what it allows, and the evasions it cannot see (git aliases, scripts in files, commands piped into a shell), so a gap is written down, not hidden. A guard that cannot read its input blocks rather than passing silently.

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
bin/kitchen check          # lint skills, scan for private data, run every test
bin/kitchen check --fast   # the same lint and scan, plus only the tests the staged paths need
```

The pre-commit hook runs `check --fast`: a docs-only commit runs no tests, and the automation suite (about 95 s of the run) runs only when `automation/`, `lib/` or `tests/test_automation.py` is staged. It prints each module it skips. Plain `check` and `integrate` still run everything. Because this repo is public, `check` rejects personal absolute paths, credential shapes (GitHub, Slack, AWS and OpenAI-style tokens, JWTs, private key blocks, literal password or secret assignments) and any term listed in `~/.config/kitchen/denylist.txt` (one term per line, kept outside the repo). It scans the working tree and the exact staged blobs, so a secret staged and then deleted from the working file still fails.

Each detector (credentials, private terms, retro provenance, the agent hooks) is tested against its attack corpus in `tests/corpus/<detector>/cases.json`: positive, negative and bypass cases, read by detection and redaction alike. A miss found in review becomes a new bypass case.

## License

Apache-2.0
