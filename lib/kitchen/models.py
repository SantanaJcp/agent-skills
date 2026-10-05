"""`kitchen models`: which model does each role, in each person's own setup (~/.config/kitchen/models.toml).

One role today, `reviewer`, the one `second-opinion` reads. It depends on who wrote the work, so it is set per author
family (`--author claude` means the work is Claude's and the reviewer runs on the other provider). A new role is added
when a workflow reads it, not before. Every entry is explicit: provider, model (`default` = that tool's own default),
effort and service tier.

A role nobody set is an error with the command that sets it, never a default model; a reviewer on the author's own
provider is refused. Whether the model exists is learned when it is used: the tool's error is shown as it is.
Principles: `cross-review` (another model reviews), `no-fallbacks` (no stand-in model), `owner-attention` (set once).
"""
from __future__ import annotations

import json
import shlex
import tomllib
from pathlib import Path

from kitchen import common

PROVIDERS = ("claude", "codex")
ROLES = ("reviewer",)  # each set per author family
EFFORTS = ("low", "medium", "high", "xhigh", "max")
TIERS = ("standard", "fast")
FIELDS = ("provider", "model", "effort", "tier")


class ModelsError(Exception):
    pass


def path() -> Path:
    return common.config_dir() / "models.toml"


def load() -> dict:
    p = path()
    if not p.is_file():
        return {}
    try:
        return tomllib.loads(p.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ModelsError(f"cannot parse {p}: {error}; fix it or rerun `kitchen models set`") from error


def key(role: str, author: str | None) -> tuple[str, str]:
    if role not in ROLES:
        raise ModelsError(f"unknown role {role!r}: one of {', '.join(ROLES)}")
    if author not in PROVIDERS:
        raise ModelsError(f"`{role}` depends on who wrote the work: pass --author {' or --author '.join(PROVIDERS)}")
    return (role, author)


def set_command(role: str, author: str | None) -> str:
    who = f" --author {author}" if author else ""
    return f"kitchen models set {role}{who} --provider <{'|'.join(PROVIDERS)}> --model <id|default> --effort <{'|'.join(EFFORTS)}> --tier <{'|'.join(TIERS)}>"


def validate(role: str, author: str | None, entry: dict) -> dict:
    missing = [f for f in FIELDS if not isinstance(entry.get(f), str) or not entry.get(f)]
    if missing:
        raise ModelsError(f"{role}{' for ' + author if author else ''}: missing {', '.join(missing)}; run `{set_command(role, author)}`")
    if entry["provider"] not in PROVIDERS:
        raise ModelsError(f"provider must be one of {', '.join(PROVIDERS)}, not {entry['provider']!r}")
    if entry["effort"] not in EFFORTS:
        raise ModelsError(f"effort must be one of {', '.join(EFFORTS)}, not {entry['effort']!r}")
    if entry["tier"] not in TIERS:
        raise ModelsError(f"tier must be one of {', '.join(TIERS)}, not {entry['tier']!r}")
    if entry["provider"] == author:
        raise ModelsError(f"a {role} for {author}'s work must run on the other provider: the author's model does not check its own work")
    return {f: entry[f] for f in FIELDS}


def get(role: str, author: str | None) -> dict:
    node = load()
    for part in key(role, author):
        node = node.get(part) if isinstance(node, dict) else None
    if not isinstance(node, dict):
        raise ModelsError(f"{role}{' for ' + author + ' work' if author else ''} is not configured in {path()}: run `{set_command(role, author)}`")
    return validate(role, author, node)


def put(role: str, author: str | None, entry: dict) -> None:
    clean = validate(role, author, entry)
    data = load()
    unknown = sorted(set(data) - set(ROLES))
    if unknown:  # rewriting the file would drop them silently
        raise ModelsError(f"{path()} has tables kitchen does not read ({', '.join(unknown)}); remove them by hand, then rerun")
    node = data
    for part in key(role, author)[:-1]:
        node = node.setdefault(part, {})
    node[key(role, author)[-1]] = clean
    lines = ["# kitchen models: which model does each role. Written by `kitchen models set`; each person sets their own.", ""]
    for role_name in ROLES:
        for table, values in [(f"{role_name}.{a}", data[role_name][a]) for a in PROVIDERS if a in data.get(role_name, {})]:
            lines.append(f"[{table}]")
            lines += [f"{f} = {json.dumps(values[f])}" for f in FIELDS]
            lines.append("")
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines), encoding="utf-8")


def command(entry: dict) -> list[str]:
    """The non-interactive CLI call for a role outside T3: `codex exec` or `claude -p`. The prompt goes last."""
    if entry["provider"] == "codex":
        argv = ["codex", "exec", "--skip-git-repo-check", "-s", "read-only"]
        if entry["model"] != "default":
            argv += ["-m", entry["model"]]
        return argv + ["-c", f'model_reasoning_effort="{entry["effort"]}"',
                       "-c", f'service_tier="{"priority" if entry["tier"] == "fast" else "default"}"']
    if entry["tier"] == "fast":
        raise ModelsError("the claude CLI has no flag for the fast tier; set --tier standard, or run the role where the tier can be set (T3's delegate_task)")
    argv = ["claude", "-p"]
    if entry["model"] != "default":
        argv += ["--model", entry["model"]]
    return argv + ["--effort", entry["effort"]]


def render() -> str:
    data = load()
    out = [f"kitchen models  ({path()})"]
    rows = [(r, a) for r in ROLES for a in PROVIDERS]
    for role, author in rows:
        label = f"{role} for {author} work" if author else role
        try:
            e = get(role, author)
            out.append(f"  {label:<24} {e['provider']} {e['model']} · effort {e['effort']} · tier {e['tier']}")
        except ModelsError as error:
            out.append(f"  {label:<24} not configured" if "not configured" in str(error) else f"  {label:<24} invalid: {error}")
    return "\n".join(out)


def shell(argv: list[str]) -> str:
    return " ".join(shlex.quote(a) for a in argv)
