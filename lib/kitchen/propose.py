"""`kitchen init`: write only what a repo is missing, on branch kitchen/init, never pushed.
Principles: `doors` (never pushed, never overwrites), `isolate` (plumbing only; one ref move), `prove` (--prove).

The proposal stage of `kitchen init`, built from git objects only: no worktree, no checkout, no write to the owner's checkout or index.
It runs `--check` on the commit the branch starts from (`kitchen/init` when it exists, else HEAD), reading files
with ls-tree and cat-file, and adds from templates/ only the files that are missing: decisions.md, bin/check,
.githooks/pre-commit, a verify-skill skeleton and a measure-only baseline. New blobs come from `hash-object -w
--stdin` (no filters), the tree from a private index file in kitchen's scratch dir, then commit-tree. It never
overwrites or edits a file and writes no AGENTS.md prose. .kitchen/init.json records the path and sha256 of
every file it generated, plus its own hash, so a rerun tells kitchen's untouched files from the owner's edits and
leaves the edits alone, the manifest included; a rerun with nothing new commits nothing. KITCHEN-INIT.md holds the report.
A symlink, submodule or file in the way of a path to write is refused before anything is written. The branch moves
once, with `update-ref --no-deref` against its expected old value, and a symbolic kitchen/init is refused. It
never pushes, opens a PR or changes GitHub settings: one-way doors are printed with their commands. Every git
command runs with core.hooksPath pointed at an empty directory. Without --prove nothing from the repo executes.

Stage 3, `--prove`, RUNS REPOSITORY CODE. It is the only path that checks out a worktree (a temporary one, where the
target's git filters may run), at the proposal's commit: `bin/check commit` twice (green and stable), then a
negative control (a syntax error appended to a tracked test or source file) that must turn it red with output
naming that file, then the revert, which must be green again; and the proposed hook against a docs-only commit
and a staged fake key. SIGTERM, SIGINT and SIGHUP kill the running check's process group and remove the worktree.
"""
from __future__ import annotations

import collections
import contextlib
import hashlib
import json
import math
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

from kitchen import repocheck

