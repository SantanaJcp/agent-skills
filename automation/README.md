# Automation

Scheduled jobs that keep a project honest without anyone asking.

| Job | When (default) | What it does |
|---|---|---|
| `bin/nightly-guard <project>` | daily 02:00 | Runs the project's steps on a dedicated clone of the shared branch. One GitHub issue while it is red, closed when green. Every run lands in `~/.local/state/kitchen/nightly/<project>.jsonl` for `kitchen status`. |
| `bin/weekly-gardener <project>` | Monday 06:00 | One unattended Claude Code run that opens at most one small, verified PR. Skips while the last one is still open. |
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
```

## Guarantees

- Jobs work in their own clone; your checkout is never touched.
- A pre-push hook in the clone refuses pushes to `dev`, `main` and `master`, and the `gh` shim refuses `pr merge` and `repo delete`.
- Nothing degrades silently: missing Docker fails the run, and a failed cleanup or metrics step is logged and recorded in the nightly history.
