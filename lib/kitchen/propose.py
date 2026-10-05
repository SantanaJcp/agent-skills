"""`kitchen adopt --propose`: write only what a repo is missing, on branch kitchen/adopt, never pushed.

Stage 2 of adopt. It makes a temporary worktree of the target repo, detached at `kitchen/adopt` when that branch
exists and at HEAD otherwise, runs `--check` there, and writes from templates/ only the files that are missing:
decisions.md, bin/check, .githooks/pre-commit, a verify-skill skeleton and a measure-only baseline. It never
overwrites, edits or deletes a file, and writes no AGENTS.md prose. .kitchen/adopt.json records the path and
sha256 of every file it generated, so a rerun tells kitchen's untouched files from the owner's edits and leaves
the edits alone; a rerun with nothing new to write commits nothing. ADOPT.md holds the report. The branch ref
moves once, at the end, by compare-and-swap. It never pushes, opens a PR or changes GitHub settings: one-way
doors are printed as numbered decisions with their commands.

Every git command here runs with core.hooksPath pointed at an empty directory and commits are built with
plumbing, so no hook of the target repo runs. Without --prove nothing from the target repo executes.

Stage 3, `--prove`, RUNS REPOSITORY CODE in the temporary worktree, at the proposal's commit: `bin/check commit`
once, then a negative control (a syntax error appended to a tracked test or source file) that must turn it red,
then the revert; and the proposed hook against a docs-only commit and a staged fake key.
"""
from __future__ import annotations

import collections
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

from kitchen import adopt