BRANCH = "kitchen/init"
MANIFEST = ".kitchen/init.json"
REPORT = "KITCHEN-INIT.md"
BASELINE = ".kitchen/baseline.json"
HOOK = ".githooks/pre-commit"
CHECK = "bin/check"
TEMPLATES = Path(__file__).resolve().parents[2] / "templates"
PROVE_TIMEOUT_SECONDS = 900
GITLEAKS_TIMEOUT_SECONDS = 120
TAIL_LINES = 12
CONTROL_FILE = "kitchen-init-control.md"
OURS = ("written", "refreshed", "unchanged", "edited by owner")
VENDORED = ("agent-hooks", "principles")  # copies of the kitchen's own files: refreshed when kitchen wrote them and nobody edited them
GENERATOR = "kitchen init"
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TEST_SDK = re.compile(r"Microsoft\.NET\.Test\.Sdk|<IsTestProject>\s*true", re.IGNORECASE)
SYNTAX = "\n) {} kitchen init negative control: deliberate syntax error\n"
BREAKERS = {".py": SYNTAX.format("#"), ".cs": "\n#error kitchen init negative control: deliberate compile error\n",
            **{suffix: SYNTAX.format("//") for suffix in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx")}}

DOES = {
    "decisions": "Dated decisions; `- [ ]` marks one the owner still owes, and `kitchen status` counts them.",
    "check-contract": "The one check contract: tiers commit, integrate, nightly and verify-tree, filled from the manifests; `--list` prints them.",
    "pre-commit-hook": "gitleaks on the staged changes (fails with the install command when gitleaks is missing), then `bin/check commit` "
                       "unless only documentation is staged. Inactive until `git config core.hooksPath .githooks` in each clone.",
    "verify-skill": "Skeleton of the project's verify skill from templates/verify: placeholders to fill, no bin/verify yet.",
    "baseline-ratchet": "What --check measured, in measure-only mode: no gate reads it yet.",
    "principles": "The kitchen's PRINCIPLES.md, so an agent with only this repo (a teammate, a cloud session) knows what we do and why.",
    "agent-hooks": "The kitchen's agent guards, copied into the repo so teammates and cloud sessions run them without installing the "
                   "kitchen; .claude/settings.json runs each one before every Bash command in Claude Code.",
}


class ProposeError(Exception):
    pass


@dataclass
class Command:
    tier: str        # commit or integrate
    run: str         # the shell command, run from `directory`
    source: str      # where it was detected
    directory: str   # component folder relative to the root, "" for the root

    def line(self) -> str:
        return f"(cd {shlex.quote(self.directory)} && {self.run})" if self.directory else self.run


@dataclass
class File:
    path: str
    piece: str
    content: str
    mode: int = 0o644


class Git:
    """git in the target repo with an empty hooks directory, so no hook of the repo runs while kitchen writes.

    `index` points git at a private index file in kitchen's scratch dir: the owner's index is never read or written."""

    def __init__(self, no_hooks: Path):
        self.no_hooks = no_hooks

    def run(self, cwd: Path, *args: str, data: bytes | None = None, index: Path | None = None) -> subprocess.CompletedProcess:
        env = repocheck.git_env()
        if index is not None:
            env["GIT_INDEX_FILE"] = str(index)
        return subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={self.no_hooks}", "-C", str(cwd), *args],
                              input=data, capture_output=True, env=env)

    def __call__(self, cwd: Path, *args: str, data: bytes | None = None, index: Path | None = None) -> str:
        result = self.run(cwd, *args, data=data, index=index)
        if result.returncode != 0:
            message = result.stderr.decode(errors="replace").strip() or f"exit {result.returncode}"
            raise ProposeError(f"git {' '.join(args[:2])}: {message}")
        return result.stdout.decode(errors="replace").strip()


class Interrupted(BaseException):
    """SIGTERM, SIGINT or SIGHUP arrived; raised in the main thread so every cleanup below runs."""

    def __init__(self, signum: int):
        super().__init__(signal.Signals(signum).name)
        self.signum = signum


@contextlib.contextmanager
def interruptible():
    caught: list[int] = []

    def handler(signum, _frame):
        if not caught:  # a second signal must not cut the cleanup short
            caught.append(signum)
            raise Interrupted(signum)

    previous = {s: signal.signal(s, handler) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    try:
        yield
    finally:
        for s, h in previous.items():
            signal.signal(s, h)


def safe(text: str) -> str:
    """Control characters (a newline in a folder name...) escaped, so a path never starts a line of a generated file."""
    return CONTROL.sub(lambda m: f"\\x{ord(m.group()):02x}", text)


def template(name: str, **values: str) -> str:
    text = (TEMPLATES / name).read_text()
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    if "{{" in text:
        raise ProposeError(f"template {name} has an unfilled placeholder")
    return text


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---- commands from manifests --------------------------------------------------------------------

def python_lint(repo: repocheck.Repo, directory: str) -> tuple[str, str] | None:
    found = repo.find_up(directory, ("ruff.toml", ".ruff.toml"))
    if found:
        return "ruff check .", f"ruff config {found}"
    for folder in repocheck.ancestors(directory):
        rel = repocheck.join(folder, "pyproject.toml")
        if rel in repo.fileset:
            try:
                tools = tomllib.loads(repo.read(rel) or "").get("tool", {})
            except tomllib.TOMLDecodeError:
                tools = {}
            if "ruff" in tools:
                return "ruff check .", f"[tool.ruff] in {rel}"
    found = repo.find_up(directory, (".flake8",)) or repo.find_up(directory, ("setup.cfg", "tox.ini"), re.compile(r"^\[flake8\]", re.MULTILINE))
    return ("flake8", f"flake8 config {found}") if found else None


def pytest_signal(repo: repocheck.Repo, directory: str) -> str | None:
    for name in ("pytest.ini", "conftest.py"):
        if repocheck.join(directory, name) in repo.fileset:
            return f"pytest: {repocheck.join(directory, name)}"
    pyproject = repocheck.join(directory, "pyproject.toml")
    text = repo.read(pyproject) or ""
    if "[tool.pytest" in text:
        return f"pytest: [tool.pytest.ini_options] in {pyproject}"
    for name, marker in (("setup.cfg", "[tool:pytest]"), ("tox.ini", "[pytest]")):
        if marker in (repo.read(repocheck.join(directory, name)) or ""):
            return f"pytest: {marker} in {repocheck.join(directory, name)}"
    for rel in repo.files:
        if repocheck.parent(rel) == directory and re.fullmatch(r"requirements[\w.-]*\.txt", PurePosixPath(rel).name) \
                and re.search(r"^\s*pytest\b", repo.read(rel) or "", re.MULTILINE):
            return f"pytest: listed in {rel}"
    if re.search(r"[\"']pytest\b", text):
        return f"pytest: a dependency in {pyproject}"
    return None


def python_commands(repo: repocheck.Repo, directory: str) -> tuple[list[Command], list[str]]:
    commands, notes = [], []
    lint = python_lint(repo, directory)
    if lint:
        commands.append(Command("commit", lint[0], lint[1], directory))
    prefix = f"{directory}/" if directory else ""
    tests = [f[len(prefix):] for f in repo.files if f.startswith(prefix) and not f.startswith(".agents/")
             and re.fullmatch(r"test.*\.py", PurePosixPath(f).name)]
    pytest = pytest_signal(repo, directory)
    if pytest:
        commands.append(Command("commit", "python3 -m pytest", pytest, directory))
    elif tests:
        start = next((d for d in ("tests", "test") if any(t.startswith(f"{d}/") for t in tests)), None)
        if start:
            commands.append(Command("commit", f"python3 -m unittest discover -s {start}", f"unittest: test files under {repocheck.join(directory, start)}/", directory))
        else:
            commands.append(Command("commit", "python3 -m unittest discover", f"unittest: {repocheck.join(directory, tests[0])}", directory))
    else:
        notes.append(f"{directory or '.'}: no test*.py file and no pytest config, so no test command")
    return commands, notes


def node_commands(repo: repocheck.Repo, directory: str, manifest: str, lint_found: bool) -> tuple[list[Command], list[str]]:
    try:
        data = json.loads(repo.read(manifest) or "")
    except json.JSONDecodeError:
        return [], [f"{manifest} does not parse, so no command"]
    scripts = data.get("scripts") if isinstance(data, dict) else None
    scripts = scripts if isinstance(scripts, dict) else {}
    commands, notes = [], []
    if isinstance(data, dict) and (data.get("dependencies") or data.get("devDependencies")):
        notes.append(f"{manifest} has dependencies: install them (npm ci) before bin/check runs")
    if "lint" in scripts:
        commands.append(Command("commit", "npm run lint", f"from {manifest} scripts.lint", directory))
    elif lint_found:
        notes.append(f"{manifest}: a lint config exists but no lint script, so no lint command")
    typecheck = next((k for k in ("typecheck", "type-check") if k in scripts), None)
    if typecheck:
        commands.append(Command("commit", f"npm run {typecheck}", f"from {manifest} scripts.{typecheck}", directory))
    test = scripts.get("test")
    if isinstance(test, str) and test.strip() and "no test specified" not in test:
        commands.append(Command("commit", "npm test", f"from {manifest} scripts.test", directory))
    else:
        notes.append(f"{manifest}: no test script, so no test command")
    if "build" in scripts:
        commands.append(Command("integrate", "npm run build", f"from {manifest} scripts.build", directory))
    return commands, notes


def dotnet_commands(repo: repocheck.Repo, directory: str, manifest: str) -> tuple[list[Command], list[str]]:
    if not manifest.endswith((".sln", ".slnx", ".csproj")):
        return [], [f"{manifest}: no solution or project to build"]
    name = shlex.quote(PurePosixPath(manifest).name)
    commands = [Command("commit", f"dotnet build {name}", f"from {manifest}", directory)]
    prefix = f"{directory}/" if directory else ""
    tests = [f for f in repo.files if f.endswith(".csproj") and f.startswith(prefix) and TEST_SDK.search(repo.read(f) or "")]
    if tests:
        commands.append(Command("commit", f"dotnet test --no-build {name}", f"test project {tests[0]}", directory))
        return commands, []
    return commands, [f"{manifest}: no test project (no Microsoft.NET.Test.Sdk reference), so no test command"]


def detect_commands(repo: repocheck.Repo, components: list[dict]) -> tuple[list[Command], list[str]]:
    commands: list[Command] = []
    notes: list[str] = []
    for component in components:
        if CONTROL.search(component["path"]) or CONTROL.search(component["manifest"]):
            notes.append(f"skipped {safe(component['manifest'])}: its path has a control character, which no generated script may carry")
            continue
        directory = "" if component["path"] == "." else component["path"]
        if component["stack"] == "python":
            found = python_commands(repo, directory)
        elif component["stack"] == "node":
            found = node_commands(repo, directory, component["manifest"], component["lint"]["status"] == "PASS")
        else:
            found = dotnet_commands(repo, directory, component["manifest"])
        commands += found[0]
        notes += found[1]
    return commands, notes


# ---- the pieces -----------------------------------------------------------------------------------

def render_check(commands: list[Command], notes: list[str]) -> str:
    def body(tier: str) -> list[str]:
        lines = []
        for command in (c for c in commands if c.tier == tier):
            lines += [f"  # unverified: {safe(command.source)}", f"  {command.line()}"]
        return lines
    commit = [f"  # {safe(note)}" for note in notes] + body("commit")
    if not any(c.tier == "commit" for c in commands):
        commit += ['  echo "bin/check commit: no command detected; add one" >&2', "  exit 1"]
    return template("init/check.sh.tmpl", commit="\n".join(commit), integrate="\n".join(["  tier_commit"] + body("integrate")))


def skill_name(folder: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "-", folder.lower()).strip("-")
    if not name:
        raise ProposeError(f"cannot derive a skill name from the folder name {folder!r}")
    return name


def baseline(report: dict) -> str:
    components = []
    for c in report["components"]:
        entry = {"path": c["path"], "stack": c["stack"], "manifest": c["manifest"], "lint": c["lint"]["status"]}
        if "lockfile" in c:
            entry["lockfile"] = c["lockfile"]["status"]
        components.append(entry)
    data = {
        "mode": "measure-only",
        "note": "Seeded by kitchen init from what --check measured. No gate reads it yet; it becomes a ratchet "
                "only when a gate compares against it and fails when a value gets worse.",
        "measured_at": report["head"],
        "must_haves": {m["id"]: m["status"] for m in report["must_haves"]},
        "components": components,
    }
    return json.dumps(data, indent=2) + "\n"


def one_way_doors(origin_url: str, protection: str, project: str) -> list[dict]:
    match = repocheck.GITHUB_REMOTE.search(origin_url)
    slug = f"{match.group(1)}/{match.group(2)}" if match else "OWNER/REPO"
    rules = [{"type": "deletion"}, {"type": "non_fast_forward"},
             {"type": "pull_request", "parameters": {"required_approving_review_count": 0, "dismiss_stale_reviews_on_push": False,
                                                     "require_code_owner_review": False, "require_last_push_approval": False,
                                                     "required_review_thread_resolution": False}}]
    ruleset = {"name": "default branch", "target": "branch", "enforcement": "active",
               "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}}, "rules": rules}
    required = {**ruleset, "rules": rules + [{"type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": False, "required_status_checks": [{"context": "check"}]}}]}
    doors = []
    if protection != "PASS":
        doors.append({"title": "Ruleset on the default branch: block deletion and force-push, require a pull request",
                      "recommend": "yes",
                      "command": f"gh api -X POST repos/{slug}/rulesets --input - <<'JSON'\n{json.dumps(ruleset)}\nJSON"})
        doors.append({"title": "Required status check on that ruleset: a CI job named `check` that runs `bin/check integrate`",
                      "recommend": "yes, once that CI job has run green, so the rule never blocks every merge",
                      "command": f"gh api repos/{slug}/rulesets   # the id of the ruleset from the decision above\n"
                                 f"gh api -X PUT repos/{slug}/rulesets/RULESET_ID --input - <<'JSON'\n{json.dumps(required)}\nJSON"})
    doors.append({"title": "Schedule the nightly tier on a host with the kitchen's automation",
                  "recommend": "yes, once `bin/check nightly` is green by hand",
                  "command": f"# in ~/.config/kitchen/automation/{project}.env: GUARD_STEPS=(\"check|bin/check nightly\")\n"
                             f"automation/bin/install-schedule {project}   # from the kitchen checkout"})
    doors.append({"title": "Credentials for unattended pushes (the gardener): a fine-grained token limited to this repo",
                  "recommend": "not yet: unattended-ready is not assessed",
                  "command": f"# create it at https://github.com/settings/personal-access-tokens/new: repository {slug}, "
                             "Contents and Pull requests read and write; keep it on the host, never in the repo"})
    if not match:
        for door in doors:
            if "OWNER/REPO" in door["command"]:
                door["command"] += "\n# origin is not a GitHub remote: replace OWNER/REPO"
    return doors


def wanted_files(repo: repocheck.Repo, report: dict, name: str, doors: list[dict], commands: list[Command], notes: list[str]) -> list[File]:
    status = {m["id"]: m["status"] for m in report["must_haves"]}
    files = []
    if status["decisions"] != "PASS":
        owed = "\n".join(f"- [ ] {d['title']} (one-way door, proposed by kitchen init; see KITCHEN-INIT.md)" for d in doors) or "None yet."
        files.append(File("decisions.md", "decisions", template("init/decisions.md.tmpl", owed=owed)))
    if status["check-contract"] != "PASS" and report["stack_status"] == "detected" and not repo.exists(CHECK) and not repo.exists(".kitchen/checks.toml"):
        files.append(File(CHECK, "check-contract", render_check(commands, notes), 0o755))
    hook_candidates = [f for f in repo.files if PurePosixPath(f).name == "pre-commit"] + report["hooks"]["managers"]
    if (status["pre-commit-hook"] != "PASS" or status["secret-scan"] != "PASS") and not report["hooks"]["active"] and not hook_candidates:
        files.append(File(HOOK, "pre-commit-hook", template("init/pre-commit.sh.tmpl"), 0o755))
    if status["verify-skill"] != "PASS" and not any(f.startswith(".agents/skills/verify-") for f in repo.files):
        skill = (TEMPLATES / "verify" / "SKILL.md.tmpl").read_text().replace("<repo>", name)
        files += [File(f".agents/skills/verify-{name}/SKILL.md", "verify-skill", skill),
                  File(f".agents/skills/verify-{name}/features/README.md", "verify-skill", template("init/features-README.md.tmpl"))]
    if status["baseline-ratchet"] != "PASS" and not repocheck.baseline_candidates(repo):
        files.append(File(BASELINE, "baseline-ratchet", baseline(report)))
    if status["agent-hooks"] != "PASS":
        guards = repocheck.kitchen_guards()
        for name, content in guards.items():
            path = f"{repocheck.VENDORED_HOOKS}/{name}"
            if not repo.exists(path) or repo.read(path) != content:  # missing, or a copy init may refresh
                files.append(File(path, "agent-hooks", content, 0o644 if name.endswith(".py") else 0o755))
        if not repo.exists(repocheck.CLAUDE_SETTINGS):
            commands = [{"type": "command", "command": repocheck.guard_command(n), "timeout": 30} for n in guards if not n.endswith(".py")]
            settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": commands}]}}
            files.append(File(repocheck.CLAUDE_SETTINGS, "agent-hooks", json.dumps(settings, indent=2) + "\n"))
    if status["principles"] != "PASS" and repocheck.KITCHEN_PRINCIPLES.is_file():
        content = repocheck.KITCHEN_PRINCIPLES.read_text(encoding="utf-8")
        if not repo.exists(repocheck.VENDORED_PRINCIPLES) or repo.read(repocheck.VENDORED_PRINCIPLES) != content:
            files.append(File(repocheck.VENDORED_PRINCIPLES, "principles", content))
    return files


# ---- manifest and plumbing: nothing here touches a working tree -------------------------------------------

def manifest_hash(data: dict) -> str:
    return sha256(json.dumps({k: v for k, v in data.items() if k != "sha256"}, indent=2, sort_keys=True).encode())


def read_manifest(repo: repocheck.Repo) -> tuple[str, dict]:
    """(state, data): absent, unchanged (kitchen wrote it as it is), edited (kitchen's, changed since) or foreign."""
    if not repo.exists(MANIFEST):
        return "absent", {}
    try:
        data = json.loads(repo.read(MANIFEST) or "") if repo.is_file(MANIFEST) else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict) or data.get("generator") != GENERATOR or not isinstance(data.get("files"), dict):
        return "foreign", {}
    return ("unchanged" if data.get("sha256") == manifest_hash(data) else "edited"), data


def blob_bytes(git: Git, root: Path, sha: str) -> bytes:
    result = git.run(root, "cat-file", "blob", sha)
    if result.returncode != 0:
        raise ProposeError(f"git cat-file blob {sha}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def classify(git: Git, repo: repocheck.Repo, path: str, entry: dict | None) -> str:
    present = repo.exists(path)
    if entry is not None:
        if not present:
            return "deleted by owner"
        if not repo.is_file(path):
            return "edited by owner"
        return "unchanged" if sha256(blob_bytes(git, repo.root, repo.tree[path][1])) == entry.get("sha256") else "edited by owner"
    return "exists" if present else "write"


def refuse_unsafe_targets(tree: dict[str, tuple[str, str]], paths: list[str]) -> None:
    """Every path kitchen writes or replaces must sit under real folders: no symlink, submodule or file in the way."""
    kinds = {"120000": "a symlink", "160000": "a submodule"}
    for path in paths:
        if CONTROL.search(path):
            raise ProposeError(f"refusing to write {safe(path)}: it has a control character")
        parts = PurePosixPath(path).parts
        for i in range(1, len(parts) + 1):
            prefix = "/".join(parts[:i])
            if prefix not in tree:
                continue
            mode = tree[prefix][0]
            if i < len(parts):
                raise ProposeError(f"refusing to write {path}: {prefix} is {kinds.get(mode, 'a file')} in the tree, not a folder")
            if mode in kinds:
                raise ProposeError(f"refusing to replace {path}: it is {kinds[mode]} in the tree")


def commit_files(git: Git, root: Path, parent: str, files: list[tuple[str, bytes, str]], message: str, index: Path) -> str:
    """A commit on top of `parent` with `files` (path, content, mode) added or replaced, from git objects only."""
    index.unlink(missing_ok=True)
    git(root, "read-tree", parent, index=index)
    for path, content, mode in files:
        sha = git(root, "hash-object", "-w", "--stdin", data=content)  # from stdin: no filter, no attributes
        git(root, "update-index", "--add", "--cacheinfo", f"{mode},{sha},{path}", index=index)
    tree = git(root, "write-tree", index=index)
    index.unlink(missing_ok=True)
    return git(root, "commit-tree", tree, "-p", parent, "-m", message)


def checked_out_at(git: Git, root: Path) -> str | None:
    current = None
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            current = line.removeprefix("worktree ")
        elif line == f"branch refs/heads/{BRANCH}":
            return current
    return None


# ---- stage 3: the proof ------------------------------------------------------------------------------

def repo_code_env(tmp: Path) -> dict[str, str]:
    """The caller's environment without git's repo-local variables; temp files go to kitchen's scratch dir, removed after."""
    env = {k: v for k, v in os.environ.items()
           if k not in repocheck.REPO_LOCAL_GIT_ENV and not k.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))}
    return {**env, "TMPDIR": str(tmp), "TMP": str(tmp), "TEMP": str(tmp)}


