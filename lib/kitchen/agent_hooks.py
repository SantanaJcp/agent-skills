"""Agent hooks: merge the guards in hooks/ into Claude Code and Codex as PreToolUse hooks on Bash.
Principles: `encode-lessons` (rules that became guards), `no-fallbacks` (a file it cannot parse is refused).

Both tools read the same shape (hooks.PreToolUse[] of {matcher, hooks: [{type: command, command, timeout}]}):
Claude Code from ~/.claude/settings.json, Codex from ~/.codex/hooks.json. The kitchen owns only the handlers whose
command is a script in this repo's hooks/; every other key and hook in those files is the user's and is kept as is.
"""
from __future__ import annotations

import copy
import json
import os
import shlex
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

TIMEOUT_SECONDS = 30
# A command each guard must block; doctor runs the installed hook on it to prove the hook works on this machine.
PROBES = {
    "deny-no-verify": "git commit --no-verify -m kitchen-doctor-probe",
    "deny-shared-push": "git push origin HEAD:main",
    "deny-recursive-rm": "rm -rf /kitchen-doctor-probe",
}


@dataclass
class Target:
    tool: str
    path: Path
    matcher: str


@dataclass
class Change:
    target: Target
    before: dict | None   # None when the file cannot be merged
    after: dict
    problem: str | None


def targets(h: Path) -> list[Target]:
    return [Target("Claude Code", h / ".claude" / "settings.json", "Bash"),
            Target("Codex", h / ".codex" / "hooks.json", "^Bash$")]


def guards(repo: Path) -> list[Path]:
    folder = repo / "hooks"
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and "." not in p.name and os.access(p, os.X_OK))


def command_for(script: Path) -> str:
    return shlex.quote(str(script))


def script_of(handler, repo: Path) -> Path | None:
    """The kitchen script a handler runs, or None when the handler is not the kitchen's."""
    if not isinstance(handler, dict) or not isinstance(handler.get("command"), str):
        return None
    try:
        words = shlex.split(handler["command"])
    except ValueError:
        return None
    if not words:
        return None
    path = Path(os.path.normpath(words[0]))
    return path if path.is_absolute() and path.parent == repo / "hooks" else None


def load(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return {}, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, f"not valid JSON ({error})"
    if not isinstance(data, dict):
        return None, "not a JSON object"
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return None, "`hooks` is not an object"
    groups = hooks.get("PreToolUse", [])
    if not isinstance(groups, list) or not all(isinstance(g, dict) and isinstance(g.get("hooks", []), list) for g in groups):
        return None, "`hooks.PreToolUse` is not a list of {matcher, hooks: [...]} groups"
    return data, None


def merged(data: dict, repo: Path, matcher: str) -> dict:
    """data with the kitchen's handlers replaced by one group for the current guards; nothing else changes."""
    result = copy.deepcopy(data)
    hooks = result.get("hooks", {})
    groups = []
    for group in hooks.get("PreToolUse", []):
        kept = [h for h in group.get("hooks", []) if script_of(h, repo) is None]
        if kept or not group.get("hooks"):
            groups.append({**group, "hooks": kept})
    current = guards(repo)
    if current:
        groups.append({"matcher": matcher, "hooks": [
            {"type": "command", "command": command_for(script), "timeout": TIMEOUT_SECONDS} for script in current]})
    if groups:
        result["hooks"] = {**hooks, "PreToolUse": groups}
    elif "PreToolUse" in hooks:
        rest = {k: v for k, v in hooks.items() if k != "PreToolUse"}
        if rest:
            result["hooks"] = rest
        else:
            result.pop("hooks")
    return result


def plan(h: Path, repo: Path) -> list[Change]:
    changes = []
    for target in targets(h):
        before, problem = load(target.path)
        after = merged(before if before is not None else {}, repo, target.matcher)
        if problem or before != after:
            changes.append(Change(target, before, after, problem and f"{target.path}: {problem}"))
    return changes


def write_json(path: Path, data: dict) -> None:
    real = path.resolve() if path.is_symlink() else path
    real.parent.mkdir(parents=True, exist_ok=True)
    tmp = real.with_name(f".{real.name}.kitchen-tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if real.exists():
        shutil.copymode(real, tmp)
    os.replace(tmp, real)


def apply(changes: list[Change], h: Path, backup_root: Path | None) -> list[str]:
    """Write the merged files. A file that cannot be merged is moved to backup_root first (install --backup)."""
    lines = []
    for change in changes:
        path = change.target.path
        if change.problem:
            assert backup_root is not None, "install refuses unmergeable hook files unless --backup is given"
            dest = backup_root / path.relative_to(h)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest))
            lines.append(f"backed up  {path} -> {dest}")
        write_json(path, change.after)
        lines.append(f"hooks      {change.target.tool}: kitchen guards merged into {path}")
    return lines