BRANCH = "kitchen/adopt"
MANIFEST = ".kitchen/adopt.json"
REPORT = "ADOPT.md"
BASELINE = ".kitchen/baseline.json"
HOOK = ".githooks/pre-commit"
CHECK = "bin/check"
TEMPLATES = Path(__file__).resolve().parents[2] / "templates"
PROVE_TIMEOUT_SECONDS = 900
GITLEAKS_TIMEOUT_SECONDS = 120
TAIL_LINES = 12
CONTROL_FILE = "kitchen-adopt-control.md"
OURS = ("written", "unchanged", "edited by owner")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TEST_SDK = re.compile(r"Microsoft\.NET\.Test\.Sdk|<IsTestProject>\s*true", re.IGNORECASE)
SYNTAX = "\n) {} kitchen adopt negative control: deliberate syntax error\n"
BREAKERS = {".py": SYNTAX.format("#"), ".cs": "\n#error kitchen adopt negative control: deliberate compile error\n",
            **{suffix: SYNTAX.format("//") for suffix in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx")}}

DOES = {
    "decisions": "Dated decisions; `- [ ]` marks one the owner still owes, and `kitchen status` counts them.",
    "check-contract": "The one check contract: tiers commit, integrate, nightly and verify-tree, filled from the manifests; `--list` prints them.",
    "pre-commit-hook": "gitleaks on the staged changes (fails with the install command when gitleaks is missing), then `bin/check commit` "
                       "unless only documentation is staged. Inactive until `git config core.hooksPath .githooks` in each clone.",
    "verify-skill": "Skeleton of the project's verify skill from templates/verify: placeholders to fill, no bin/verify yet.",
    "baseline-ratchet": "What --check measured, in measure-only mode: no gate reads it yet.",
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
    """git in the target repo with an empty hooks directory: no hook of the repo runs while kitchen writes."""

    def __init__(self, no_hooks: Path):
        self.no_hooks = no_hooks

    def run(self, cwd: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={self.no_hooks}", "-C", str(cwd), *args],
                              capture_output=True, text=True, env=adopt.git_env())

    def __call__(self, cwd: Path, *args: str) -> str:
        result = self.run(cwd, *args)
        if result.returncode != 0:
            raise ProposeError(f"git {' '.join(args)}: {result.stderr.strip() or 'exit ' + str(result.returncode)}")
        return result.stdout.strip()


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

def python_lint(repo: adopt.Repo, directory: str) -> tuple[str, str] | None:
    found = repo.find_up(directory, ("ruff.toml", ".ruff.toml"))
    if found:
        return "ruff check .", f"ruff config {found}"
    for folder in adopt.ancestors(directory):
        rel = adopt.join(folder, "pyproject.toml")
        if rel in repo.fileset:
            try:
                tools = tomllib.loads(repo.read(rel) or "").get("tool", {})
            except tomllib.TOMLDecodeError:
                tools = {}
            if "ruff" in tools:
                return "ruff check .", f"[tool.ruff] in {rel}"
    found = repo.find_up(directory, (".flake8",)) or repo.find_up(directory, ("setup.cfg", "tox.ini"), re.compile(r"^\[flake8\]", re.MULTILINE))
    return ("flake8", f"flake8 config {found}") if found else None


def pytest_signal(repo: adopt.Repo, directory: str) -> str | None:
    for name in ("pytest.ini", "conftest.py"):
        if adopt.join(directory, name) in repo.fileset:
            return f"pytest: {adopt.join(directory, name)}"
    pyproject = adopt.join(directory, "pyproject.toml")
    text = repo.read(pyproject) or ""
    if "[tool.pytest" in text:
        return f"pytest: [tool.pytest.ini_options] in {pyproject}"
    for name, marker in (("setup.cfg", "[tool:pytest]"), ("tox.ini", "[pytest]")):
        if marker in (repo.read(adopt.join(directory, name)) or ""):
            return f"pytest: {marker} in {adopt.join(directory, name)}"
    for rel in repo.files:
        if adopt.parent(rel) == directory and re.fullmatch(r"requirements[\w.-]*\.txt", PurePosixPath(rel).name) \
                and re.search(r"^\s*pytest\b", repo.read(rel) or "", re.MULTILINE):
            return f"pytest: listed in {rel}"
    if re.search(r"[\"']pytest\b", text):
        return f"pytest: a dependency in {pyproject}"
    return None


def python_commands(repo: adopt.Repo, directory: str) -> tuple[list[Command], list[str]]:
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
            commands.append(Command("commit", f"python3 -m unittest discover -s {start}", f"unittest: test files under {adopt.join(directory, start)}/", directory))
        else:
            commands.append(Command("commit", "python3 -m unittest discover", f"unittest: {adopt.join(directory, tests[0])}", directory))
    else:
        notes.append(f"{directory or '.'}: no test*.py file and no pytest config, so no test command")
    return commands, notes


def node_commands(repo: adopt.Repo, directory: str, manifest: str, lint_found: bool) -> tuple[list[Command], list[str]]:
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


def dotnet_commands(repo: adopt.Repo, directory: str, manifest: str) -> tuple[list[Command], list[str]]:
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


def detect_commands(repo: adopt.Repo, components: list[dict]) -> tuple[list[Command], list[str]]:
    commands: list[Command] = []
    notes: list[str] = []
    for component in components:
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
            lines += [f"  # unverified: {command.source}", f"  {command.line()}"]
        return lines
    commit = [f"  # {note}" for note in notes] + body("commit")
    if not any(c.tier == "commit" for c in commands):
        commit += ['  echo "bin/check commit: no command detected; add one" >&2', "  exit 1"]
    return template("adopt/check.sh.tmpl", commit="\n".join(commit), integrate="\n".join(["  tier_commit"] + body("integrate")))


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
        "note": "Seeded by kitchen adopt --propose from what --check measured. No gate reads it yet; it becomes a ratchet "
                "only when a gate compares against it and fails when a value gets worse.",
        "measured_at": report["head"],
        "must_haves": {m["id"]: m["status"] for m in report["must_haves"]},
        "components": components,
    }
    return json.dumps(data, indent=2) + "\n"


def one_way_doors(origin_url: str, protection: str, project: str) -> list[dict]:
    match = adopt.GITHUB_REMOTE.search(origin_url)
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


def wanted_files(repo: adopt.Repo, report: dict, name: str, doors: list[dict], commands: list[Command], notes: list[str]) -> list[File]:
    status = {m["id"]: m["status"] for m in report["must_haves"]}
    exists = lambda rel: os.path.lexists(repo.root / rel)
    files = []
    if status["decisions"] != "PASS":
        owed = "\n".join(f"- [ ] {d['title']} (one-way door, proposed by kitchen adopt; see ADOPT.md)" for d in doors) or "None yet."
        files.append(File("decisions.md", "decisions", template("adopt/decisions.md.tmpl", owed=owed)))
    if status["check-contract"] != "PASS" and report["stack_status"] == "detected" and not exists(CHECK) and not exists(".kitchen/checks.toml"):
        files.append(File(CHECK, "check-contract", render_check(commands, notes), 0o755))
    hook_candidates = [f for f in repo.files if PurePosixPath(f).name == "pre-commit"] + report["hooks"]["managers"]
    if (status["pre-commit-hook"] != "PASS" or status["secret-scan"] != "PASS") and not report["hooks"]["active"] and not hook_candidates:
        files.append(File(HOOK, "pre-commit-hook", template("adopt/pre-commit.sh.tmpl"), 0o755))
    if status["verify-skill"] != "PASS" and not any(f.startswith(".agents/skills/verify-") for f in repo.files):
        skill = (TEMPLATES / "verify" / "SKILL.md.tmpl").read_text().replace("<repo>", name)
        files += [File(f".agents/skills/verify-{name}/SKILL.md", "verify-skill", skill),
                  File(f".agents/skills/verify-{name}/features/README.md", "verify-skill", template("adopt/features-README.md.tmpl"))]
    if status["baseline-ratchet"] != "PASS" and not adopt.baseline_candidates(repo):
        files.append(File(BASELINE, "baseline-ratchet", baseline(report)))
    return files


# ---- manifest and writing ----------------------------------------------------------------------------

def load_manifest(wt: Path) -> dict:
    path = wt / MANIFEST
    if not os.path.lexists(path):
        return {"files": {}}
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProposeError(f"{MANIFEST} on the branch cannot be read ({error}); fix or remove it, then rerun")
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise ProposeError(f"{MANIFEST} on the branch has no files map; fix or remove it, then rerun")
    return data


def classify(wt: Path, path: str, entry: dict | None) -> str:
    target = wt / path
    present = os.path.lexists(target)
    if entry is not None:
        if not present:
            return "deleted by owner"
        if target.is_symlink() or not target.is_file():
            return "edited by owner"
        return "unchanged" if sha256(target.read_bytes()) == entry.get("sha256") else "edited by owner"
    return "exists" if present else "write"


def write_new(wt: Path, path: str, content: str, mode: int) -> None:
    current = wt
    for part in PurePosixPath(path).parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise ProposeError(f"{path}: {current.relative_to(wt)} is a symlink or a file; refusing to write through it")
    target = wt / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "x", encoding="utf-8", newline="\n") as handle:  # "x": an existing file is never overwritten
        handle.write(content)
    os.chmod(target, mode)


def commit(git: Git, wt: Path, paths: list[str], message: str) -> str:
    git(wt, "add", "-f", "--", *paths)
    parent = git(wt, "rev-parse", "HEAD")
    sha = git(wt, "commit-tree", git(wt, "write-tree"), "-p", parent, "-m", message)
    git(wt, "update-ref", "--no-deref", "HEAD", sha, parent)
    return sha


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
           if k not in adopt.REPO_LOCAL_GIT_ENV and not k.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))}
    return {**env, "TMPDIR": str(tmp), "TMP": str(tmp), "TEMP": str(tmp)}