def kill_group(process: subprocess.Popen) -> None:
    """SIGKILL the process group the run started: the check and anything it spawned."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    process.wait()


def run_code(argv: list[str], cwd: Path, tmp: Path, timeout: int = PROVE_TIMEOUT_SECONDS) -> dict:
    """Run repository code in its own process group; exit None means it never finished (timeout) or never started."""
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=repo_code_env(tmp), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    except OSError as error:
        return {"exit": None, "why": f"cannot run {argv[0]}: {error.strerror}", "tail": [], "output": ""}
    try:
        out, _ = process.communicate(timeout=timeout)
        result = {"exit": process.returncode, "why": f"exit {process.returncode}"}
    except subprocess.TimeoutExpired:
        kill_group(process)
        out = process.stdout.read() if process.stdout else b""
        result = {"exit": None, "why": f"timed out after {timeout}s"}
    except BaseException:  # Interrupted, KeyboardInterrupt: nothing the run started may outlive kitchen
        kill_group(process)
        raise
    kill_group(process)  # whatever it left running in the background
    text = ANSI.sub("", out.decode("utf-8", errors="replace"))
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return {**result, "tail": lines[-TAIL_LINES:], "output": text}


def fake_aws_key() -> str:
    """A random key in AWS's shape, built at run time so no repo ever holds one; entropy high enough for gitleaks."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    while True:
        body = "".join(secrets.choice(alphabet) for _ in range(16))
        if -sum(n / 16 * math.log2(n / 16) for n in collections.Counter(body).values()) > 3.5:
            return "AKIA" + body


