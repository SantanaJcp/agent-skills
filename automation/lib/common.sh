#!/usr/bin/env bash
# Shared helpers for kitchen automation jobs. Usage: source common.sh <project>
# Config: ${KITCHEN_CONFIG:-~/.config/kitchen}/automation/<project>.env (private, never in this repo)
# State:  ${KITCHEN_STATE:-~/.local/state/kitchen}/automation/<project>/ and nightly/<project>.jsonl
set -euo pipefail

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

# A dedicated clone at the tip of $BRANCH; the developer's checkout is never touched.
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

# Automation may push its own branches, never the shared ones.
install_push_guard() {
  local hook="$CLONE_DIR/.git/hooks/pre-push"
  cat > "$hook" <<HOOK
#!/usr/bin/env bash
while read -r local_ref local_sha remote_ref remote_sha; do
  case "\$remote_ref" in
    refs/heads/dev|refs/heads/main|refs/heads/master)
      echo "kitchen automation: refusing to push to \$remote_ref" >&2; exit 1 ;;
  esac
done
exit 0
HOOK
  chmod +x "$hook"
  git -C "$CLONE_DIR" config core.hooksPath .git/hooks
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
record_nightly() { # status failed_step cleanup metrics sha run_id log
  python3 - "$NIGHTLY_RECORD" "$@" <<'PY'
import datetime, json, sys
record, status, failed, cleanup, metrics, sha, run_id, log = sys.argv[1:]
entry = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "sha": sha,
         "status": status, "failed_step": failed or None, "cleanup": cleanup, "metrics": metrics,
         "run_id": run_id, "log": log}
open(record, "a").write(json.dumps(entry) + "\n")
PY
}
