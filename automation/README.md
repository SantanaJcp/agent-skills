# Automation

Scheduled jobs that keep a project honest without anyone asking.

| Job | When (default) | What it does |
|---|---|---|
| `bin/nightly-guard <project>` | daily 02:00 | Runs the project's steps on a dedicated clone of the shared branch. One GitHub issue while it is red, closed when green. Every run lands exactly once in `~/.local/state/kitchen/nightly/<project>.jsonl` for `kitchen status`. |
| `bin/weekly-gardener <project>` | Monday 06:00 | One unattended Claude Code run that commits at most one small, verified change on a local branch; the job then publishes it as a PR if it passes its checks. Skips while the last one is still open. |
| `bin/weekly-retro` | Monday 07:00 | Runs the `retro` skill over the week's transcripts and writes a report of proposals. Applies nothing. |

Schedule them with `bin/install-schedule <project>` and `bin/install-schedule --retro` (launchd on macOS).

## Project config

One file per project at `~/.config/kitchen/automation/<project>.env`, outside this public repo. `<project>` matches the project's folder name so `kitchen status` can find its history.

```bash
REPO_URL="git@github.com:owner/repo.git"
GH_REPO="owner/repo"
BRANCH="dev"
EXTRA_PATH="$HOME/.dotnet"            # tools launchd cannot find on its own
NEEDS_DOCKER=1
GUARD_LABEL="nightly-guard"
GARDENER_LABEL="gardener"
GUARD_STEPS=(                          # name|command, run in order; the first failure stops the run
  "build|make build"
  "tests|make test"
)
CLEANUP_CMD="make stop"                # optional
METRICS_CMD="python3 scripts/metrics.py --json"   # optional; snapshot per run in the history
QUALITY_CMD="python3 scripts/metrics.py"          # optional; what the gardener measures with
BASELINE_FILE="scripts/metrics.json"             # optional
HOOKS_PATH="scripts/hooks"             # optional; the project's hooks folder, kept working in the clone
LOCK_WAIT_SECONDS=3600                 # optional; how long a job waits for the other one before "skipped: busy"
GARDENER_MAX_CHANGED_LINES=400         # optional; larger gardener diffs are not published
GARDENER_PROTECTED_PATHS=(".github/*")  # optional; shell patterns the gardener may not touch
GARDENER_SANDBOX_DOMAINS=("api.nuget.org") # optional; domains the gardener's Bash may reach (default: none)
GARDENER_SANDBOX_READ=("$HOME/.dotnet") # optional; paths under $HOME its Bash may read (toolchains); the rest of $HOME is denied
GARDENER_SANDBOX_WRITE=("$HOME/.cache/kitchen/gardener/shop") # optional; paths outside the clone its Bash may read and write.
                                       # Give it caches of its own, never ones your own builds use (~/.nuget/packages,
                                       # ~/.npm): a package it plants there would run unsandboxed in your next build.
NUGET_PACKAGES="$HOME/.cache/kitchen/gardener/shop/nuget"  # not exported: reaches only the gardener, via GARDENER_ENV_PASS
GARDENER_ENV_PASS=(DOTNET_ROOT NUGET_PACKAGES)  # optional; extra variable names the agent's build needs
GARDENER_VERIFY_STEPS=(                # optional; name|command the job reruns on the final tree before publishing,
  "build|make build"                   # sandboxed like the agent (no Docker unless its socket is allowed)
  "tests|make unit-test"
)
GARDENER_VERIFY_TIMEOUT_SECONDS=3600   # optional; deadline for each verify step
GARDENER_SANDBOX_UNIX_SOCKETS=()       # optional; e.g. the Docker socket. Docker can mount any host path, so
                                       # allowing it reopens what the sandbox closes
GH_TIMEOUT_SECONDS=120                 # optional; deadline for every gh call
NET_TIMEOUT_SECONDS=600                # optional; deadline for clone, fetch and push
```

## Nightly record

One JSON line per run: `ts`, `started`, `sha` (full 40 characters), `status`, `failed_step`, `cleanup`, `metrics`, `warnings`, `run_id`, `log`. The line is written as `running` when the run starts and replaced when it ends.

| `status` | Meaning |
|---|---|
| `green` / `red` | The steps' verdict. Problems around it (`cleanup failed`, `metrics failed`, `issue report failed`) go to `warnings` and never change the verdict. |
| `running` | The run is in progress. |
| `incomplete` | Interrupted, aborted or timed out before a verdict; `failed_step` names the phase (a step, `sync`, `lock`). A `running` line left by a run killed with SIGKILL is closed as `incomplete` (`failed_step: killed`) by the next run. |
| `skipped: busy` | The other job of the project held the clone for `LOCK_WAIT_SECONDS`. |

Trial runs (`GUARD_ONLY=...`) are neither recorded nor reported.

## Guarantees