def gitleaks_tree(wt: Path, scratch: Path) -> dict:
    exe = shutil.which("gitleaks")
    if not exe:
        return {"state": "not run", "detail": "gitleaks is not installed"}
    report = scratch / "gitleaks-tree.json"
    try:
        result = subprocess.run([exe, "dir", str(wt), "--redact", "--no-banner", "--exit-code", "0", "--report-format", "json",
                                 "--report-path", str(report)], capture_output=True, text=True, timeout=GITLEAKS_TIMEOUT_SECONDS,
                                stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"state": "error", "detail": f"gitleaks dir timed out after {GITLEAKS_TIMEOUT_SECONDS}s"}
    if result.returncode != 0:
        return {"state": "error", "detail": f"gitleaks dir exit {result.returncode}"}
    try:
        findings = json.loads(report.read_text() or "[]")
    except (OSError, json.JSONDecodeError):
        return {"state": "error", "detail": "gitleaks dir wrote no readable report"}
    real = os.path.realpath(wt)
    where = sorted({f"{os.path.relpath(os.path.realpath(f.get('File', '')), real)}:{f.get('StartLine')}" for f in findings})
    return {"state": "ran", "count": len(findings), "where": where[:5]}


def control_target(repo: repocheck.Repo) -> str | None:
    """The file the negative control breaks: the first tracked test file, else the first tracked source file."""
    breakable = lambda rel: PurePosixPath(rel).suffix in BREAKERS and not rel.startswith((".agents/", ".kitchen/")) and not CONTROL.search(rel)
    tests = sorted(f for f in repocheck.test_files(repo) if breakable(f))
    if tests:
        return tests[0]
    sources = sorted(f for f in repo.files if breakable(f))
    return sources[0] if sources else None


def negative_control(git: Git, wt: Path, target: str | None, tmp: Path, log: Callable[[str], None]) -> dict:
    """Trusted only if: red with the deliberate breakage, the red output names the broken file, green again after the revert."""
    if target is None:
        return {"state": "not run", "detail": "no tracked test or source file (.py, .js, .ts, .cs...) to break",
                "why": "negative control not run: no tracked test or source file to break"}
    path = wt / target
    original = path.read_bytes()
    change = f"a {'compile' if path.suffix == '.cs' else 'syntax'} error appended to {target}"
    log(f"kitchen init --prove: negative control, {change}; bin/check commit must go red")
    try:
        with open(path, "ab") as handle:
            handle.write(BREAKERS[path.suffix].encode())
        red = run_code([str(wt / CHECK), "commit"], wt, tmp)
    finally:
        path.write_bytes(original)
    if git.run(wt, "diff", "--quiet", "HEAD", "--", target).returncode != 0:
        raise ProposeError(f"the negative control on {target} could not be reverted in the temporary worktree")
    after = run_code([str(wt / CHECK), "commit"], wt, tmp)
    named = target in red["output"] or PurePosixPath(target).name in red["output"]
    shown = {k: v for k, v in red.items() if k != "output"}
    base = {"target": target, "change": change, "result": shown}
    if red["exit"] in (0, None):
        why = f"stayed green under its negative control ({change})" if red["exit"] == 0 else f"negative control {red['why']} ({change})"
        return {**base, "state": "no", "why": why, "detail": f"bin/check commit {red['why']} after {change}"}
    if not named:
        why = f"went red ({red['why']}) under its negative control, but its output never names {target}, so it may be red for another reason"
        return {**base, "state": "no", "why": why, "detail": f"bin/check commit {red['why']} after {change}, without naming {target}"}
    if after["exit"] != 0:
        why = f"red under its negative control, then still red after the revert ({after['why']})"
        return {**base, "state": "no", "why": why, "detail": f"bin/check commit {after['why']} after {target} was reverted"}
    return {**base, "state": "yes", "why": f"green twice, red naming {target} under its negative control ({change}), green after the revert",
            "detail": f"bin/check commit {red['why']} after {change}, naming {target}; green again after the revert"}


