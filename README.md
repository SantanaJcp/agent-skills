# agent-skills

My personal agent kitchen: small, owned skills plus the tooling that keeps them honest, shared by Claude Code and Codex from one source.

> Built on ideas from [Poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack) and [Matt Pocock's skills](https://github.com/mattpocock/skills), rewritten small and owned. The previous Acta v2 suite is preserved at tag `acta-v2-final`.

## Layout

| Path | What lives there |
|---|---|
| `PRINCIPLES.md` | What we do and why: the 13 principles every rule, hook and check points at (pstack's 24 folded in) |
| `global/AGENTS.md` | The kitchen owner's own rules; each person can install their own instead |
| `decisions.md` | Decisions about the kitchen that outlive a session |
| `skills/<name>/` | One skill per folder: a short `SKILL.md`, plus scripts when a step is mechanical |
| `bin/kitchen` | The CLI that installs and checks everything |
| `hooks/` | Agent guards, run by Claude Code and Codex before every shell command |
| `templates/` | Starting points for per-project pieces: a `verify-<repo>` skill, and what `kitchen init` writes |
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
bin/kitchen install   # links skills and hooks, writes your rules plus the principles index for Claude Code and Codex
bin/kitchen doctor    # proves links, agent hooks, agent CLIs, automation tools and schedules
```

`install` links each `skills/<name>` into `~/.claude/skills/` and `~/.agents/skills/`, and writes `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`: your own rules, then one line per principle from `PRINCIPLES.md`. Codex reads one global file and has no include, so this file is generated, not linked: edit the sources and rerun `install` (`doctor` fails while a copy is stale). Whose rules: `--rules <absolute path>`, `--rules global` (this kitchen's `global/AGENTS.md`) or `--rules none`, remembered in `~/.config/kitchen/rules.txt`; a terminal asks, and without a choice it uses `global/AGENTS.md` and says so. In a terminal it ends by offering `kitchen init` for all the repos in your `projects.txt`, one, or none; never automatically. It refuses to replace anything it does not manage; `--backup` moves those paths to `~/.kitchen-backups/` first.

It also merges the agent hooks into `~/.claude/settings.json` and `~/.codex/hooks.json`: it adds one `PreToolUse` group on Bash that runs each script in `hooks/`, and keeps every other setting and hook in those files. A file it cannot parse is refused; `--backup` moves it aside and writes one with only the kitchen hooks. Codex runs a new hook only after you trust it in `/hooks`.

`doctor` fails when a link or a hook is missing, a hook is disabled, or a guard does not block its probe command. It warns when `claude` or `codex` is not on PATH, when automation is configured but `node` or `srt` is missing, and when a kitchen LaunchAgent plist is present but not loaded (macOS) or a kitchen timer is not active (Linux).

## Agent hooks

Three rules that used to be text are now guards. Each one blocks with a message that says what to do instead:

| Guard | Blocks |
|---|---|
| `deny-no-verify` | `git commit --no-verify` or `-n`, `--no-verify` on push, merge and other hooked commands, a `core.hooksPath` or `include.*` override on the command line, and options that come from a variable, a command output or `xargs` |
| `deny-shared-push` | `git push` to `dev`, `main`, `master` or a branch listed in `~/.config/kitchen/shared-branches.txt` (names or globs), including a bare `git push` from such a branch, `--all` and `--mirror`. A push whose destination cannot be known statically blocks too: the matching refspec `:`, abbreviated options, arguments from `xargs`, or a `-c`/`GIT_CONFIG_*` that sets `push.*`, `remote.*`, `branch.*` or `include.*` |
| `deny-recursive-rm` | recursive `rm` on anything outside `/tmp` or `$TMPDIR`; use `trash <path>` instead |

They read through `VAR=x` prefixes, `command`, `env`, `sudo`, `xargs`, `find -exec`, `sh -c`, `eval`, subshells, `$(...)` and heredocs. The attack corpus in `tests/corpus/hooks/cases.json` lists what each guard blocks, what it allows, and the evasions it cannot see (git aliases, scripts in files, commands piped into a shell), so a gap is written down, not hidden. A guard that cannot read its input, parse the command or even load blocks with exit 2 (the only code both tools treat as a block) rather than passing silently.

## Daily use

```bash
kitchen status              # every project: branch, upstream, PRs, nightly guard, gardener, agent checkpoints, owed decisions
kitchen status --exceptions # only the lines that are not green; exits 1 when there are any
kitchen log "msg" --status done|blocked|decision|note   # agents leave checkpoints during autonomous runs
kitchen inventory           # skills, rule files and Codex automations the agents can see, and where copies drift
kitchen retro --since 7d    # my prompts from Claude Code and Codex, for the retro skill
kitchen models              # which model reviews each author's work; `kitchen models set reviewer --author claude ...` to change it
kitchen integrate fix/a fix/b --base main   # merge in order in a disposable clone, run the project's checks after each merge
kitchen init ../some-repo          # set one repo up: shows what is missing, asks numbered questions, writes only what you answer yes to
kitchen init --check ../some-repo  # read-only: what a repo is missing for a trustworthy agent loop
kitchen init ../some-repo --yes --base dev [--prove]   # the same without a terminal (an agent): recommended answers; --prove RUNS repo code
```

`integrate` reads check commands from `~/.config/kitchen/integrate.toml` (`[projects.<repo folder>]` with `base`, `checks = [...]` and optional `path`), prints PASS or FAIL bound to the exact SHA vector, and records it in `~/.local/state/kitchen/integrate/` with a digest of everything that decides what runs (checks, `path`, the base and every other key of the project's entry except `gardener`). There is no default base: without `base` or `--base` it fails. `kitchen integrate <refs> --recorded` runs nothing and passes only if a recorded PASS matches the refs' current SHAs and that digest as configured now, so any moved HEAD or changed check configuration invalidates it. Nothing it runs inherits `GIT_*`.

`init` is per repo, never automatic. It checks what the repo is missing, then asks, each with a recommended answer: write the missing pieces on branch `kitchen/init` (the shared layer, what the team and cloud sessions get); prove that branch's gate; add the repo to your kitchen (the personal layer: `projects.txt`, and `integrate.toml` with the base and `bin/check integrate`). Enter takes the recommendation. Without a terminal it asks nothing and writes nothing: it prints the questions and exits 2, so an agent answers with `--yes` (the recommendations, never repository code), `--prove` and `--base`. An unknown base is asked, or refused under `--yes`, never guessed. The personal layer only appends; a config file it cannot parse is an error. `init` does the mechanical part; what only judgment can fill (this project's real check commands, the verify skill, the proposals) it hands to an agent: while anything is left, it ends with the exact prompt to give one, which loops on `kitchen init . --yes --prove` until the gate is green and the planted defect turns it red, then opens a pull request. A `--prove` run with nothing new to write still updates `KITCHEN-INIT.md`, so the branch never keeps an old verdict.

`init --check` only reads files, git metadata and GET-only `gh api` calls (15 s timeout); it never runs a hook, a package script or `bin/check`. It reports the stacks (.NET, Node, Python; anything else is `unsupported`), each component's lockfile and lint config, hooks, agent files and CI, then eleven must-haves as PASS, FAIL or unknown with the file or command that proves each: a check contract (`bin/check` declaring the tiers commit, integrate, nightly and verify-tree, or `.kitchen/checks.toml`), an active pre-commit hook, an AGENTS.md under 200 lines that names the verify command, a verify skill with a feature-map guard, `decisions.md`, a secret scan in the hook, a baseline checked by a gate, project skills linked into `.claude/skills`, a required status on the shared branch (unknown, never PASS, without gh), the agent guards traveling with the repo (`.kitchen/hooks/` identical to this kitchen's, run from `.claude/settings.json`), and the principles traveling with it (`.kitchen/PRINCIPLES.md` identical to this kitchen's, named in AGENTS.md or CLAUDE.md). The exit code is the number of must-haves not PASS (64 when the path is not a git repo); `--json` gives the same report for machines.

The branch is built from git objects only: no worktree, no checkout, nothing written to your checkout or index. It adds, from `templates/init` and `templates/verify`, only the files that are missing: `decisions.md` (the one-way doors as owed `- [ ]`), `bin/check` with the tiers and `--list` filled from the manifests (every command marked `unverified`, and a tier with no command fails), `.githooks/pre-commit` (gitleaks on the staged changes, then `bin/check commit` unless only docs are staged), a verify-skill skeleton, a measure-only `.kitchen/baseline.json`, and the kitchen's guards in `.kitchen/hooks/` with a `.claude/settings.json` that runs each one and blocks when the copy is missing while that file is present (a session that loaded the settings and then switched to a branch from before init is not locked out; the guards installed for the person still run). Claude Code loads that file in a session started at the repo root (measured); Codex loaded no project hooks when measured, so a Codex session has the guards only where `kitchen install` ran. It never overwrites a file the owner wrote or edited: an incomplete must-have becomes a proposal in the report. The one exception follows the kitchen: a copy of the kitchen's own files (`.kitchen/hooks/`, `.kitchen/PRINCIPLES.md`) that init wrote and nobody has edited since (its bytes and mode match what an untouched `.kitchen/init.json` recorded) is refreshed when the kitchen's version changes; an edited copy is left alone and reported. It also proposes `.kitchen/PRINCIPLES.md`, and the line that names it in AGENTS.md, which init does not write. `.kitchen/init.json` records each generated file's sha256, so a rerun leaves the owner's edits and deletions alone and commits nothing when there is nothing new. The report is printed and committed as `KITCHEN-INIT.md`, with the one-way doors as numbered decisions and their commands, never executed. A symlink, submodule or file in the way of a path, or a symbolic `kitchen/init`, is refused; the branch moves once, against its expected old value. Every git command uses an empty `core.hooksPath`; nothing is pushed and no GitHub setting changes.

`--prove` runs repository code. It is the only mode that checks out a temporary worktree (where the repo's git filters may run), at the proposal's commit: `bin/check commit` twice (green and stable), then a negative control (a syntax error appended to the first tracked test file, else source file) that must turn it red with output naming that file, then the revert, which must be green again; and the proposed hook against a docs-only commit and a staged, randomly generated fake key. Anything else is reported `untrusted`, with the reason, and the exit code is 1. SIGTERM, SIGINT or SIGHUP kill the check's process group, remove the worktree and exit 128 + the signal number. The code's temp files go to a scratch directory that is removed afterwards; tool caches under `HOME` (npm, NuGet) are not contained.

`status` starts with the installed rule files: `fresh`, or each file that is missing or stale since `kitchen install` (an exception for `--exceptions`, so an edited rule that never reached the agents shows up). It shows `unknown` whenever a read fails, never a zero or `none` (the `gh` call has a deadline, `KITCHEN_GH_TIMEOUT_SECONDS`, default 15). It reads `decisions.md` from the project's `base` in `integrate.toml` and names the ref, shows how far the nightly's SHA is behind that base, counts the green streak in nights, marks a nightly older than 24 hours `overdue`, and shows the gardener's last result and its age from the local record, `overdue` when it is older than 8 days (weekly plus a day of grace). Nightly, gardener and decisions count only when explicit config says the project has them: the nightly when `~/.config/kitchen/automation/<project>.env` leaves at least one `GUARD_STEPS` step (a gardener-only host sets `GUARD_STEPS=()`), the gardener when it leaves at least one `GARDENER_VERIFY_STEPS` step or the `integrate.toml` entry has a `gardener` key, decisions when the entry has a `base`. Without that config the line says `not configured`, neither green nor an exception, so `--exceptions` stays quiet for a project that never had them. A configured one without its record is an exception. To count the steps, `status` sources the env the way the jobs do: bash under `set -euo pipefail`, launchd's `PATH=/usr/bin:/bin`, no stdin, a deadline (`KITCHEN_ENV_TIMEOUT_SECONDS`, default 5). Whatever the env runs, `status` runs too, as the jobs already do every night. An env that cannot be read, exits non-zero or misses the deadline is `unknown`. A project whose gardener runs on another host says so with `gardener = "remote:<host-label>"` in its `integrate.toml` entry, and the line becomes `remote (<host-label>): not read here`, which is neither green nor an exception. It groups `kitchen log` checkpoints by repository, so a checkpoint logged from a worktree shows under its repo, and lists the ones of no listed project under `unattached`. `kitchen log --status blocked|decision` also shows a local notification (osascript on macOS, notify-send on Linux; with neither it says so), redacted, never sent anywhere else. `retro` keeps only messages I typed: it classifies each one by provenance (Claude `origin`, `promptSource`, `entrypoint`, synthetic replays, agent-launched `claude -p` sessions, and messages an agent sent through a T3 Code tool (`t3_thread_launch`, `create_threads`, `delegate_task`, `t3_thread_send`), matched per message so the owner's follow-ups in that thread still count; Codex `originator`, `source`, `thread_source` and heartbeat automations), ends with one coverage line of included and excluded counts by reason, and `--include-automated` shows the excluded ones tagged with their reason.

`models` is each person's own setup, in `~/.config/kitchen/models.toml`. One role today, `reviewer`, set per author family (`--author claude` means the work is Claude's, so the reviewer runs on Codex), with provider, model (`default` for the tool's own), effort and tier; another role is added when a workflow reads it. An unset role fails with the command that sets it; a reviewer on the author's own provider is refused; `get --command` prints the `codex exec` or `claude -p` call. `second-opinion` takes its reviewer from here: through `delegate_task` in T3 Code, the other CLI elsewhere, BLOCKED where the other provider cannot be reached.

Per-machine config lives outside the repo, in `~/.config/kitchen/`: `projects.txt` (one project path per line), `denylist.txt`, `rules.txt` and `models.toml`. State (journal, nightly history, retro reports) lives in `~/.local/state/kitchen/`.

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

The pre-commit hook runs `check --fast`: a docs-only commit runs only `tests/test_principles.py` (under a second: every control names a principle that exists), and the automation suite (about 95 s of the run) runs only when `automation/`, `lib/` or `tests/test_automation.py` is staged. It prints each module it skips. Plain `check` and `integrate` still run everything. Because this repo is public, `check` rejects personal absolute paths, credential shapes (GitHub, Slack, AWS and OpenAI-style tokens, JWTs, private key blocks, literal password or secret assignments) and any term listed in `~/.config/kitchen/denylist.txt` (one term per line, kept outside the repo). It scans the working tree and the exact staged blobs, so a secret staged and then deleted from the working file still fails.

Each detector (credentials, private terms, retro provenance, the agent hooks) is tested against its attack corpus in `tests/corpus/<detector>/cases.json`: positive, negative and bypass cases, read by detection and redaction alike. A miss found in review becomes a new bypass case.

## License

Apache-2.0