def installed(data: dict, repo: Path, matcher: str) -> set[Path]:
    found = set()
    for group in data.get("hooks", {}).get("PreToolUse", []):
        if group.get("matcher") != matcher:
            continue
        for handler in group.get("hooks", []):
            script = script_of(handler, repo)
            if script is not None and handler.get("type") == "command":
                found.add(script)
    return found


def probe(script: Path, command: str) -> bool:
    payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(Path.home()),
                          "tool_input": {"command": command}})
    try:
        result = subprocess.run(["/bin/sh", "-c", command_for(script)], input=payload, capture_output=True, text=True,
                                timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 2 and "Blocked by the kitchen hook" in result.stderr


def doctor(h: Path, repo: Path) -> list[tuple[str, str]]:
    """(level, message) lines for `kitchen doctor`: are the guards installed, enabled and blocking in each tool?"""
    current = guards(repo)
    if not current:
        return []
    report: list[tuple[str, str]] = []
    for target in targets(h):
        data, problem = load(target.path)
        if problem:
            report.append(("FAIL", f"{target.tool} hooks: {target.path} is {problem}; fix it, or run `bin/kitchen install --backup`"))
            continue
        missing = [p.name for p in current if p not in installed(data, repo, target.matcher)]
        stale = [str(p) for g in data.get("hooks", {}).get("PreToolUse", []) for p in
                 (script_of(x, repo) for x in g.get("hooks", [])) if p is not None and p not in current]
        if missing:
            report.append(("FAIL", f"{target.tool} hooks not installed ({', '.join(missing)}) in {target.path}: run `bin/kitchen install`"))
        if stale:
            report.append(("FAIL", f"{target.tool} hooks point to scripts that are gone ({', '.join(stale)}): run `bin/kitchen install`"))
        if target.tool == "Claude Code" and data.get("disableAllHooks") is True:
            report.append(("FAIL", f"Claude Code: disableAllHooks is true in {target.path}, so no hook runs"))
        if not missing and not stale:
            report.append(("INFO", f"{target.tool} hooks installed: {', '.join(p.name for p in current)}"))
    report += codex_features(h)
    for script in current:
        if script.name in PROBES and not probe(script, PROBES[script.name]):
            report.append(("FAIL", f"hook {script.name} did not block its probe `{PROBES[script.name]}`: run it by hand to see why"))
    if any(level == "INFO" and message.startswith("Codex hooks installed") for level, message in report):
        report.append(("INFO", "Codex runs a new or changed hook only after you trust it: open /hooks in Codex once after install"))
    return report


def codex_features(h: Path) -> list[tuple[str, str]]:
    config = h / ".codex" / "config.toml"
    if not config.is_file():
        return []
    try:
        features = tomllib.loads(config.read_text(encoding="utf-8")).get("features", {})
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        return [("WARN", f"cannot read {config} to see whether Codex hooks are enabled: {error}")]
    for key in ("hooks", "codex_hooks"):
        if isinstance(features, dict) and features.get(key) is False:
            return [("FAIL", f"Codex hooks are disabled: [features] {key} = false in {config}")]
    return []