def prove_hook(git: Git, wt: Path, tmp: Path, log: Callable[[str], None]) -> dict:
    control = wt / CONTROL_FILE
    if os.path.lexists(control):
        return {"state": "untrusted", "why": f"{CONTROL_FILE} already exists, and the hook's controls need that path"}
    log(f"kitchen init --prove: running {HOOK} against a staged docs-only change, then a staged fake key")
    try:
        control.write_text("kitchen init positive control: documentation only\n")
        git(wt, "add", "-f", "--", CONTROL_FILE)
        allowed = run_code([str(wt / HOOK)], wt, tmp)
        control.write_text("kitchen init negative control\naws_access_key_id = " + fake_aws_key() + "\n")
        git(wt, "add", "-f", "--", CONTROL_FILE)
        blocked = run_code([str(wt / HOOK)], wt, tmp)
    finally:
        git.run(wt, "rm", "-q", "--cached", "--ignore-unmatch", "--", CONTROL_FILE)
        control.unlink(missing_ok=True)
    if git.run(wt, "diff", "--cached", "--quiet").returncode != 0:
        raise ProposeError("the hook's controls could not be unstaged in the temporary worktree")
    first = lambda run: next((l for l in run["tail"] if "gitleaks" in l or "pre-commit" in l), run["tail"][-1] if run["tail"] else "")
    if allowed["exit"] != 0:
        return {"state": "untrusted", "why": f"blocked a docs-only commit ({allowed['why']}): {first(allowed)}"}
    if blocked["exit"] in (0, None):
        return {"state": "untrusted", "why": f"let a staged fake AWS key through ({blocked['why']})"}
    if not any("leaks found" in line for line in blocked["tail"]):
        return {"state": "untrusted", "why": f"blocked the staged fake key, but not through gitleaks ({blocked['why']}): {first(blocked)}"}
    return {"state": "trusted", "why": "let a docs-only commit through and blocked a staged fake AWS key (gitleaks: leaks found)"}


def prove(git: Git, wt: Path, target: str | None, hook_ours: bool, scratch: Path, log: Callable[[str], None]) -> dict:
    head = git(wt, "rev-parse", "HEAD")
    tmp = scratch / "tmp"  # TMPDIR for repository code
    tmp.mkdir(exist_ok=True)
    proof: dict = {"sha": head, "gitleaks_tree": gitleaks_tree(wt, scratch), "hook": None}
    if not (wt / CHECK).is_file():
        why = "no bin/check to run" + ("; --prove does not run .kitchen/checks.toml" if (wt / ".kitchen" / "checks.toml").is_file() else "")
        proof["checks"] = {"state": "not run", "detail": why}
        proof["control"] = {"state": "not run", "detail": "no bin/check to turn red", "why": why}
    else:
        log(f"kitchen init --prove: running bin/check commit twice in {wt}")
        first = run_code([str(wt / CHECK), "commit"], wt, tmp)
        second = run_code([str(wt / CHECK), "commit"], wt, tmp) if first["exit"] == 0 else None
        proof["green"] = {k: v for k, v in (second if second and second["exit"] != 0 else first).items() if k != "output"}
        if first["exit"] != 0:
            proof["checks"] = {"state": "no", "detail": f"bin/check commit {first['why']} at {head[:7]}"}
        elif second["exit"] != 0:
            proof["checks"] = {"state": "no", "detail": f"not stable: bin/check commit exit 0, then {second['why']} on the second run at {head[:7]}"}
        else:
            proof["checks"] = {"state": "yes", "detail": f"bin/check commit exit 0 twice at {head[:7]}"}
        if proof["checks"]["state"] == "yes":
            proof["control"] = negative_control(git, wt, target, tmp, log)
        else:
            why = "bin/check commit is not green and stable before the control, so a red control would prove nothing"
            proof["control"] = {"state": "not run", "detail": why, "why": why}
    if hook_ours:
        proof["hook"] = prove_hook(git, wt, tmp, log)
    return proof


# ---- the report ------------------------------------------------------------------------------------

def blocks(piece: str, content: str | None, proof: dict | None) -> str:
    if piece == "decisions":
        owed = len(re.findall(r"^\s*- \[ \]", content or "", re.MULTILINE))
        return f"nothing; it lists {owed} owed decision{'s' if owed != 1 else ''} for `kitchen status`"
    if piece == "principles":
        return "nothing: agents read it once AGENTS.md or CLAUDE.md names it"
    if piece == "agent-hooks":
        return ("agent commands that push to a shared branch, skip the repo's hooks, or rm -r outside the temp dir, "
                "in Claude Code sessions started at the repo root")
    if piece in ("verify-skill", "baseline-ratchet"):
        return "nothing: " + ("a skeleton" if piece == "verify-skill" else "measure-only")
    if proof is None:
        return "not run: needs --prove, which runs repository code"
    check = proof["checks"]
    gate = {"yes": f"nothing: bin/check commit is green at {proof['sha'][:7]}",
            "no": f"every commit that is not docs-only, today: {check['detail']}"}.get(check["state"], f"unknown: {check['detail']}")
    if piece == "check-contract":
        return gate
    tree = proof["gitleaks_tree"]
    if tree["state"] == "ran":
        leaks = (f"{tree['count']} gitleaks finding{'s' if tree['count'] != 1 else ''} in today's tree ({', '.join(tree['where'])}), "
                 "each blocking a commit that stages it") if tree["count"] else "no gitleaks finding in today's tree"
    else:
        leaks = f"gitleaks over today's tree not run: {tree['detail']}"
    return f"{leaks}; bin/check commit: {gate}"


def trust_lines(states: dict[str, str], pieces: dict[str, str], proof: dict | None, check_present: bool) -> list[dict]:
    out = []
    if check_present:
        if proof is None:
            out.append({"path": CHECK, "state": "not proved", "why": "rerun with --prove"})
        elif proof["checks"]["state"] != "yes":
            out.append({"path": CHECK, "state": "untrusted", "why": proof["checks"]["detail"]})
        else:
            control = proof["control"]
            out.append({"path": CHECK, "state": "trusted" if control["state"] == "yes" else "untrusted", "why": control["why"]})
    for path, piece in pieces.items():
        if states.get(path) not in OURS:
            continue
        if piece == "pre-commit-hook":
            hook = proof["hook"] if proof else None
            out.append({"path": path, "state": hook["state"] if hook else "not proved", "why": hook["why"] if hook else "rerun with --prove"})
        elif piece == "verify-skill" and path.endswith("/SKILL.md"):
            out.append({"path": path, "state": "untrusted", "why": "a skeleton: nothing to run until bin/verify exists and its own negative control goes red"})
        elif piece == "baseline-ratchet":
            out.append({"path": path, "state": "measure-only", "why": "not a gate, so there is nothing to prove"})
    return out