def run_code(argv: list[str], cwd: Path, tmp: Path, timeout: int = PROVE_TIMEOUT_SECONDS) -> dict:
    """Run repository code; exit None means it never finished (timeout) or never started."""
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=repo_code_env(tmp), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    except OSError as error:
        return {"exit": None, "why": f"cannot run {argv[0]}: {error.strerror}", "tail": []}
    try:
        out, _ = process.communicate(timeout=timeout)
        result = {"exit": process.returncode, "why": f"exit {process.returncode}"}
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        out, _ = process.communicate()
        result = {"exit": None, "why": f"timed out after {timeout}s"}
    lines = [ANSI.sub("", line).rstrip() for line in out.decode("utf-8", errors="replace").splitlines()]
    return {**result, "tail": [line for line in lines if line.strip()][-TAIL_LINES:]}


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


def control_target(repo: adopt.Repo) -> str | None:
    """The file the negative control breaks: the first tracked test file, else the first tracked source file."""
    breakable = lambda rel: PurePosixPath(rel).suffix in BREAKERS and not rel.startswith((".agents/", ".kitchen/")) \
        and not (repo.root / rel).is_symlink()
    tests = sorted(f for f in adopt.test_files(repo) if breakable(f))
    if tests:
        return tests[0]
    sources = sorted(f for f in repo.files if breakable(f))
    return sources[0] if sources else None


