#!/bin/sh
# Pre-commit gate. Git runs it only after, in each clone:
#   git config core.hooksPath .githooks
# 1. gitleaks scans the staged changes. Without gitleaks the commit fails: install it, never skip it.
# 2. bin/check commit runs unless every staged path is documentation (*.md, docs/, LICENSE).
set -eu
cd "$(git rev-parse --show-toplevel)"

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "pre-commit: gitleaks is not installed, so the staged changes cannot be scanned for secrets." >&2
  echo "Install it, then commit again: brew install gitleaks (macOS), or a release from https://github.com/gitleaks/gitleaks/releases" >&2
  exit 1
fi
gitleaks git --pre-commit --staged --redact --no-banner

if ! git diff --cached --name-only --diff-filter=ACMRD | grep -qvE '\.md$|^docs/|^LICENSE$'; then
  echo "pre-commit: only documentation is staged; bin/check commit is not needed"
  exit 0
fi
if [ ! -x bin/check ]; then
  echo "pre-commit: bin/check is missing or not executable, so the commit gate cannot run" >&2
  exit 1
fi
exec bin/check commit
