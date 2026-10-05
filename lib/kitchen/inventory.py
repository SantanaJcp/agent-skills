"""`kitchen inventory`: every skill, rule file and automation the agents can see, and where they drift."""
from __future__ import annotations

import hashlib
import os
import tomllib
from collections import defaultdict
from pathlib import Path

from .common import home, projects
from . import rules


def skill_locations() -> list[tuple[str, Path]]:
    h = home()
    places = [("claude", h / ".claude" / "skills"), ("shared", h / ".agents" / "skills"), ("codex", h / ".codex" / "skills")]
    for repo in projects():
        places += [(f"{repo.name}:agents", repo / ".agents" / "skills"), (f"{repo.name}:claude", repo / ".claude" / "skills")]
    return places


def digest(path: Path) -> str | None:
    manifest = path / "SKILL.md"
    return hashlib.sha256(manifest.read_bytes()).hexdigest()[:12] if manifest.is_file() else None


def skills(repo_root: Path) -> list[dict]:
    found = []
    for scope, folder in skill_locations():
        if not folder.is_dir():
            continue
        for entry in sorted(os.listdir(folder)):
            path = folder / entry
            if entry.startswith(".") or not (path.is_dir() or path.is_symlink()):
                continue
            target = Path(os.path.realpath(path))
            found.append({
                "name": entry,
                "scope": scope,
                "path": str(path),
                "symlink": path.is_symlink(),
                "broken": path.is_symlink() and not path.exists(),
                "managed": path.is_symlink() and target.is_relative_to(repo_root),
                "real": str(target),
                "digest": digest(path) if path.exists() else None,
            })
    return found


def drift(found: list[dict]) -> list[dict]:
    by_name = defaultdict(list)
    for skill in found:
        if skill["digest"]:
            by_name[skill["name"]].append(skill)
    issues = []
    for name, copies in sorted(by_name.items()):
        distinct = {}
        for copy in copies:
            distinct.setdefault(copy["real"], copy)
        digests = {copy["digest"] for copy in distinct.values()}
        if len(distinct) > 1 and len(digests) > 1:
            issues.append({"name": name, "copies": [{"scope": c["scope"], "path": c["path"], "digest": c["digest"]} for c in distinct.values()]})
    return issues


def codex_config() -> dict:
    config = home() / ".codex" / "config.toml"
    if not config.is_file():
        return {"disabled_skills": [], "error": None}
    try:
        data = tomllib.loads(config.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        return {"disabled_skills": [], "error": f"cannot parse {config}: {error}"}
    entries = data.get("skills", {}).get("config", [])
    return {"disabled_skills": [e.get("path") for e in entries if e.get("enabled") is False], "error": None}


def automations() -> list[dict]:
    found = []
    for manifest in sorted((home() / ".codex" / "automations").glob("*/automation.toml")):
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        found.append({"id": data.get("id"), "name": data.get("name"), "kind": data.get("kind"), "status": data.get("status")})
    return found


def rule_files(repo_root: Path) -> list[dict]:
    h = home()
    files = []
    for path in (h / ".claude" / "CLAUDE.md", h / ".codex" / "AGENTS.md"):
        files.append({
            "path": str(path),
            "exists": path.exists(),
            "managed": rules.generated(path),  # written by `kitchen install` from the person's rules and PRINCIPLES.md
        })
    return files


def build(repo_root: Path) -> dict:
    found = skills(repo_root)
    return {
        "skills": found,
        "broken": [s for s in found if s["broken"]],
        "drift": drift(found),
        "codex": codex_config(),
        "automations": automations(),
        "rules": rule_files(repo_root),
    }


def render(report: dict) -> str:
    out = ["kitchen inventory", ""]
    out.append("Rule files")
    for rule in report["rules"]:
        state = "managed by kitchen" if rule["managed"] else ("exists, not managed" if rule["exists"] else "missing")
        out.append(f"  {rule['path']}: {state}")

    out += ["", "Skills"]
    by_scope = defaultdict(list)
    for skill in report["skills"]:
        mark = "kitchen" if skill["managed"] else ("broken link" if skill["broken"] else ("link" if skill["symlink"] else "folder"))
        by_scope[skill["scope"]].append(f"{skill['name']} ({mark})")
    for scope, names in by_scope.items():
        out.append(f"  {scope}: {', '.join(names)}")

    out += ["", "Problems"]
    problems = [f"  broken link: {s['path']}" for s in report["broken"]]
    for issue in report["drift"]:
        copies = "; ".join(f"{c['scope']} {c['digest']}" for c in issue["copies"])
        problems.append(f"  drift: {issue['name']} has different content in {copies}")
    if report["codex"]["error"]:
        problems.append(f"  codex config: {report['codex']['error']}")
    problems += [f"  disabled in Codex config: {path}" for path in report["codex"]["disabled_skills"]]
    out += problems or ["  none"]

    paused = [a for a in report["automations"] if a["status"] == "PAUSED"]
    out += ["", f"Codex automations: {len(report['automations'])} total, {len(paused)} paused"]
    out += [f"  {a['status']:<7} {a['kind']:<9} {a['id']}" for a in report["automations"]]
    return "\n".join(out)
