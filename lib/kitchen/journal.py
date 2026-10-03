"""`kitchen log`: checkpoints that autonomous agents leave for `kitchen status`."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .common import git_out, now, parse_ts, state_dir

STATUSES = ("note", "done", "blocked", "decision")


def journal_path() -> Path:
    return state_dir() / "log.jsonl"


def detect_agent() -> str:
    if os.environ.get("KITCHEN_AGENT"):
        return os.environ["KITCHEN_AGENT"]
    if os.environ.get("CLAUDECODE"):
        return "claude"
    if any(name.startswith("CODEX_") for name in os.environ):
        return "codex"
    return "unknown"


def write(message: str, status: str, cwd: Path) -> dict:
    repo = git_out(cwd, "rev-parse", "--show-toplevel")
    entry = {
        "ts": now().isoformat(timespec="seconds"),
        "repo": repo or str(cwd.resolve()),
        "branch": git_out(cwd, "rev-parse", "--abbrev-ref", "HEAD") if repo else None,
        "sha": git_out(cwd, "rev-parse", "--short", "HEAD") if repo else None,
        "agent": detect_agent(),
        "session": os.environ.get("CLAUDE_CODE_SESSION_ID"),
        "status": status,
        "message": message,
    }
    journal_path().parent.mkdir(parents=True, exist_ok=True)
    with journal_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read(since=None, repo: str | None = None) -> list[dict]:
    if not journal_path().is_file():
        return []
    entries = []
    for number, line in enumerate(journal_path().read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"{journal_path()}:{number} is not valid JSON: {error}") from error
        ts = parse_ts(entry.get("ts", ""))
        if since and (ts is None or ts < since):
            continue
        if repo and entry.get("repo") != repo:
            continue
        entries.append(entry)
    return entries
