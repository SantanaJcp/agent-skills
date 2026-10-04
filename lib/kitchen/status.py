"""`kitchen status`: where every project stands, read from git, gh, the nightly guard and the journal."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import journal
from .common import git, git_common_dir, git_out, state_dir

OWED_DECISION = re.compile(r"^\s*- \[ \]", re.MULTILINE)
UNKNOWN = "unknown"  # a git read failed: never shown as zero or none


def nightly(name: str) -> dict | None:
    history = state_dir() / "nightly" / f"{name}.jsonl"
    if not history.is_file():
        return None
    lines = [line for line in history.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    runs = [json.loads(line) for line in lines]
    streak = 0
    for run in reversed(runs):
        if run.get("status") != "green":
            break
        streak += 1
    return {**runs[-1], "green_streak": streak}


def pull_requests(repo: Path) -> dict:
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--author", "@me", "--state", "open", "--json", "number,title,isDraft,headRefName"],
            cwd=repo, capture_output=True, text=True,
        )
    except FileNotFoundError:
        return {"error": "gh is not installed"}
    if result.returncode != 0:
        return {"error": (result.stderr.strip().splitlines() or ["gh failed"])[0]}
    return {"open": json.loads(result.stdout or "[]")}


def upstream(repo: Path, branch: str | None) -> dict | str | None:
    """None when the branch has no upstream; UNKNOWN when git could not say."""
    if branch is None:
        return UNKNOWN
    if branch == "HEAD":
        return None  # detached
    tracked = git(repo, "for-each-ref", "--format=%(upstream:short)", f"refs/heads/{branch}")
    if tracked.returncode != 0:
        return UNKNOWN
    if not tracked.stdout.strip():
        return None
    counts = git_out(repo, "rev-list", "--left-right", "--count", f"{tracked.stdout.strip()}...HEAD")
    if not counts:
        return UNKNOWN
    behind, ahead = (int(n) for n in counts.split())
    return {"ahead": ahead, "behind": behind, "sha": git_out(repo, "rev-parse", f"{tracked.stdout.strip()}^{{commit}}")}


def nightly_match(run: dict | None, head: str | None, up) -> str | None:
    """Which local commit the nightly run tested, compared by full SHA; short SHAs are never matched."""
    sha = (run or {}).get("sha") or ""
    if len(sha) != 40:
        return None
    if sha == head:
        return "HEAD"
    if isinstance(up, dict) and sha == up.get("sha"):
        return "upstream"
    return None


def project(repo: Path, since) -> dict:
    name = repo.name
    if not repo.is_dir():
        return {"name": name, "path": str(repo), "error": "path does not exist"}
    toplevel = git_out(repo, "rev-parse", "--show-toplevel")
    if not toplevel:
        return {"name": name, "path": str(repo), "error": "not a git repository"}

    branch = git_out(repo, "rev-parse", "--abbrev-ref", "HEAD")
    head = git_out(repo, "rev-parse", "HEAD")
    status = git(repo, "status", "--porcelain")
    listing = git(repo, "worktree", "list", "--porcelain")
    blocks = [b for b in listing.stdout.split("\n\n") if b.strip()][1:] if listing.returncode == 0 else None
    prunable = sum(1 for b in blocks if "\nprunable" in b) if blocks is not None else UNKNOWN
    up = upstream(repo, branch)
    run = nightly(name)
    decisions_file = repo / "decisions.md"

    return {
        "name": name,
        "path": toplevel,
        "branch": branch or UNKNOWN,
        "sha": head or UNKNOWN,
        "dirty": len([line for line in status.stdout.splitlines() if line]) if status.returncode == 0 else UNKNOWN,
        "upstream": up,
        "extra_worktrees": len(blocks) - prunable if blocks is not None else UNKNOWN,
        "prunable_worktrees": prunable,
        "pull_requests": pull_requests(repo),
        "nightly": {**run, "matches": nightly_match(run, head, up)} if run else None,
        "journal": journal.read(since=since, project=git_common_dir(repo), repo=toplevel),
        "owed_decisions": len(OWED_DECISION.findall(decisions_file.read_text(encoding="utf-8"))) if decisions_file.is_file() else None,
    }


def render(report: list[dict], window: str) -> str:
    out = [f"kitchen status · journal window {window}"]
    for p in report:
        out.append("")
        if "error" in p:
            out.append(f"{p['name']}  ✗ {p['error']} ({p['path']})")
            continue
        up = p["upstream"]
        upstream_text = "no upstream" if up is None else (f"upstream {UNKNOWN}" if up == UNKNOWN else f"↑{up['ahead']} ↓{up['behind']}")
        out.append(f"{p['name']}  {p['branch']} @ {p['sha'][:8]}  {upstream_text}  dirty: {p['dirty']}  extra worktrees: {p['extra_worktrees']}"
                   + (f" (+{p['prunable_worktrees']} prunable)" if p["prunable_worktrees"] not in (0, UNKNOWN) else ""))

        run = p["nightly"]
        if run is None:
            out.append("  nightly    no record")
        else:
            mark = "✓" if run.get("status") == "green" else "✗"
            failed = f" (failed: {run['failed_step']})" if run.get("failed_step") else ""
            matches = f" (= {run['matches']})" if run.get("matches") else ""
            warnings = f" · warnings: {'; '.join(map(str, run['warnings']))}" if run.get("warnings") else ""
            out.append(f"  nightly    {mark} {run.get('status')} at {run.get('ts')} on {str(run.get('sha'))[:8]}{matches}{failed}"
                       f" · green streak {run['green_streak']}{warnings}")

        prs = p["pull_requests"]
        if "error" in prs:
            out.append(f"  PRs        unknown: {prs['error']}")
        else:
            listed = ", ".join(f"#{pr['number']}{' (draft)' if pr['isDraft'] else ''}" for pr in prs["open"]) or "none"
            out.append(f"  PRs        {listed}")

        entries = p["journal"]
        blocked = [e for e in entries if e.get("status") == "blocked"]
        out.append(f"  journal    {len(entries)} entries, {len(blocked)} blocked")
        for entry in (blocked + [e for e in entries if e.get("status") != "blocked"])[:5]:
            out.append(f"    {entry['ts'][:16]} {entry['status']:<8} [{entry.get('agent')}] {entry['message']}")

        owed = p["owed_decisions"]
        out.append(f"  decisions  {'no decisions.md' if owed is None else f'{owed} owed by you'}")
    return "\n".join(out)
