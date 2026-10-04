#!/usr/bin/env bash
# Shared helpers for kitchen automation jobs. Usage: source common.sh <project>
# Config: ${KITCHEN_CONFIG:-~/.config/kitchen}/automation/<project>.env (private, never in this repo)
# State:  ${KITCHEN_STATE:-~/.local/state/kitchen}/automation/<project>/ and nightly/<project>.jsonl
set -euo pipefail
# Jobs only ever work on their own clone; a GIT_DIR inherited from a git hook would redirect them.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_NAMESPACE

KITCHEN_AUTOMATION="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${1:?usage: <job> <project>}"
CONFIG_ROOT="${KITCHEN_CONFIG:-$HOME/.config/kitchen}"
STATE_ROOT="${KITCHEN_STATE:-$HOME/.local/state/kitchen}"
CONFIG="$CONFIG_ROOT/automation/$PROJECT.env"
[ -f "$CONFIG" ] || { echo "no config: $CONFIG" >&2; exit 2; }
# shellcheck source=/dev/null
source "$CONFIG"

STATE_DIR="$STATE_ROOT/automation/$PROJECT"
CLONE_DIR="$STATE_DIR/clone"
LOG_DIR="$STATE_DIR/logs"
HISTORY_DIR="$STATE_DIR/history"
NIGHTLY_RECORD="$STATE_ROOT/nightly/$PROJECT.jsonl"
mkdir -p "$LOG_DIR" "$HISTORY_DIR" "$(dirname "$NIGHTLY_RECORD")"

# launchd starts with a bare PATH. The shims go first so the gh wrapper wins;
# the wrapper calls the real gh found without the shims.
TOOL_PATH="${EXTRA_PATH:-}:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export KITCHEN_REAL_GH="${KITCHEN_REAL_GH:-$(PATH="$TOOL_PATH" command -v gh || true)}"
export PATH="$KITCHEN_AUTOMATION/shims:$TOOL_PATH"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

# Problems that did not change the verdict but must not hide: logged now, recorded with the run.
WARNINGS=()
warn() { WARNINGS+=("$1"); log "WARNING: $1"; }

# Secrets out of anything that leaves the machine (stdin to stdout).
redact() { python3 "$KITCHEN_AUTOMATION/lib/redact.py"; }

# One job at a time per project: the guard and the gardener share the clone that sync_clone resets.
# Waits up to LOCK_WAIT_SECONDS (default 3600) and returns 1 when the lock stays busy.
# The lock lives in a helper process, so it is released when the job exits, however it exits.
LOCK_HOLDER_PID=""
acquire_project_lock() {
  local answer="$STATE_DIR/.lock-answer.$$" word=""
  rm -f "$answer"
  python3 "$KITCHEN_AUTOMATION/lib/lock.py" "$STATE_DIR/job.lock" "${LOCK_WAIT_SECONDS:-3600}" "${LOCK_POLL_SECONDS:-5}" "$answer" \
    </dev/null >/dev/null 2>&1 &
  LOCK_HOLDER_PID=$!
  while [ ! -s "$answer" ] && kill -0 "$LOCK_HOLDER_PID" 2>/dev/null; do sleep 0.2; done
  if [ -s "$answer" ]; then word="$(cat "$answer")"; fi
  rm -f "$answer"
  [ "$word" = acquired ] && return 0
  wait "$LOCK_HOLDER_PID" 2>/dev/null || true
  LOCK_HOLDER_PID=""
  return 1
}

release_project_lock() {
  [ -n "$LOCK_HOLDER_PID" ] || return 0
  kill "$LOCK_HOLDER_PID" 2>/dev/null || true
  wait "$LOCK_HOLDER_PID" 2>/dev/null || true
  LOCK_HOLDER_PID=""
}