def readiness(states: dict[str, str], written: int, proof: dict | None) -> dict:
    present = sum(1 for s in states.values() if s in OURS)
    files = ({"state": "yes", "detail": f"{present} file{'s' if present != 1 else ''} on {BRANCH}" + ("" if written else "; nothing new this run")}
             if present else {"state": "no", "detail": "nothing is missing that kitchen init writes"})
    if proof is None:
        rerun = "rerun with --prove (it runs repository code)"
        return {"files_proposed": files, "checks_run_green": {"state": "not run", "detail": rerun},
                "negative_control_went_red": {"state": "not run", "detail": rerun},
                "unattended_ready": {"state": "not assessed", "detail": "kitchen init does not assess unattended runs (sandbox, schedule, credentials)"}}
    controls = [proof["control"]]
    if proof["hook"]:
        hook = proof["hook"]
        controls.append({"state": {"trusted": "yes", "untrusted": "no"}[hook["state"]], "detail": f"{HOOK}: {hook['why']}"})
    states_seen = {c["state"] for c in controls}
    red = "yes" if states_seen == {"yes"} else "no" if "no" in states_seen else "not run"
    return {"files_proposed": files, "checks_run_green": proof["checks"],
            "negative_control_went_red": {"state": red, "detail": "; ".join(c["detail"] for c in controls)},
            "unattended_ready": {"state": "not assessed", "detail": "kitchen init does not assess unattended runs (sandbox, schedule, credentials)"}}


def proposals(report: dict, states: dict[str, str], pieces: dict[str, str], name: str, repo: repocheck.Repo) -> list[dict]:
    status = {m["id"]: m for m in report["must_haves"]}
    steps = {s["id"]: s["step"] for s in report["next_steps"]}
    ours = {pieces[p] for p, s in states.items() if s in OURS}
    out = []
    def add(key: str, text: str) -> None:
        out.append({"id": key, "text": text})
    def existing(key: str) -> None:
        add(key, f"{status[key]['proof']}. {steps.get(key, '')}".strip())
    for key in ("check-contract", "pre-commit-hook", "secret-scan", "agents-md", "verify-skill", "baseline-ratchet", "skills-linked",
                "agent-hooks", "principles"):
        if status[key]["status"] == "PASS":
            continue
        if key == "check-contract" and "check-contract" not in ours:
            if report["stack_status"] != "detected":
                add(key, "unsupported stack (no .NET, Node or Python manifest): write bin/check by hand with the tiers commit, integrate, "
                         "nightly and verify-tree; kitchen init does not guess commands")
            else:
                existing(key)
        elif key in ("pre-commit-hook", "secret-scan") and "pre-commit-hook" not in ours:
            if key == "secret-scan" and report["hooks"]["active"]:
                add(key, f"add `gitleaks git --pre-commit --staged` to {report['hooks']['pre_commit']}, failing when gitleaks is missing")
            else:
                existing(key)
        elif key == "agents-md":
            if report["agent_files"]["AGENTS.md"] is None:
                add(key, "AGENTS.md is missing, and kitchen init writes no prose. Draft one with Claude Code's init: run "
                         "`CLAUDE_CODE_NEW_INIT=1 claude`, then `/init`; keep only verified commands, name `bin/check` and the verify "
                         "skill, and stay under 200 lines.")
            else:
                existing(key)
        elif key in ("verify-skill", "baseline-ratchet") and key not in ours:
            existing(key)
        elif key == "principles":
            copy = repocheck.VENDORED_PRINCIPLES
            if states.get(copy) in ("exists", "edited by owner"):
                add(key, f"{copy} is not kitchen's copy, so kitchen left it alone: replace it with the kitchen's PRINCIPLES.md")
            if not any(copy in (repo.read(name) or "") for name in ("AGENTS.md", "CLAUDE.md")):
                add(key, f"add this line to AGENTS.md (kitchen writes no prose there): {repocheck.PRINCIPLES_POINTER}")
        elif key == "agent-hooks":
            if "agent-hooks" not in ours:
                existing(key)
            elif repocheck.CLAUDE_SETTINGS not in states:  # it exists, so kitchen did not write it
                commands = [{"type": "command", "command": repocheck.guard_command(n), "timeout": 30}
                            for n in repocheck.kitchen_guards() if not n.endswith(".py")]
                add(key, f"{repocheck.CLAUDE_SETTINGS} exists, so kitchen left it alone: add this group under hooks.PreToolUse: "
                         + json.dumps({"matcher": "Bash", "hooks": commands}))
        elif key == "skills-linked":
            skills = report["agent_files"]["project_skills"] or ([f"verify-{name}"] if "verify-skill" in ours else [])
            if skills:
                links = " && ".join(f"ln -s ../../.agents/skills/{s} .claude/skills/{s}" for s in skills)
                add(key, f"link the project skills in each clone: mkdir -p .claude/skills && {links}")
            else:
                existing(key)
    return out


def unverified(report: dict, states: dict[str, str], pieces: dict[str, str], commands: list[Command], proof: dict | None, name: str) -> list[str]:
    out = []
    check_state = states.get(CHECK)
    ran_commit = proof is not None and proof["checks"]["state"] in ("yes", "no")
    if check_state in ("written", "unchanged"):
        for command in commands:
            if not (ran_commit and command.tier == "commit"):
                out.append(f"`{command.line()}` ({command.source}): detected, never run")
        out.append("bin/check integrate, nightly and verify-tree: never run by kitchen init")
    elif check_state == "edited by owner":
        out.append("bin/check was edited after kitchen generated it; kitchen no longer vouches for its commands")
    if states.get(HOOK) in OURS:
        out.append(f"{HOOK} is inactive until `git config core.hooksPath .githooks` in each clone")
        if proof is None:
            out.append(f"{HOOK}: gitleaks never ran")
    if any(pieces.get(p) == "verify-skill" and s in OURS for p, s in states.items()):
        out.append(f"verify-{name} is a skeleton: placeholders, no bin/verify, no feature mapped; it proves nothing yet")
    if any(pieces.get(p) == "agent-hooks" and s in OURS for p, s in states.items()):
        out.append(f"{repocheck.VENDORED_HOOKS}: Claude Code loads {repocheck.CLAUDE_SETTINGS} only in a session started at the repo root (measured)")
        out.append("Codex gets no project hooks from this branch: project hooks did not load in Codex 0.160 when measured; "
                   "a Codex session has the guards only where `kitchen install` ran")
    if states.get(BASELINE) in OURS:
        out.append(f"{BASELINE} is measure-only: no gate compares against it")
    if report["components"]:
        out.append("--check only reads lint configs and manifests; it never ran a linter, a build or a test")
    for m in report["must_haves"]:
        if m["status"] == "unknown":
            out.append(f"{m['label']}: unknown ({m['proof']})")
    return out


