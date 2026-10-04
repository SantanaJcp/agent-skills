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
```

## Nightly record

One JSON line per run: `ts`, `sha` (full 40 characters), `status`, `failed_step`, `cleanup`, `metrics`, `warnings`, `run_id`, `log`.

| `status` | Meaning |
|---|---|
| `green` / `red` | The steps' verdict. Problems around it (`cleanup failed`, `metrics failed`, `issue report failed`) go to `warnings` and never change the verdict. |
| `incomplete` | Interrupted or aborted before a verdict; `failed_step` names the phase (a step, `sync`, `lock`). |
| `skipped: busy` | The other job of the project held the clone for `LOCK_WAIT_SECONDS`. |

Trial runs (`GUARD_ONLY=...`) are neither recorded nor reported. A run killed with SIGKILL cannot write its record.

## Guarantees

- Jobs work in their own clone; your checkout is never touched. One job at a time per project: the guard and the gardener take a lock before touching the clone, released when the job exits, however it exits.
- A pre-push hook in the clone refuses pushes to `dev`, `main`, `master` and `$BRANCH`. The project's own hooks (`HOOKS_PATH`, or the hooks path the project configured in the clone) keep running next to it.
- The gardener's agent runs sealed: no `gh` (a shim refuses every call), no GitHub tokens, no SSH agent, `GIT_SSH_COMMAND` and askpass refuse, git credential helpers cleared, `origin`'s push URL refused. It commits on `gardener/<date>-<slug>` and writes a PR summary. The job then pushes that branch and opens the PR with the gardener label only when it is the only gardener branch, starts from `origin/$BRANCH`, has commits, stays within `GARDENER_MAX_CHANGED_LINES` and touches none of `GARDENER_PROTECTED_PATHS`. Otherwise it logs one `GARDENER-RESULT: refused - <reason>` line and exits 1.
- The seal is environment-level, not an OS sandbox: it stops the agent's ordinary tools from publishing, but a process running as you could still reach your keychain or SSH keys on purpose.
- Log lines posted to GitHub issues and the gardener's PR text are redacted with the same secret patterns as `kitchen retro`.
- Nothing degrades silently: missing Docker fails the run, and a failed cleanup, metrics step or issue report is logged and recorded as a warning.