def negative_control(git: Git, wt: Path, target: str | None, tmp: Path, log: Callable[[str], None]) -> dict:
    if target is None:
        return {"state": "not run", "detail": "no tracked test or source file (.py, .js, .ts, .cs...) to break"}
    path = wt / target
    original = path.read_bytes()
    change = f"a {'compile' if path.suffix == '.cs' else 'syntax'} error appended to {target}"
    log(f"kitchen adopt --prove: negative control, {change}; bin/check commit must go red")
    try:
        with open(path, "ab") as handle:
            handle.write(BREAKERS[path.suffix].encode())
        red = run_code([str(wt / CHECK), "commit"], wt, tmp)
    finally:
        path.write_bytes(original)
    if git.run(wt, "diff", "--quiet", "HEAD", "--", target).returncode != 0:
        raise ProposeError(f"the negative control on {target} could not be reverted in the temporary worktree")
    went_red = red["exit"] not in (0, None)
    return {"state": "yes" if went_red else "no", "target": target, "change": change, "result": red,
            "detail": f"bin/check commit {red['why']} after {change}; reverted"}


def prove_hook(git: Git, wt: Path, tmp: Path, log: Callable[[str], None]) -> dict:
    control = wt / CONTROL_FILE
    if os.path.lexists(control):
        return {"state": "untrusted", "why": f"{CONTROL_FILE} already exists, and the hook's controls need that path"}
    log(f"kitchen adopt --prove: running {HOOK} against a staged docs-only change, then a staged fake key")
    try:
        control.write_text("kitchen adopt positive control: documentation only\n")
        git(wt, "add", "-f", "--", CONTROL_FILE)
        allowed = run_code([str(wt / HOOK)], wt, tmp)
        control.write_text("kitchen adopt negative control\naws_access_key_id = " + fake_aws_key() + "\n")
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


def prove(git: Git, wt: Path, hook_ours: bool, scratch: Path, log: Callable[[str], None]) -> dict:
    head = git(wt, "rev-parse", "HEAD")
    target = control_target(adopt.Repo(wt))  # chosen before anything runs, from tracked files only
    tmp = scratch / "tmp"  # TMPDIR for repository code
    tmp.mkdir()
    proof: dict = {"sha": head, "gitleaks_tree": gitleaks_tree(wt, scratch), "hook": None}
    if not (wt / CHECK).is_file():
        why = "no bin/check to run" + ("; --prove does not run .kitchen/checks.toml" if (wt / ".kitchen" / "checks.toml").is_file() else "")
        proof["checks"] = {"state": "not run", "detail": why}
        proof["control"] = {"state": "not run", "detail": "no bin/check to turn red"}
    else:
        log(f"kitchen adopt --prove: running bin/check commit in {wt}")
        green = run_code([str(wt / CHECK), "commit"], wt, tmp)
        proof["green"] = green
        if green["exit"] == 0:
            proof["checks"] = {"state": "yes", "detail": f"bin/check commit exit 0 at {head[:7]}"}
            proof["control"] = negative_control(git, wt, target, tmp, log)
        else:
            proof["checks"] = {"state": "no", "detail": f"bin/check commit {green['why']} at {head[:7]}"}
            proof["control"] = {"state": "not run", "detail": "bin/check commit is red before the control, so a red control would prove nothing"}
    if hook_ours:
        proof["hook"] = prove_hook(git, wt, tmp, log)
    return proof


# ---- the report ------------------------------------------------------------------------------------

def blocks(piece: str, content: str | None, proof: dict | None) -> str:
    if piece == "decisions":
        owed = len(re.findall(r"^\s*- \[ \]", content or "", re.MULTILINE))
        return f"nothing; it lists {owed} owed decision{'s' if owed != 1 else ''} for `kitchen status`"
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
        elif proof["control"]["state"] == "yes":
            out.append({"path": CHECK, "state": "trusted", "why": f"green, then red under its negative control ({proof['control']['change']})"})
        elif proof["control"]["state"] == "no":
            out.append({"path": CHECK, "state": "untrusted", "why": f"stayed green under its negative control ({proof['control']['change']})"})
        else:
            out.append({"path": CHECK, "state": "untrusted", "why": f"negative control not run: {proof['control']['detail']}"})
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
             if present else {"state": "no", "detail": "nothing is missing that kitchen adopt writes"})
    if proof is None:
        rerun = "rerun with --prove (it runs repository code)"
        return {"files_proposed": files, "checks_run_green": {"state": "not run", "detail": rerun},
                "negative_control_went_red": {"state": "not run", "detail": rerun},
                "unattended_ready": {"state": "not assessed", "detail": "kitchen adopt does not assess unattended runs (sandbox, schedule, credentials)"}}
    controls = [proof["control"]]
    if proof["hook"]:
        hook = proof["hook"]
        controls.append({"state": {"trusted": "yes", "untrusted": "no"}[hook["state"]], "detail": f"{HOOK}: {hook['why']}"})
    states_seen = {c["state"] for c in controls}
    red = "yes" if states_seen == {"yes"} else "no" if "no" in states_seen else "not run"
    return {"files_proposed": files, "checks_run_green": proof["checks"],
            "negative_control_went_red": {"state": red, "detail": "; ".join(c["detail"] for c in controls)},
            "unattended_ready": {"state": "not assessed", "detail": "kitchen adopt does not assess unattended runs (sandbox, schedule, credentials)"}}


