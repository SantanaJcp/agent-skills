"""Which test modules a commit needs: `kitchen check --fast` runs only those; plain `kitchen check` runs them all.

Lint and the public-safety scan always run. The automation suite (about 95 s) runs only when a staged path
can change it; the other modules (about 15 s) run unless every staged path is documentation.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

AUTOMATION_SUITE = "tests/test_automation.py"
AUTOMATION_TRIGGERS = ("automation/", "lib/")


def test_modules(repo: Path) -> list[str]:
    folder = repo / "tests"
    return sorted(p.relative_to(repo).as_posix() for p in folder.glob("test_*.py")) if folder.is_dir() else []


def staged_paths(repo: Path) -> list[str]:
    """Every path the commit adds, changes or deletes; both sides of a rename.

    The hook's environment is kept on purpose: `git commit -a` points GIT_INDEX_FILE at a temporary index."""
    result = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--name-only", "--no-renames", "-z"],
                            capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"cannot list staged paths: {result.stderr.decode(errors='replace').strip()}")
    return [os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw]


def is_docs(path: str) -> bool:
    return path == "LICENSE" or (path.endswith(".md") and not path.startswith("tests/"))


def touches_automation(path: str) -> bool:
    return path == AUTOMATION_SUITE or path.startswith(AUTOMATION_TRIGGERS)


def select(modules: list[str], staged: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """(modules to run, [(module, why it is skipped)]) for these staged paths."""
    if not staged:
        return [], [(m, "nothing is staged") for m in modules]
    automation = any(touches_automation(p) for p in staged)
    other = any(not is_docs(p) and not p.startswith("automation/") for p in staged)
    run, skipped = [], []
    for module in modules:
        if module == AUTOMATION_SUITE:
            needed, why = automation, "no staged path under automation/, lib/ or tests/test_automation.py"
        else:
            needed, why = other, "the staged paths are documentation or automation only"
        if needed:
            run.append(module)
        else:
            skipped.append((module, why))
    return run, skipped


def dotted(module: str) -> str:
    return module.removesuffix(".py").replace("/", ".")
