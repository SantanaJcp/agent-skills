"""`kitchen status`: where every project stands, read from git, gh, the nightly guard and the journal."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import journal
from .common import git_out, parse_ts, state_dir

OWED_DECISION = re.compile(r"^\s*- \[ \]", re.MULTILINE)


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


def project(repo: Path, since) -> dict:
    name = repo.name
    if not repo.is_dir():
        return {"name": name, "path": str(repo), "error": "path does not exist"}
    toplevel = git_out(repo, "rev-parse", "--show-toplevel")
    if not toplevel:
        return {"name": name, "path": str(repo), "error": "not a git repository"}

    counts = git_out(repo, "rev-list", "--left-right", "--count", "@{u}...HEAD")
    behind, ahead = (int(n) for n in counts.split()) if counts else (None, None)
    porcelain = git_out(repo, "status", "--porcelain") or ""
    blocks = [b for b in (git_out(repo, "worktree", "list", "--porcelain") or "").split("\n\n") if b.strip()][1:]
    prunable = sum(1 for b in blocks if "\nprunable" in b)
    decisions_file = repo / "decisions.md"

    return {
        "name": name,
        "path": toplevel,
        "branch": git_out(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "sha": git_out(repo, "rev-parse", "--short", "HEAD"),
        "dirty": len([line for line in porcelain.splitlines() if line]),
        "upstream": {"ahead": ahead, "behind": behind} if counts else None,
        "extra_worktrees": len(blocks) - prunable,
        "prunable_worktrees": prunable,
        "pull_requests": pull_requests(repo),
        "nightly": nightly(name),
        "journal": journal.read(since=since, repo=toplevel),
        "owed_decisions": len(OWED_DECISION.findall(decisions_file.read_text(encoding="utf-8"))) if decisions_file.is_file() else None,
    }


def render(report: list[dict], window: str) -> str:
    out = [f"kitchen status · journal window {window}"]
    for p in report:
        out.append("")
        if "error" in p:
            out.append(f"{p['name']}  ✗ {p['error']} ({p['path']})")
            continue
        upstream = "no upstream" if p["upstream"] is None else f"↑{p['upstream']['ahead']} ↓{p['upstream']['behind']}"
        out.append(f"{p['name']}  {p['branch']} @ {p['sha']}  {upstream}  dirty: {p['dirty']}  extra worktrees: {p['extra_worktrees']}"
                   + (f" (+{p['prunable_worktrees']} prunable)" if p["prunable_worktrees"] else ""))

        run = p["nightly"]
        if run is None:
            out.append("  nightly    no record")
        else:
            mark = "✓" if run.get("status") == "green" else "✗"
            failed = f" (failed: {run['failed_step']})" if run.get("failed_step") else ""
            out.append(f"  nightly    {mark} {run.get('status')} at {run.get('ts')} on {run.get('sha')}{failed} · green streak {run['green_streak']}")

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