# A dedicated clone at the tip of $BRANCH; the developer's checkout is never touched.
# Destructive (reset and clean): call it only while holding the project lock.
sync_clone() {
  if [ ! -d "$CLONE_DIR/.git" ]; then
    git clone --quiet "$REPO_URL" "$CLONE_DIR"
  fi
  git -C "$CLONE_DIR" fetch --quiet --prune origin
  git -C "$CLONE_DIR" checkout --quiet --detach "origin/$BRANCH"
  git -C "$CLONE_DIR" reset --quiet --hard "origin/$BRANCH"
  git -C "$CLONE_DIR" clean --quiet -fdx -e node_modules
  install_push_guard
}

# Automation may push its own branches, never the shared ones. The project's own hooks keep working:
# core.hooksPath points at a kitchen folder that forwards every hook of the project's hooks folder
# (HOOKS_PATH in the config, else the clone's previous core.hooksPath, else .git/hooks) and puts the
# pre-push guard in front of the project's own pre-push.
install_push_guard() {
  local git_dir hooks_dir current project_hooks hook name
  git_dir="$(git -C "$CLONE_DIR" rev-parse --absolute-git-dir)"
  hooks_dir="$git_dir/kitchen-hooks"
  current="$(git -C "$CLONE_DIR" config --get core.hooksPath || true)"
  if [ -n "${HOOKS_PATH:-}" ]; then
    project_hooks="$HOOKS_PATH"
  elif [ -n "$current" ] && [ "$current" != "$hooks_dir" ]; then
    project_hooks="$current"
  else
    project_hooks="$git_dir/hooks"
  fi
  case "$project_hooks" in /*) ;; *) project_hooks="$CLONE_DIR/$project_hooks" ;; esac
  rm -rf "$hooks_dir"
  mkdir -p "$hooks_dir"
  for hook in "$project_hooks"/*; do
    [ -f "$hook" ] || continue
    name="$(basename "$hook")"
    case "$name" in *.sample|pre-push) continue ;; esac
    printf '#!/usr/bin/env bash\nhook=%q\n[ -x "$hook" ] || exit 0\nexec "$hook" "$@"\n' "$hook" > "$hooks_dir/$name"
    chmod +x "$hooks_dir/$name"
  done
  cat > "$hooks_dir/pre-push" <<HOOK
#!/usr/bin/env bash
input="\$(cat)"
while read -r local_ref local_sha remote_ref remote_sha; do
  case "\$remote_ref" in
    refs/heads/dev|refs/heads/main|refs/heads/master|$(printf %q "refs/heads/$BRANCH"))
      echo "kitchen automation: refusing to push to \$remote_ref" >&2; exit 1 ;;
  esac
done <<< "\$input"
hook=$(printf %q "$project_hooks/pre-push")
[ -x "\$hook" ] || exit 0
if [ -n "\$input" ]; then printf '%s\n' "\$input"; fi | "\$hook" "\$@"
HOOK
  chmod +x "$hooks_dir/pre-push"
  git -C "$CLONE_DIR" config core.hooksPath "$hooks_dir"
}

# Starts Docker Desktop on macOS when needed. Never pretends: returns 1 when Docker is not usable.
ensure_docker() {
  docker info >/dev/null 2>&1 && return 0
  if [ "$(uname)" = Darwin ]; then
    log "docker not running; starting Docker Desktop"
    if open -a Docker >/dev/null 2>&1; then
      for _ in $(seq 1 "${DOCKER_WAIT_TRIES:-60}"); do docker info >/dev/null 2>&1 && return 0; sleep "${DOCKER_WAIT_SECONDS:-5}"; done
    fi
  fi
  log "docker is not available"
  return 1
}

# Appends one run to the nightly history that `kitchen status` reads.
record_nightly() { # status failed_step cleanup metrics sha run_id log [warning...]
  python3 - "$NIGHTLY_RECORD" "$@" <<'PY'
import datetime, json, sys
record, status, failed, cleanup, metrics, sha, run_id, log, *warnings = sys.argv[1:]
entry = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "sha": sha or None,
         "status": status, "failed_step": failed or None, "cleanup": cleanup, "metrics": metrics,
         "warnings": warnings, "run_id": run_id, "log": log}
with open(record, "a") as handle:
    handle.write(json.dumps(entry) + "\n")
PY
}