class Out:
    """Report lines; every text is escaped for control characters, so nothing from the repo can forge a line."""

    def __init__(self, markdown: bool):
        self.md = markdown
        self.lines: list[str] = []

    def head(self, text: str) -> None:
        self.lines += ["", f"## {safe(text)}", ""] if self.md else ["", safe(text)]

    def item(self, text: str, n: int | None = None) -> None:
        mark = f"{n}. " if n else ("- " if self.md else "")
        self.lines.append(f"{'' if self.md else '  '}{mark}{safe(text)}")

    def sub(self, text: str) -> None:
        self.lines.append(("   " if self.md else "       ") + safe(text))

    def code(self, text: str) -> None:
        lines = [safe(line) for line in text.splitlines()]
        if self.md:
            self.lines += ["", "   ```sh"] + [f"   {line}" for line in lines] + ["   ```", ""]
        else:
            self.lines += [("     $ " if i == 0 else "       ") + line for i, line in enumerate(lines)]


def render(result: dict, markdown: bool = False) -> str:
    out = Out(markdown)
    if markdown:
        out.lines += ["# kitchen init proposal", "",
                      f"Written by `kitchen init` from base {result['base'][:7]}. The owner reviews and pushes this branch; "
                      "kitchen never pushes, opens a pull request or changes GitHub settings."]
    else:
        ran = "--prove: RAN REPOSITORY CODE in a temporary worktree" if result["ran_repository_code"] else "ran no repository code"
        out.lines.append(f"kitchen init {result['path']}  ({ran})")
        sha = (result["branch_sha"] or "")[:7]
        if result["changed"]:
            out.lines.append(f"Branch {BRANCH} @ {sha} ({'new' if result['created'] else 'updated'}), from {result['base'][:7]}; not pushed")
        elif result["branch_sha"]:
            out.lines.append(f"Branch {BRANCH} @ {sha} (unchanged: nothing new to write)")
        else:
            out.lines.append("No branch: nothing to write")
    out.head(f"Measured by --check at {result['measured_at']} (that commit's tree; uncommitted changes are not part of the proposal)")
    for m in result["must_haves"]:
        out.item(f"{m['status']:<8} {m['label']:<34} {m['proof']}")
    out.head(f"Files on {BRANCH}")
    if not result["files"]:
        out.item("none")
    for i, f in enumerate(result["files"]):
        out.item(f"{f['state']:<16} {f['path']}")
        following = result["files"][i + 1] if i + 1 < len(result["files"]) else None
        if following and (following["piece"], following["state"], following["blocks"]) == (f["piece"], f["state"], f["blocks"]):
            continue  # one piece, several files: say what it does once, under its last file
        out.sub(f"does: {f['does']}")
        if f["state"] in ("written", "refreshed", "unchanged"):
            out.sub(f"would block today: {f['blocks']}")
    out.head("Proposals (not written: yours to apply)")
    if not result["proposals"]:
        out.item("none")
    for n, p in enumerate(result["proposals"], start=1):
        out.item(f"{p['id']}: {p['text']}", n)
    out.head("Unverified")
    for line in result["unverified"] or ["nothing listed"]:
        out.item(line)
    out.head("Readiness")
    labels = {"files_proposed": "files proposed", "checks_run_green": "checks run green",
              "negative_control_went_red": "negative control went red", "unattended_ready": "unattended-ready"}
    for key, label in labels.items():
        state = result["readiness"][key]
        out.item(f"{label:<27} {state['state']}: {state['detail']}")
    if result["trust"]:
        out.head("Trust per piece")
        for t in result["trust"]:
            out.item(f"{t['state']:<12} {t['path']}: {t['why']}")
    out.head("One-way doors: owner decisions, printed and never executed")
    for n, door in enumerate(result["doors"], start=1):
        out.item(f"{door['title']}. Recommended: {door['recommend']}.", n)
        out.code(door["command"])
    out.head("Next (two-way, yours)")
    for line in result["next"]:
        out.item(line)
    if result["notes"]:
        out.head("Notes")
        for line in result["notes"]:
            out.item(line)
    if not markdown and result.get("prove_tail"):
        out.head("Output of the red runs (last lines)")
        for label, lines in result["prove_tail"].items():
            out.item(label)
            for line in lines:
                out.sub(line)
    return "\n".join(out.lines) + "\n"


# ---- entry point -----------------------------------------------------------------------------------

def propose(path: Path, branch: str | None = None, run_proof: bool = False, log: Callable[[str], None] = lambda _: None) -> dict:
    """Write the proposal with git plumbing; only --prove checks out a worktree, because it runs repository code anyway."""
    original = repocheck.Repo(path.resolve())
    root = original.root
    head = original.git("rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    if not head:
        raise ProposeError(f"{root} has no commit to branch from")
    with interruptible():
        scratch = Path(tempfile.mkdtemp(prefix="kitchen-init-"))
        try:
            no_hooks = scratch / "no-hooks"
            no_hooks.mkdir()
            git = Git(no_hooks)
            target = git.run(root, "symbolic-ref", "-q", f"refs/heads/{BRANCH}")
            if target.returncode == 0:
                raise ProposeError(f"refs/heads/{BRANCH} is a symbolic ref to {target.stdout.decode().strip()}; "
                                   "refusing to move it. Delete it (git symbolic-ref -d refs/heads/kitchen/init), then rerun")
            elsewhere = checked_out_at(git, root)
            if elsewhere:
                raise ProposeError(f"{BRANCH} is checked out at {elsewhere}: switch that checkout to another branch, then rerun")
            existing = original.git("rev-parse", "--verify", "--quiet", f"refs/heads/{BRANCH}^{{commit}}")
            return build(git, root, head, existing, branch, run_proof, scratch, log)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)