- Jobs work in their own clone; your checkout is never touched. One job at a time per project: each job runs under `lib/supervise.py`, which holds the project lock and runs the job in its own process group. When the job ends, however it ends, the group is stopped, then every process that still has its working directory or an open file in the clone or the gardener's work dirs (found with `lsof`, which also catches descendants that left the group with `setsid`) gets TERM, then KILL. If any survive, the run is recorded `incomplete` with `failed_step: survivors <pids>` and the project stays busy until they exit. Do not keep a shell or editor open inside the automation clone: the job stops it.
- Every gh call and every clone, fetch and push has a deadline, so a hung network call cannot hold a run or its record.
- A pre-push hook in the clone refuses pushes to `dev`, `main`, `master` and `$BRANCH`. The project's own hooks (`HOOKS_PATH`, or the hooks path the project configured in the clone) keep running next to it.
- The gardener's agent runs sealed. Its environment is an allowlist (`env -i` plus `HOME`, `USER`, `LOGNAME`, `SHELL`, `TMPDIR`, `LANG`, `LC_*`, `TERM`, the job's own variables, `GARDENER_ENV_PASS`, and `ANTHROPIC_API_KEY`/`CLAUDE_CODE_OAUTH_TOKEN` only when set, because claude then needs them to log in). Its shell is zsh with an empty `ZDOTDIR`: Claude Code re-applies the user's shell startup files to every Bash command, which would bring back their exports, functions and aliases. Toolchain variables the build needs go in `GARDENER_ENV_PASS`. No `gh` (a shim refuses every call), `GIT_SSH_COMMAND` and askpass refuse, git credential helpers cleared, `origin`'s push URL refused, no MCP servers.
- Its reads are an allowlist. Claude Code's `permissions.blockReadsOutsideWorkingDirectories` makes Read, Grep and Glob refuse anything outside the working directories, and its Bash runs in Claude Code's OS sandbox (`lib/sandbox_settings.py`, Seatbelt on macOS, `failIfUnavailable`, no unsandboxed escape) with all of `$HOME` denied and only the clone, the run's work dir, the metrics history and `GARDENER_SANDBOX_READ`/`GARDENER_SANDBOX_WRITE` re-opened. Credential locations stay denied even inside those, and git sees an identity-only config instead of `~/.gitconfig`. Bash writes only to the clone, the work dir and `GARDENER_SANDBOX_WRITE`; network only to `GARDENER_SANDBOX_DOMAINS`. The claude process itself stays outside, so its login and the model API work.
- It commits on `gardener/<date>-<slug>` and writes a PR summary. The job validates the branch's final tree (the only gardener branch, starts from `origin/$BRANCH`, has commits, within `GARDENER_MAX_CHANGED_LINES`, none of `GARDENER_PROTECTED_PATHS`, and no added line that looks like a credential: kitchen redaction patterns, known token shapes, or long random-looking strings, see `lib/scan_diff.py`) and publishes exactly that tree as ONE new commit on `origin/$BRANCH`, never the agent's history. Every check and the commit use SHAs pinned once (the base before Claude ran, the branch's commit and tree), never ref names that a leftover process could move.
- Before publishing, the job reruns `GARDENER_VERIFY_STEPS` itself on exactly the validated tree, written from the git objects by `lib/export_tree.py` (no `.gitattributes` such as `export-ignore`, no filters, no hooks, no symlink followed). Each step runs under `srt` (`@anthropic-ai/sandbox-runtime`, the runtime behind Claude Code's sandbox, pinned in `package.json`; `bin/install-schedule` installs it) with the agent's boundary from `lib/sandbox_settings.py --format srt` and its environment allowlist without the claude login, in `bash -e -o pipefail`. A step passes only when srt exits 0 and the step recorded exit 0 (srt reports a child killed by a signal as 0). A failing, killed or hung step publishes nothing. The PR body ends with the steps that passed, or says that none were configured and the only evidence is the agent's report. `srt` is a node script: `EXTRA_PATH` must reach `node` under launchd.
- Nothing the agent wrote runs unsealed afterwards, and no git command of the job reads the agent's git config or hooks. The agent works in a fresh clone of its own (`gardener/<run>/clone`, deleted at the end; the nightly's clone is never handed to it). The job lists its branch with `for-each-ref`, copies the objects into a bare repository of its own and re-hashes them with `git fsck`, then validates, verifies and pushes from there. Its settings, exports and PR text live in `gardener-job/<run>/`, which the agent cannot write, so nothing it plants in its work dir redirects the job's writes. The project's cleanup command runs in a fresh export of the pinned base.
- What content scanning can and cannot do: it catches accidental leaks (a token pasted into a file, also when split across lines). Encoded or deliberately disguised exfiltration (base64, hex, pieces spread around) is stopped only by the boundary: sandboxed reads that never reach the secrets, and an environment that never holds them. Otherwise it logs one `GARDENER-RESULT: refused - <reason>` line and exits 1.
- Log lines posted to GitHub issues and the gardener's PR text are redacted with the same secret patterns as `kitchen retro`.
- Nothing degrades silently: missing Docker fails the run, and a failed cleanup, metrics step or issue report is logged and recorded as a warning.
