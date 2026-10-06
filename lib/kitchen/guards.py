"""`kitchen guards <repo>`: the kitchen's guards in one project, so they run there and nowhere else.

Copies hooks/ into the repo's .kitchen/hooks/ and runs each guard before every Bash call from .claude/settings.json
(Claude Code) and .codex/hooks.json (Codex). Both files are merged: the kitchen's handlers are replaced, every other
key and hook stays. A file that cannot be parsed is an error and nothing is written. `--check` writes nothing and fails
while anything differs from what this kitchen would write. Codex runs a new or changed project hook only after the
person trusts it in `/hooks`, and only in a trusted project.

Each handler runs the repo's own copy and fails closed (exit 2 blocks) when the copy is missing, but only while the
checkout still has the settings file: a session keeps the hooks it loaded, so after a switch to a branch without the
guards, a stale handler would otherwise block every Bash call.
Principles: `doors` (the guards), `no-fallbacks` (fail closed, refuse what cannot be parsed), `isolate` (one project,
reruns byte-identical), `encode-lessons` (rules that became guards).
"""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path

VENDORED = ".kitchen/hooks"
TIMEOUT_SECONDS = 30


class GuardsError(Exception):
    pass


@dataclass
class Tool:
    name: str
    settings: str     # repo-relative file the tool reads project hooks from
    matcher: str
    root: str         # shell code that sets $r to the project root, or exits 2


TOOLS = (
    Tool("Claude Code", ".claude/settings.json", "Bash",
         '[ -n "$CLAUDE_PROJECT_DIR" ] || { echo "kitchen: CLAUDE_PROJECT_DIR is not set" >&2; exit 2; }; r="$CLAUDE_PROJECT_DIR"'),
    # Codex sets no project variable and runs hooks in the session cwd; its docs say to resolve from the git root.
    Tool("Codex", ".codex/hooks.json", "^Bash$",
         'r=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "kitchen: not inside a git repository" >&2; exit 2; }'),
)


def kitchen_files(kitchen: Path) -> dict[str, tuple[bytes, int]]:
    """name -> (bytes, mode) for every file the guards need: each executable guard and the parser they share."""
    folder = kitchen / "hooks"
    out = {}
    for path in sorted(folder.iterdir()) if folder.is_dir() else []:
        if path.is_file() and (path.suffix == ".py" or ("." not in path.name and os.access(path, os.X_OK))):
            out[path.name] = (path.read_bytes(), 0o644 if path.suffix == ".py" else 0o755)
    if not any(mode == 0o755 for _, mode in out.values()):
        raise GuardsError(f"this kitchen has no guards in {folder}")
    return out


def command(tool: Tool, name: str) -> str:
    return (f"sh -c '{tool.root}; s=\"$r/{tool.settings}\"; h=\"$r/{VENDORED}/{name}\"; "
            f"[ -e \"$s\" ] || [ -L \"$s\" ] || exit 0; [ -x \"$h\" ] || {{ echo \"kitchen: guard missing: $h\" >&2; exit 2; }}; exec \"$h\"'")


def is_kitchen_handler(handler) -> bool:
    return isinstance(handler, dict) and isinstance(handler.get("command"), str) \
        and handler["command"].startswith("sh -c '") and f'/{VENDORED}/' in handler["command"]


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardsError(f"{path} is not valid JSON ({error}); fix it, then rerun") from error
    hooks = data.get("hooks", {}) if isinstance(data, dict) else None
    groups = hooks.get("PreToolUse", []) if isinstance(hooks, dict) else None
    if not isinstance(groups, list) or not all(isinstance(g, dict) and isinstance(g.get("hooks", []), list) for g in groups):
        raise GuardsError(f"{path} does not have the shape hooks.PreToolUse[] of {{matcher, hooks: [...]}}; fix it, then rerun")
    return data


def merged(data: dict, tool: Tool, names: list[str]) -> dict:
    """data with the kitchen's handlers replaced by one group that runs each guard; nothing else changes."""
    result = copy.deepcopy(data)
    hooks = result.get("hooks", {})
    groups = []
    for group in hooks.get("PreToolUse", []):
        kept = [h for h in group.get("hooks", []) if not is_kitchen_handler(h)]
        if kept or not group.get("hooks"):
            groups.append({**group, "hooks": kept})
    groups.append({"matcher": tool.matcher, "hooks": [
        {"type": "command", "command": command(tool, name), "timeout": TIMEOUT_SECONDS} for name in names]})
    result["hooks"] = {**hooks, "PreToolUse": groups}
    return result


def plan(repo: Path, kitchen: Path) -> list[tuple[str, bytes, int]]:
    """(repo-relative path, bytes, mode) for every file that differs from what this kitchen would write."""
    files = kitchen_files(kitchen)
    names = [n for n, (_, mode) in files.items() if mode == 0o755]
    wanted = [(f"{VENDORED}/{n}", content, mode) for n, (content, mode) in files.items()]
    for tool in TOOLS:
        data = merged(load(repo / tool.settings), tool, names)
        wanted.append((tool.settings, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode(), 0o644))
    changes = []
    for rel, content, mode in wanted:
        path = repo / rel
        if path.is_symlink():
            raise GuardsError(f"{path} is a symlink; kitchen guards writes only regular files")
        same = path.is_file() and path.read_bytes() == content
        if rel.startswith(VENDORED):
            same = same and (path.stat().st_mode & 0o777) == mode
        if not same:
            changes.append((rel, content, mode))
    return changes


def apply(repo: Path, changes: list[tuple[str, bytes, int]]) -> None:
    for rel, content, mode in changes:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.kitchen-tmp")
        tmp.write_bytes(content)
        os.chmod(tmp, mode if rel.startswith(VENDORED) else (path.stat().st_mode & 0o777 if path.exists() else mode))
        os.replace(tmp, path)


def run(repo: Path, kitchen: Path, check: bool) -> int:
    if not (repo / ".git").exists():
        raise GuardsError(f"{repo} is not the root of a git repository")
    changes = plan(repo, kitchen)
    if check:
        for rel, _, _ in changes:
            print(f"FAIL  {rel} differs from what `kitchen guards` writes")
        print(f"{'FAIL' if changes else 'OK'}    kitchen guards in {repo}")
        return 1 if changes else 0
    apply(repo, changes)
    for rel, _, _ in changes:
        print(f"wrote      {rel}")
    print(f"OK    guards in {repo}: {', '.join(n for n, (_, m) in kitchen_files(kitchen).items() if m == 0o755)}"
          + ("" if changes else " (already current)"))
    print("next:  commit them; Claude Code loads them in a session started at the repo root; "
          "in Codex, trust the project and open /hooks once to approve them (Codex skips a new or changed hook until then)")
    return 0