def proposals(report: dict, states: dict[str, str], pieces: dict[str, str], name: str) -> list[dict]:
    status = {m["id"]: m for m in report["must_haves"]}
    steps = {s["id"]: s["step"] for s in report["next_steps"]}
    ours = {pieces[p] for p, s in states.items() if s in OURS}
    out = []
    def add(key: str, text: str) -> None:
        out.append({"id": key, "text": text})
    def existing(key: str) -> None:
        add(key, f"{status[key]['proof']}. {steps.get(key, '')}".strip())
    for key in ("check-contract", "pre-commit-hook", "secret-scan", "agents-md", "verify-skill", "baseline-ratchet", "skills-linked"):
        if status[key]["status"] == "PASS":
            continue
        if key == "check-contract" and "check-contract" not in ours:
            if report["stack_status"] != "detected":
                add(key, "unsupported stack (no .NET, Node or Python manifest): write bin/check by hand with the tiers commit, integrate, "
                         "nightly and verify-tree; kitchen adopt does not guess commands")
            else:
                existing(key)
        elif key in ("pre-commit-hook", "secret-scan") and "pre-commit-hook" not in ours:
            if key == "secret-scan" and report["hooks"]["active"]:
                add(key, f"add `gitleaks git --pre-commit --staged` to {report['hooks']['pre_commit']}, failing when gitleaks is missing")
            else:
                existing(key)
        elif key == "agents-md":
            if report["agent_files"]["AGENTS.md"] is None:
                add(key, "AGENTS.md is missing, and kitchen adopt writes no prose. Draft one with Claude Code's init: run "
                         "`CLAUDE_CODE_NEW_INIT=1 claude`, then `/init`; keep only verified commands, name `bin/check` and the verify "
                         "skill, and stay under 200 lines.")
            else:
                existing(key)
        elif key in ("verify-skill", "baseline-ratchet") and key not in ours:
            existing(key)
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
        out.append("bin/check integrate, nightly and verify-tree: never run by kitchen adopt")
    elif check_state == "edited by owner":
        out.append("bin/check was edited after kitchen generated it; kitchen no longer vouches for its commands")
    if states.get(HOOK) in OURS:
        out.append(f"{HOOK} is inactive until `git config core.hooksPath .githooks` in each clone")
        if proof is None:
            out.append(f"{HOOK}: gitleaks never ran")
    if any(pieces.get(p) == "verify-skill" and s in OURS for p, s in states.items()):
        out.append(f"verify-{name} is a skeleton: placeholders, no bin/verify, no feature mapped; it proves nothing yet")
    if states.get(BASELINE) in OURS:
        out.append(f"{BASELINE} is measure-only: no gate compares against it")
    if report["components"]:
        out.append("--check only reads lint configs and manifests; it never ran a linter, a build or a test")
    for m in report["must_haves"]:
        if m["status"] == "unknown":
            out.append(f"{m['label']}: unknown ({m['proof']})")
    return out


class Out:
    def __init__(self, markdown: bool):
        self.md = markdown
        self.lines: list[str] = []

    def head(self, text: str) -> None:
        self.lines += ["", f"## {text}", ""] if self.md else ["", text]

    def item(self, text: str, n: int | None = None) -> None:
        mark = f"{n}. " if n else ("- " if self.md else "")
        self.lines.append(f"{'' if self.md else '  '}{mark}{text}")

    def sub(self, text: str) -> None:
        self.lines.append(("   " if self.md else "       ") + text)

    def code(self, text: str) -> None:
        if self.md:
            self.lines += ["", "   ```sh"] + [f"   {line}" for line in text.splitlines()] + ["   ```", ""]
        else:
            self.lines += [("     $ " if i == 0 else "       ") + line for i, line in enumerate(text.splitlines())]