def build(git: Git, root: Path, head: str, existing: str | None, branch: str | None, run_proof: bool,
          scratch: Path, log: Callable[[str], None]) -> dict:
    start = existing or head
    report = repocheck.check(root, branch, commit=start)
    repo = repocheck.Repo(root, start)
    manifest_state, manifest = read_manifest(repo)
    name = skill_name(root.name)
    status = {m["id"]: m["status"] for m in report["must_haves"]}
    origin = git.run(root, "config", "--get", "remote.origin.url").stdout.decode(errors="replace").strip()
    doors = one_way_doors(origin, status["branch-protection"], safe(root.name))
    commands, command_notes = detect_commands(repo, report["components"])
    wanted = {f.path: f for f in wanted_files(repo, report, name, doors, commands, command_notes)}
    entries = manifest.get("files", {})
    paths = list(wanted) + [p for p in entries if p not in wanted]
    states = {p: classify(git, repo, p, entries.get(p)) for p in paths}
    pieces = {p: wanted[p].piece if p in wanted else str(entries[p].get("piece", "")) for p in paths}
    notes: list[str] = []
    if existing and git.run(root, "merge-base", "--is-ancestor", head, existing).returncode != 0:
        notes.append(f"{BRANCH} does not contain HEAD ({head[:7]}); rebase it if the proposal should sit on today's HEAD")

    for p in paths:  # a copy of the kitchen's own file that kitchen wrote and nobody edited follows the kitchen
        if states[p] == "unchanged" and pieces[p] in VENDORED and p in wanted:
            states[p] = "refresh"
    to_write = [wanted[p] for p in paths if states[p] in ("write", "refresh")]
    report_entry = manifest.get("report") if isinstance(manifest.get("report"), dict) else None
    report_now = classify(git, repo, REPORT, report_entry) if to_write else "skip"
    write_manifest = bool(to_write) and manifest_state in ("absent", "unchanged")
    if to_write:
        refuse_unsafe_targets(repo.tree, [f.path for f in to_write] + ([MANIFEST] if write_manifest else [])
                              + ([REPORT] if report_now in ("write", "unchanged") else []))
    for f in to_write:
        if git.run(root, "check-ignore", "-q", "--no-index", "--", f.path).returncode == 0:
            notes.append(f"{f.path} matches a .gitignore rule; it is committed anyway. Consider `!{f.path}` in .gitignore")
    pieces_commit = start
    if to_write:
        listing = "\n".join(f"- {f.path}" for f in to_write)
        pieces_commit = commit_files(git, root, start, [(f.path, f.content.encode(), "100755" if f.mode & 0o111 else "100644") for f in to_write],
                                     f"kitchen init: propose the missing pieces\n\n{listing}\n", scratch / "index")
        for f in to_write:
            states[f.path] = "refreshed" if states[f.path] == "refresh" else "written"

    proof = None
    if run_proof:
        proof = prove_in_worktree(git, root, pieces_commit, states.get(HOOK) in OURS, scratch, log)

    files = []
    for p in paths:
        content = wanted[p].content if states[p] in ("written", "refreshed") else (repo.read(p) if repo.is_file(p) else None)
        files.append({"path": p, "piece": pieces[p], "state": states[p], "does": DOES.get(pieces[p], ""),
                      "blocks": blocks(pieces[p], content, proof)})
    next_steps = []
    if to_write or existing:
        next_steps.append(f"review the branch (`git diff HEAD...{BRANCH}`), then push it yourself: `git push -u origin {BRANCH}`")
    if states.get(HOOK) in OURS:
        next_steps.append("after it merges, activate the hook in each clone: `git config core.hooksPath .githooks`")
    if not next_steps:
        next_steps.append("nothing to push")
    if to_write and not write_manifest:
        why = "is not kitchen's" if manifest_state == "foreign" else "was edited after kitchen wrote it"
        notes.append(f"{MANIFEST} {why}: left alone, so the files written now are not recorded in it, and a rerun treats them as the owner's")
    result = {
        "path": str(root),
        "branch": BRANCH,
        "base": str(manifest.get("base") or head),
        "measured_at": report["head"],
        "ran_repository_code": run_proof,
        "must_haves": [{"id": m["id"], "label": m["label"], "status": m["status"], "proof": m["proof"]} for m in report["must_haves"]],
        "files": files,
        "proposals": proposals(report, states, pieces, name, repo),
        "unverified": unverified(report, states, pieces, commands, proof, name),
        "readiness": readiness(states, len(to_write), proof),
        "trust": trust_lines(states, pieces, proof, proof["check_present"] if proof else repo.is_file(CHECK) or CHECK in [f.path for f in to_write]),
        "doors": doors,
        "next": next_steps,
        "notes": notes,
    }
    if proof:
        tails = {}
        if proof.get("green") and proof["green"]["exit"] != 0:
            tails["bin/check commit"] = proof["green"]["tail"]
        if proof["control"].get("result"):
            tails[f"bin/check commit under the negative control ({proof['control']['target']})"] = proof["control"]["result"]["tail"]
        result["prove_tail"] = tails
    ready = result["readiness"]
    result["exit"] = 1 if run_proof and (ready["checks_run_green"]["state"] != "yes" or ready["negative_control_went_red"]["state"] != "yes") else 0

    final = existing
    report_state = None
    if to_write:
        bookkeeping: list[tuple[str, bytes, str]] = []
        markdown = render(result, markdown=True).replace(str(root), "<repo>").replace(os.path.expanduser("~"), "~")
        if report_now in ("write", "unchanged"):
            bookkeeping.append((REPORT, markdown.encode(), "100644"))
            report_entry = {"path": REPORT, "sha256": sha256(markdown.encode())}
            report_state = "written"
        else:
            why = "exists and is not kitchen's" if report_now == "exists" else f"was {report_now}"
            report_state = f"not written: {REPORT} {why}"
            notes.append(f"{REPORT} {why}, so the report is only printed")
        if write_manifest:
            data = {**manifest, "generator": GENERATOR, "version": 1, "base": result["base"],
                    "files": dict(sorted({**entries, **{f.path: {"piece": f.piece, "sha256": sha256(f.content.encode())} for f in to_write}}.items()))}
            if report_entry:
                data["report"] = report_entry
            data["sha256"] = manifest_hash(data)
            bookkeeping.append((MANIFEST, (json.dumps(data, indent=2) + "\n").encode(), "100644"))
        final = pieces_commit
        if bookkeeping:
            proof_sha = proof["sha"][:7] if proof else None
            final = commit_files(git, root, pieces_commit, bookkeeping, "kitchen init: report and manifest\n\n"
                                 + (f"--prove ran at {proof_sha}.\n" if proof_sha else "Not proved: rerun with --prove.\n"), scratch / "index")
        zero = "0" * len(final)
        git(root, "update-ref", "--no-deref", "-m", "kitchen init", f"refs/heads/{BRANCH}", final, existing or zero)
    result.update({"branch_sha": final, "created": bool(to_write) and not existing, "changed": bool(to_write), "report_file": report_state})
    return result


def prove_in_worktree(git: Git, root: Path, commit: str, hook_ours: bool, scratch: Path, log: Callable[[str], None]) -> dict:
    """The only place a worktree exists. Its checkout may run the target's filters (and kitchen's empty hooksPath keeps
    hooks out); then the proof runs repository code on purpose."""
    target = control_target(repocheck.Repo(root, commit))  # chosen from the commit's tracked files, before anything runs
    wt = scratch / "worktree"
    log(f"kitchen init --prove: checking out {commit[:7]} in {wt}; the target's git filters (smudge) may run here")
    try:
        git(root, "worktree", "add", "--detach", "--quiet", str(wt), commit)
        proof = prove(git, wt, target, hook_ours, scratch, log)
        proof["check_present"] = (wt / CHECK).is_file()
        for key in ("green",):
            if key in proof:
                proof[key] = {k: v for k, v in proof[key].items() if k != "output"}
        sanitize = lambda text: text.replace(os.path.realpath(wt), "<worktree>").replace(str(wt), "<worktree>")
        for section in ("green",):
            if section in proof:
                proof[section]["tail"] = [sanitize(line) for line in proof[section]["tail"]]
        if proof["control"].get("result"):
            proof["control"]["result"]["tail"] = [sanitize(line) for line in proof["control"]["result"]["tail"]]
        return proof
    finally:
        removed = git.run(root, "worktree", "remove", "--force", str(wt))
        git.run(root, "worktree", "prune")
        if removed.returncode != 0 and wt.exists():
            log(f"kitchen init --prove: could not remove the temporary worktree {wt}: {removed.stderr.decode(errors='replace').strip()}")
