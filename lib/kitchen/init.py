"""`kitchen init <repo>`: set one repo up for an agent loop its owner can trust, asking only what the repo cannot answer.

1. check: what the repo is missing (repocheck: read-only, runs no repository code). `--check` stops here.
2. ask: numbered questions, each with a recommended answer, in a terminal. `--yes` takes the recommendations;
   without a terminal and without `--yes`, init prints the questions and stops: it never answers for the owner.
3. apply: the shared layer, what the team and cloud sessions get, goes on branch kitchen/init (propose: never
   pushed, never overwrites a file); the personal layer goes into ~/.config/kitchen (projects.txt, integrate.toml).

Principles: `owner-attention` (ask only what the repo cannot answer), `doors` (nothing pushed, one-way doors printed),
`no-fallbacks` (an unknown base is asked or refused, never guessed).
"""
from __future__ import annotations

import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from kitchen import common, repocheck

CHECKS = ["bin/check integrate"]
TOML_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


class InitError(Exception):
    pass


@dataclass
class Question:
    id: str
    text: str
    recommended: bool
    why: str


def default_branch(root: Path) -> str | None:
    """The remote's default branch, from origin/HEAD. None when git cannot say: init asks instead of guessing."""
    ref = common.git_out(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    return ref.split("/", 1)[1] if ref and "/" in ref else None


def personal_state(root: Path) -> dict:
    """Is the repo already in the owner's kitchen? Both files are read strictly: a file init cannot parse is an error."""
    listed = any(p.resolve() == root for p in common.projects() if p.exists())
    path = common.config_dir() / "integrate.toml"
    entry = None
    if path.is_file():
        try:
            entry = tomllib.loads(path.read_text(encoding="utf-8")).get("projects", {}).get(root.name)
        except tomllib.TOMLDecodeError as error:
            raise InitError(f"cannot parse {path}: {error}; fix it, then rerun") from error
    return {"listed": listed, "integrate": entry is not None}


def questions(report: dict, personal: dict, base: str | None) -> list[Question]:
    out = []
    if report["missing"]:
        out.append(Question("branch", f"Write the missing pieces on branch kitchen/init? Nothing is pushed; you review and push it.",
                            True, "every piece it writes is listed afterwards, with what it would block today"))
        out.append(Question("prove", "Prove the gate on that branch? This RUNS THE REPO'S CODE in a temporary worktree: "
                                     "bin/check commit twice, once more with a planted defect that must turn it red, and the hook.",
                            True, "a gate that never went red is not trusted"))
    if not (personal["listed"] and personal["integrate"]):
        where = f"base {base}" if base else "base unknown (origin/HEAD is not set): you will be asked for it"
        out.append(Question("personal", f"Add {report['path']} to your kitchen? projects.txt (kitchen status) and "
                                        f"integrate.toml ({where}, checks {' '.join(CHECKS)}).",
                            True, "personal: lives in ~/.config/kitchen, never in the repo"))
    return out


def ask(question: Question, n: int, read: Callable[[str], str], write: Callable[[str], None]) -> bool:
    write(f"\n{n}. {question.text}\n   ({question.why})\n   [1] yes{' (recommended)' if question.recommended else ''}"
          f"  [2] no{'' if question.recommended else ' (recommended)'}\n")
    while True:
        reply = read("> ").strip().lower()
        if reply == "":
            return question.recommended
        if reply in ("1", "y", "yes", "s", "si", "sí"):
            return True
        if reply in ("2", "n", "no"):
            return False
        write("   answer 1 or 2 (Enter takes the recommended one)\n")


def ask_base(read: Callable[[str], str], write: Callable[[str], None]) -> str:
    write("   Which branch is the shared base (for example main or dev)?\n")
    while True:
        reply = read("> ").strip()
        if reply:
            return reply
        write("   the base has no default; type a branch name\n")


def shown(path: Path) -> str:
    home = str(common.home())
    return "~" + str(path)[len(home):] if str(path).startswith(home + os.sep) else str(path)


def add_personal(root: Path, base: str, state: dict) -> list[str]:
    """Append the repo to projects.txt and integrate.toml. Appends only; never rewrites a line the owner wrote."""
    done = []
    config = common.config_dir()
    config.mkdir(parents=True, exist_ok=True)
    if not state["listed"]:
        listing = config / "projects.txt"
        text = listing.read_text(encoding="utf-8") if listing.is_file() else ""
        listing.write_text(text + ("" if text.endswith("\n") or not text else "\n") + f"{root}\n", encoding="utf-8")
        done.append(f"added      {root} to {shown(listing)}")
    if not state["integrate"]:
        if not TOML_KEY.match(root.name):
            raise InitError(f"the folder name {root.name!r} is not a bare TOML key; add [projects.\"{root.name}\"] to integrate.toml by hand")
        path = config / "integrate.toml"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        block = f"[projects.{root.name}]\nbase = {json.dumps(base)}\nchecks = {json.dumps(CHECKS)}\n"
        path.write_text(text + ("\n" if text and not text.endswith("\n\n") else "") + block, encoding="utf-8")
        done.append(f"added      [projects.{root.name}] to {shown(path)} (base {base}, checks {' '.join(CHECKS)})")
    return done


def run(path: Path, branch: str | None, check_only: bool, yes: bool, prove: bool, base: str | None, as_json: bool,
        out: Callable[[str], None] = lambda text: print(text, end=""), err: Callable[[str], None] = lambda text: print(text, end="", file=sys.stderr),
        read: Callable[[str], str] = input, interactive: bool | None = None) -> int:
    from kitchen import propose  # local import: --check alone never loads the writer

    report = repocheck.check(path, branch)
    if check_only:
        out((json.dumps(report, indent=2, ensure_ascii=False) if as_json else repocheck.render(report)) + "\n")
        return report["missing"]

    root = Path(report["path"])
    personal = personal_state(root)
    base = base or default_branch(root)
    asked = questions(report, personal, base)
    interactive = sys.stdin.isatty() if interactive is None else interactive
    if not yes and not interactive:
        err("kitchen init asks before it writes, and there is no terminal to ask in. Run it in a terminal, or answer with flags:\n"
            "  --yes takes the recommended answers (it never runs repository code: add --prove for that), --base <branch> sets the base.\n")
        for n, q in enumerate(asked, start=1):
            err(f"  {n}. {q.text} Recommended: {'yes' if q.recommended else 'no'}.\n")
        return 2

    if not yes and not as_json:
        out(repocheck.render_summary(report) + "\n")  # the context for the questions; --yes asks nothing, and the proposal repeats it
    answers: dict[str, bool] = {}
    for n, q in enumerate(asked, start=1):
        if q.id == "prove" and not answers.get("branch"):
            answers["prove"] = False
        elif yes:
            answers[q.id] = q.recommended and (q.id != "prove" or prove)
        elif q.id == "prove" and prove:
            answers[q.id] = True
        else:
            answers[q.id] = ask(q, n, read, out)
    if answers.get("personal") and not base:
        if yes:
            err("FAIL  the shared base is unknown (origin/HEAD is not set): pass --base <branch>\n")
            return 2
        base = ask_base(read, out)

    code = 0
    summary: dict = {"check": report, "answers": answers, "proposal": None, "personal": []}
    if answers.get("branch"):
        if answers.get("prove"):
            err("kitchen init --prove RUNS REPOSITORY CODE in a temporary worktree of the target repo: its checkout may run "
                "the repo's git filters, then bin/check commit, the commands it calls and the proposed hook run.\n")
        result = propose.propose(root, branch, answers.get("prove", False), log=lambda line: err(line + "\n"))
        summary["proposal"] = result
        if not as_json:
            out("\n" + propose.render(result))
        code = result["exit"]
    if answers.get("personal"):
        summary["personal"] = add_personal(root, base, personal)
    if as_json:
        out(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
        return code
    for line in summary["personal"]:
        out(line + "\n")
    for q in asked:
        if answers.get(q.id):
            continue
        if q.id == "prove" and not answers.get("branch"):
            why = "no branch to prove"
        elif q.id == "prove" and yes:
            why = "--yes never runs repository code: add --prove"
        else:
            why = "answered no"
        out(f"skipped    {q.id} ({why})\n")
    if not asked:
        out("nothing to do: every must-have passes and the repo is already in your kitchen\n")
    return code