def render(result: dict, markdown: bool = False) -> str:
    out = Out(markdown)
    if markdown:
        out.lines += ["# kitchen adopt proposal", "",
                      f"Written by `kitchen adopt --propose` from base {result['base'][:7]}. The owner reviews and pushes this branch; "
                      "kitchen never pushes, opens a pull request or changes GitHub settings."]
    else:
        ran = "--prove: RAN REPOSITORY CODE in a temporary worktree" if result["ran_repository_code"] else "ran no repository code"
        out.lines.append(f"kitchen adopt --propose {result['path']}  ({ran})")
        sha = (result["branch_sha"] or "")[:7]
        if result["changed"]:
            out.lines.append(f"Branch {BRANCH} @ {sha} ({'new' if result['created'] else 'updated'}), from {result['base'][:7]}; not pushed")
        elif result["branch_sha"]:
            out.lines.append(f"Branch {BRANCH} @ {sha} (unchanged: nothing new to write)")
        else:
            out.lines.append("No branch: nothing to write")
    out.head(f"Measured by --check at {result['measured_at'] or 'no commit'}")
    for m in result["must_haves"]:
        out.item(f"{m['status']:<8} {m['label']:<34} {m['proof']}")
    out.head(f"Files on {BRANCH}")
    if not result["files"]:
        out.item("none")
    for f in result["files"]:
        out.item(f"{f['state']:<16} {f['path']}")
        out.sub(f"does: {f['does']}")
        if f["state"] in ("written", "unchanged"):
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
    original = adopt.Repo(path.resolve())
    root = original.root
    head = original.git("rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    if not head:
        raise ProposeError(f"{root} has no commit to branch from")
    scratch = Path(tempfile.mkdtemp(prefix="kitchen-adopt-"))
    try:
        no_hooks = scratch / "no-hooks"
        no_hooks.mkdir()
        git = Git(no_hooks)
        elsewhere = checked_out_at(git, root)
        if elsewhere:
            raise ProposeError(f"{BRANCH} is checked out at {elsewhere}: switch that checkout to another branch, then rerun")
        existing = original.git("rev-parse", "--verify", "--quiet", f"refs/heads/{BRANCH}^{{commit}}")
        wt = scratch / "worktree"
        git(root, "worktree", "add", "--detach", "--quiet", str(wt), existing or head)
        try:
            result = build(git, root, wt, head, existing, branch, run_proof, scratch, log)
        finally:
            removed = git.run(root, "worktree", "remove", "--force", str(wt))
            git.run(root, "worktree", "prune")
        if removed.returncode != 0:
            raise ProposeError(f"the temporary worktree {wt} could not be removed: {removed.stderr.strip()}"
                               + (f" (branch {BRANCH} is at {result['branch_sha'][:7]})" if result.get("branch_sha") else ""))
        return result
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def build(git: Git, root: Path, wt: Path, head: str, existing: str | None, branch: str | None, run_proof: bool,
          scratch: Path, log: Callable[[str], None]) -> dict:
    report = adopt.check(wt, branch)
    repo = adopt.Repo(wt)
    manifest = load_manifest(wt)
    name = skill_name(root.name)
    status = {m["id"]: m["status"] for m in report["must_haves"]}
    doors = one_way_doors(git.run(root, "config", "--get", "remote.origin.url").stdout.strip(), status["branch-protection"], root.name)
    commands, command_notes = detect_commands(repo, report["components"])
    wanted = {f.path: f for f in wanted_files(repo, report, name, doors, commands, command_notes)}
    entries = manifest["files"]
    paths = list(wanted) + [p for p in entries if p not in wanted]
    states = {p: classify(wt, p, entries.get(p)) for p in paths}
    pieces = {p: wanted[p].piece if p in wanted else entries[p].get("piece", "") for p in paths}
    notes: list[str] = []
    if git.run(root, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        notes.append(f"the checkout has uncommitted changes; the proposal starts from a commit ({(existing or head)[:7]}), so they are not part of it")
    if existing and git.run(root, "merge-base", "--is-ancestor", head, existing).returncode != 0:
        notes.append(f"{BRANCH} does not contain HEAD ({head[:7]}); rebase it if the proposal should sit on today's HEAD")

    to_write = [wanted[p] for p in paths if states[p] == "write"]
    for f in to_write:
        if git.run(wt, "check-ignore", "-q", "--", f.path).returncode == 0:
            notes.append(f"{f.path} matches a .gitignore rule; it is tracked anyway (git add -f). Consider `!{f.path}` in .gitignore")
        write_new(wt, f.path, f.content, f.mode)
    if to_write:
        listing = "\n".join(f"- {f.path}" for f in to_write)
        commit(git, wt, [f.path for f in to_write], f"kitchen adopt: propose the missing pieces\n\n{listing}\n")
        for f in to_write:
            states[f.path] = "written"

    proof = None
    if run_proof:
        proof = prove(git, wt, states.get(HOOK) in OURS, scratch, log)

    files = []
    for p in paths:
        content = (wt / p).read_text(errors="replace") if (wt / p).is_file() else None
        files.append({"path": p, "piece": pieces[p], "state": states[p], "does": DOES.get(pieces[p], ""),
                      "blocks": blocks(pieces[p], content, proof)})
    next_steps = []
    if to_write or existing:
        next_steps.append(f"review the branch (`git diff HEAD...{BRANCH}`), then push it yourself: `git push -u origin {BRANCH}`")
    if states.get(HOOK) in OURS:
        next_steps.append("after it merges, activate the hook in each clone: `git config core.hooksPath .githooks`")
    if not next_steps:
        next_steps.append("nothing to push")
    sanitize = lambda text: text.replace(os.path.realpath(wt), "<worktree>").replace(str(wt), "<worktree>")
    result = {
        "path": str(root),
        "branch": BRANCH,
        "base": manifest.get("base") or head,
        "measured_at": report["head"],
        "ran_repository_code": run_proof,
        "must_haves": [{"id": m["id"], "label": m["label"], "status": m["status"], "proof": sanitize(m["proof"])} for m in report["must_haves"]],
        "files": files,
        "proposals": [{**p, "text": sanitize(p["text"])} for p in proposals(report, states, pieces, name)],
        "unverified": [sanitize(line) for line in unverified(report, states, pieces, commands, proof, name)],
        "readiness": readiness(states, len(to_write), proof),
        "trust": trust_lines(states, pieces, proof, (wt / CHECK).is_file()),
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
        result["prove_tail"] = {k: [sanitize(line) for line in v] for k, v in tails.items()}
    ready = result["readiness"]
    result["exit"] = 1 if run_proof and (ready["checks_run_green"]["state"] != "yes" or ready["negative_control_went_red"]["state"] != "yes") else 0

    final = existing
    report_state = None
    if to_write:
        new_entries = {**entries, **{f.path: {"piece": f.piece, "sha256": sha256(f.content.encode())} for f in to_write}}
        bookkeeping = []
        report_entry = manifest.get("report")
        report_now = classify(wt, REPORT, report_entry if isinstance(report_entry, dict) else None)
        markdown = render(result, markdown=True).replace(str(root), "<repo>").replace(os.path.expanduser("~"), "~")
        if report_now in ("write", "unchanged"):
            (wt / REPORT).unlink(missing_ok=True)
            write_new(wt, REPORT, markdown, 0o644)
            bookkeeping.append(REPORT)
            report_entry = {"path": REPORT, "sha256": sha256(markdown.encode())}
            report_state = "written"
        else:
            why = "exists and is not kitchen's" if report_now == "exists" else f"was {report_now}"
            report_state = f"not written: {REPORT} {why}"
            notes.append(f"{REPORT} {why}, so the report is only printed")
        data = {"generator": "kitchen adopt --propose", "version": 1, "base": result["base"], "files": dict(sorted(new_entries.items()))}
        if report_entry:
            data["report"] = report_entry
        (wt / MANIFEST).unlink(missing_ok=True)
        write_new(wt, MANIFEST, json.dumps(data, indent=2) + "\n", 0o644)
        bookkeeping.append(MANIFEST)
        proof_sha = proof["sha"][:7] if proof else None
        final = commit(git, wt, bookkeeping, "kitchen adopt: report and manifest\n\n"
                       + (f"--prove ran at {proof_sha}.\n" if proof_sha else "Not proved: rerun with --prove.\n"))
        zero = "0" * len(final)
        git(root, "update-ref", "-m", "kitchen adopt --propose", f"refs/heads/{BRANCH}", final, existing or zero)
    result.update({"branch_sha": final, "created": bool(to_write) and not existing, "changed": bool(to_write), "report_file": report_state})
    return result
