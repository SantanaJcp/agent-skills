"""`kitchen adopt --check`: what a repo still needs for an agent loop that can be trusted. Read-only.

It reads files and git metadata, plus GET-only `gh api` calls with a timeout when gh is installed.
It never runs repository code: no hooks, no package scripts, no `bin/check`. Every criterion is
PASS, FAIL or unknown, with the file or command that proves it. unknown never counts as PASS: the
exit code is the number of must-haves that are not PASS.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path, PurePosixPath

TIERS = ("commit", "integrate", "nightly", "verify-tree")
MAX_AGENTS_LINES = 200
MAX_READ_BYTES = 1_000_000
GH_TIMEOUT_SECONDS = 15
NOT_A_REPO = 64  # outside 0..len(MUST_HAVES), so it never reads as a count of missing must-haves

MUST_HAVES = (
    ("check-contract", "check contract"),
    ("pre-commit-hook", "pre-commit hook active"),
    ("agents-md", "AGENTS.md"),
    ("verify-skill", "verify skill + map guard"),
    ("decisions", "decisions.md"),
    ("secret-scan", "secret scan in hook"),
    ("baseline-ratchet", "baseline ratchet"),
    ("skills-linked", "skills in .claude/skills"),
    ("branch-protection", "required status on shared branch"),
)

LOCKFILES = ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb")
NODE_LINT = tuple(f"eslint.config.{ext}" for ext in ("js", "mjs", "cjs", "ts", "mts", "cts")) + (
    ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yaml", ".eslintrc.yml",
    "biome.json", "biome.jsonc", ".oxlintrc.json")
PYTHON_LINT = ("ruff.toml", ".ruff.toml", ".flake8", ".pylintrc", "pylintrc", "mypy.ini", ".mypy.ini")
PYTHON_LINT_TOOLS = ("ruff", "flake8", "pylint", "mypy")
PYTHON_LINT_SECTIONS = re.compile(r"^\[(flake8|mypy|pylint[^\]]*)\]", re.MULTILINE)
DOTNET_EDITORCONFIG = re.compile(r"dotnet_diagnostic\.|dotnet_analyzer_diagnostic\.|^\s*\[\*\.(cs|\{[^\]]*\bcs\b)", re.MULTILINE)
MSBUILD_LINT = re.compile(r"<(TreatWarningsAsErrors|AnalysisLevel|AnalysisMode|EnforceCodeStyleInBuild|CodeAnalysisRuleSet)>")
UNSUPPORTED_MANIFESTS = {"go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "Gemfile", "composer.json",
                         "mix.exs", "Package.swift", "deno.json", "deno.jsonc", "pubspec.yaml", "CMakeLists.txt"}
UNSUPPORTED_SUFFIXES = (".fsproj", ".vbproj")
VENDORED = {"node_modules", ".venv", "venv", ".tox", "site-packages", "obj"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "fixture", "fixtures", "testdata"}
SOURCE_SUFFIXES = {".cs", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".py", ".sh", ".go", ".rs", ".java", ".kt", ".rb"}
CI_FILES = (".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile", ".circleci/config.yml", "bitbucket-pipelines.yml")
SECRET_SCANNER = re.compile(r"\b(gitleaks|trufflehog|detect-secrets|git-secrets|ggshield|secretlint|talisman)\b")
TIER_TOKEN = re.compile(r"(?<![\w-])(commit|integrate|nightly|verify-tree)(?![\w-])")
CASE_ARM = re.compile(r"^\s*\(?\s*([\"']?[\w-]+[\"']?(?:\s*\|\s*[\"']?[\w-]+[\"']?)*)\s*\)")
KEYED_TIER = re.compile(r"^\s*[\"']?(commit|integrate|nightly|verify-tree)[\"']?(\s*:|\s+=\s*[\[{\"'])")  # not shell `commit=$(...)`
TIER_LIST_LINE = re.compile(r"\b(tiers|TIERS|choices)\b")
VERIFY_NAME = re.compile(r"verify-[a-z0-9][a-z0-9-]*|bin/check\b|bin/verify\b")
RATCHET_WORD = re.compile(r"--check|ratchet|\bcheck\b|\bverify\b|\bcompare\b", re.IGNORECASE)
GITHUB_REMOTE = re.compile(r"github\.com[:/]+([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")


class NotARepo(Exception):
    pass


# `git rev-parse --local-env-vars`: what a hook exports; inherited, they would point git at another repo.
REPO_LOCAL_GIT_ENV = {"GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                      "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                      "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                      "GIT_COMMON_DIR", "GIT_INTERNAL_SUPER_PREFIX"}


def git_env() -> dict[str, str]:
    """Target the inspected repo, and keep optional locks off so no command refreshes its index."""
    env = {key: value for key, value in os.environ.items() if key not in REPO_LOCAL_GIT_ENV and not key.startswith("GIT_CONFIG_KEY_") and not key.startswith("GIT_CONFIG_VALUE_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def run_git(root: Path, *args: str) -> bytes | None:
    result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(root), *args], capture_output=True, env=git_env())
    return result.stdout if result.returncode == 0 else None


def code_lines(text: str) -> list[tuple[int, str]]:
    """(line number, line) for lines that are not comments: a `# TODO add gitleaks` proves nothing."""
    return [(n, line) for n, line in enumerate(text.splitlines(), start=1)
            if not line.lstrip().startswith(("#", "//", "<!--", "*"))]


def ancestors(directory: str) -> list[str]:
    parts = PurePosixPath(directory).parts if directory else ()
    return ["/".join(parts[:i]) for i in range(len(parts), -1, -1)]


def join(directory: str, name: str) -> str:
    return f"{directory}/{name}" if directory else name


def parent(rel: str) -> str:
    value = str(PurePosixPath(rel).parent)
    return "" if value == "." else value


def under(child: str, directory: str) -> bool:
    return not directory or child == directory or child.startswith(directory + "/")


def criterion(status: str, proof: str, **extra) -> dict:
    return {"status": status, "proof": proof, **extra}


class Repo:
    def __init__(self, path: Path):
        top = run_git(path, "rev-parse", "--show-toplevel") if path.is_dir() else None
        if top is None:
            raise NotARepo(f"{path} is not a git repository")
        self.root = Path(top.decode().strip())
        listing = run_git(self.root, "ls-files", "-z", "-co", "--exclude-standard")
        if listing is None:
            raise NotARepo(f"git ls-files failed in {self.root}")
        names = {os.fsdecode(raw) for raw in listing.split(b"\0") if raw}
        self.files = sorted(n for n in names if not VENDORED & set(PurePosixPath(n).parts[:-1]) and (self.root / n).is_file())
        self.fileset = set(self.files)
        self._cache: dict[str, str | None] = {}

    def git(self, *args: str) -> str | None:
        out = run_git(self.root, *args)
        return out.decode(errors="replace").strip() if out is not None else None

    def read(self, rel: str) -> str | None:
        if rel not in self._cache:
            path = self.root / rel
            text = None
            if path.is_file():
                with open(path, "rb") as handle:
                    text = handle.read(MAX_READ_BYTES).decode("utf-8", errors="replace")
            self._cache[rel] = text
        return self._cache[rel]

    def display(self, path: Path) -> str:
        return str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path)

    def find_up(self, directory: str, names: tuple[str, ...], pattern: re.Pattern | None = None) -> str | None:
        for folder in ancestors(directory):
            for name in names:
                rel = join(folder, name)
                if rel in self.fileset and (pattern is None or pattern.search(self.read(rel) or "")):
                    return rel
        return None


# ---- detection ----------------------------------------------------------------------------------

def node_lint(repo: Repo, directory: str) -> dict:
    found = repo.find_up(directory, NODE_LINT)
    if found:
        return criterion("PASS", found)
    try:
        manifest = json.loads(repo.read(join(directory, "package.json")) or "{}")
    except json.JSONDecodeError:
        manifest = {}
    if isinstance(manifest, dict) and "eslintConfig" in manifest:
        return criterion("PASS", f"{join(directory, 'package.json')} eslintConfig")
    return criterion("FAIL", f"no eslint, biome or oxlint config from {directory or '.'} up to the root")


def python_lint(repo: Repo, directory: str) -> dict:
    found = repo.find_up(directory, PYTHON_LINT)
    if found:
        return criterion("PASS", found)
    for folder in ancestors(directory):
        rel = join(folder, "pyproject.toml")
        if rel in repo.fileset:
            try:
                tools = tomllib.loads(repo.read(rel) or "").get("tool", {})
            except tomllib.TOMLDecodeError:
                tools = {}
            hit = next((t for t in PYTHON_LINT_TOOLS if t in tools), None)
            if hit:
                return criterion("PASS", f"{rel} [tool.{hit}]")
    found = repo.find_up(directory, ("setup.cfg", "tox.ini"), PYTHON_LINT_SECTIONS)
    if found:
        return criterion("PASS", found)
    return criterion("FAIL", f"no ruff, flake8, pylint or mypy config from {directory or '.'} up to the root")


def dotnet_lint(repo: Repo, directory: str, manifest: str) -> dict:
    for folder in ancestors(directory):
        for name, pattern in ((".editorconfig", DOTNET_EDITORCONFIG), (".globalconfig", None), ("Directory.Build.props", MSBUILD_LINT)):
            rel = join(folder, name)
            if rel in repo.fileset and (pattern is None or pattern.search(repo.read(rel) or "")):
                return criterion("PASS", rel)
    if manifest.endswith(".csproj") and MSBUILD_LINT.search(repo.read(manifest) or ""):
        return criterion("PASS", manifest)
    return criterion("FAIL", f"no .editorconfig with .NET rules, .globalconfig or Directory.Build.props with analyzer settings from {directory or '.'} up to the root")


def components(repo: Repo) -> list[dict]:
    found: list[dict] = []
    solutions = [f for f in repo.files if f.endswith((".sln", ".slnx"))]
    projects = [f for f in repo.files if f.endswith(".csproj") and not any(under(parent(f), parent(s)) for s in solutions)]
    dotnet = solutions + projects
    if not dotnet:
        dotnet = [f for f in repo.files if PurePosixPath(f).name == "global.json"]
    for manifest in dotnet:
        found.append({"path": parent(manifest) or ".", "stack": "dotnet", "manifest": manifest,
                      "lint": dotnet_lint(repo, parent(manifest), manifest)})
    for manifest in (f for f in repo.files if PurePosixPath(f).name == "package.json"):
        directory = parent(manifest)
        lock = repo.find_up(directory, LOCKFILES)
        found.append({"path": directory or ".", "stack": "node", "manifest": manifest,
                      "lockfile": criterion("PASS", lock) if lock else criterion("FAIL", f"no lockfile from {directory or '.'} up to the root"),
                      "lint": node_lint(repo, directory)})
    python_dirs: dict[str, str] = {}
    for f in repo.files:
        name = PurePosixPath(f).name
        if name == "pyproject.toml" or re.fullmatch(r"requirements[\w.-]*\.txt", name):
            current = python_dirs.get(parent(f))
            if current is None or (name == "pyproject.toml" and not current.endswith("pyproject.toml")):
                python_dirs[parent(f)] = f
    for directory, manifest in sorted(python_dirs.items()):
        found.append({"path": directory or ".", "stack": "python", "manifest": manifest, "lint": python_lint(repo, directory)})
    return sorted(found, key=lambda c: (c["path"], c["stack"], c["manifest"]))


def stacks(repo: Repo) -> tuple[dict[str, list[str]], list[str]]:
    evidence: dict[str, list[str]] = {}
    unsupported: list[str] = []
    for f in repo.files:
        name = PurePosixPath(f).name
        if name.endswith((".sln", ".slnx", ".csproj")) or name == "global.json":
            evidence.setdefault("dotnet", []).append(f)
        elif name == "package.json" or name in LOCKFILES:
            evidence.setdefault("node", []).append(f)
        elif name == "pyproject.toml" or re.fullmatch(r"requirements[\w.-]*\.txt", name):
            evidence.setdefault("python", []).append(f)
        elif name in UNSUPPORTED_MANIFESTS or name.endswith(UNSUPPORTED_SUFFIXES):
            unsupported.append(f)
    if "node" in evidence and not any(PurePosixPath(f).name == "package.json" for f in evidence["node"]):
        unsupported += evidence.pop("node")  # a lockfile alone is not a Node project we can reason about
    return dict(sorted(evidence.items())), unsupported


def hook_state(repo: Repo) -> dict:
    configured = repo.git("config", "--get", "core.hooksPath")
    if configured:
        hooks_dir = Path(os.path.expanduser(configured))
        source = f"core.hooksPath={configured}"
    else:
        hooks_dir = Path(repo.git("rev-parse", "--git-path", "hooks") or ".git/hooks")
        source = "core.hooksPath unset, default hooks dir"
    hooks_dir = hooks_dir if hooks_dir.is_absolute() else repo.root / hooks_dir
    pre_commit = hooks_dir / "pre-commit"
    return {
        "core_hooks_path": configured,
        "source": source,
        "pre_commit": repo.display(pre_commit),
        "exists": pre_commit.is_file(),
        "active": pre_commit.is_file() and os.access(pre_commit, os.X_OK),
        "managers": [m for m in (".githooks", ".husky", ".pre-commit-config.yaml") if (repo.root / m).exists()],
        "_path": pre_commit,
    }


def read_absolute(path: Path) -> str:
    with open(path, "rb") as handle:
        return handle.read(MAX_READ_BYTES).decode("utf-8", errors="replace")


def hook_scope(repo: Repo, hooks: dict) -> list[tuple[str, str]]:
    """The active hook, its manager's config, and the repo files it calls (one level)."""
    if not hooks["active"]:
        return []
    text = read_absolute(hooks["_path"])
    scope = [(hooks["pre_commit"], text)]
    extra: list[str] = []
    if "pre-commit" in text and ".pre-commit-config.yaml" in repo.fileset and re.search(r"pre-commit(\.com|\s+hook-impl|\s+run)|INSTALL_PYTHON", text):
        extra.append(".pre-commit-config.yaml")
    if (hooks["core_hooks_path"] or "").rstrip("/").endswith(".husky/_") and ".husky/pre-commit" in repo.fileset:
        extra.append(".husky/pre-commit")
    for _, line in code_lines(text):
        for token in re.findall(r"[A-Za-z0-9_.@/-]+", line):
            rel = token.lstrip("/").removeprefix("./")
            if rel in repo.fileset and rel != hooks["pre_commit"]:
                extra.append(rel)
    for rel in dict.fromkeys(extra):
        scope.append((rel, repo.read(rel) or ""))
    return scope


def gate_scope(repo: Repo, hooks: dict) -> list[tuple[str, str]]:
    """Every place a check can be enforced: the hook scope, the check contract and CI."""
    scope = hook_scope(repo, hooks)
    seen = {label for label, _ in scope}
    names = ["bin/check", ".kitchen/checks.toml", ".pre-commit-config.yaml", ".husky/pre-commit"]
    names += [f for f in repo.files if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]
    names += [f for f in CI_FILES if f in repo.fileset]
    for rel in names:
        if rel in repo.fileset and rel not in seen:
            scope.append((rel, repo.read(rel) or ""))
    return scope


def first_hit(scope: list[tuple[str, str]], test) -> str | None:
    """`file:line` of the first non-comment line where test(line) is truthy."""
    for label, text in scope:
        for number, line in code_lines(text):
            if test(line):
                return f"{label}:{number}"
    return None


def ci_files(repo: Repo) -> list[str]:
    return [f for f in repo.files if (f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))) or f in CI_FILES]


def project_skills(repo: Repo) -> list[str]:
    return sorted({PurePosixPath(f).parts[2] for f in repo.files
                   if f.startswith(".agents/skills/") and len(PurePosixPath(f).parts) == 4 and f.endswith("/SKILL.md")})


# ---- must-haves ---------------------------------------------------------------------------------

def declared_tiers(text: str) -> dict[str, int]:
    """Tiers a script declares in a tier table: case arms, keyed entries or a tiers/choices list."""
    found: dict[str, int] = {}
    lines = code_lines(text)
    for index, (number, line) in enumerate(lines):
        names: list[str] = []
        arm = CASE_ARM.match(line)
        if arm:
            names += [n.strip().strip("\"'") for n in arm.group(1).split("|")]
        keyed = KEYED_TIER.match(line)
        if keyed:
            names.append(keyed.group(1))
        if TIER_LIST_LINE.search(line):
            block = line
            for _, following in lines[index + 1:index + 20]:
                if sum(block.count(o) - block.count(c) for o, c in ("()", "[]", "{}")) <= 0:
                    break
                block += "\n" + following
            names += TIER_TOKEN.findall(block)
        for name in names:
            if name in TIERS:
                found.setdefault(name, number)
    return found


def toml_tiers(data: dict) -> set[str]:
    found = {k for k in data if k in TIERS}
    if isinstance(data.get("tiers"), dict):
        found |= {k for k in data["tiers"] if k in TIERS}
    for value in data.values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    tiers = item.get("tiers", item.get("tier", []))
                    found |= {t for t in ([tiers] if isinstance(tiers, str) else tiers) if t in TIERS}
    return found


def check_contract(repo: Repo) -> dict:
    reasons: list[str] = []
    script = repo.root / "bin" / "check"
    if script.is_file():
        tiers = declared_tiers(read_absolute(script))
        missing = [t for t in TIERS if t not in tiers]
        if not os.access(script, os.X_OK):
            reasons.append("bin/check is not executable")
        elif missing:
            reasons.append(f"bin/check declares no tier table entry for {', '.join(missing)} (it is read, never run)")
        else:
            lines = ", ".join(f"{t}:{tiers[t]}" for t in TIERS)
            return criterion("PASS", f"bin/check (executable) declares {', '.join(TIERS)} at lines {lines}")
    toml = repo.root / ".kitchen" / "checks.toml"
    if toml.is_file():
        try:
            tiers = toml_tiers(tomllib.loads(read_absolute(toml)))
        except tomllib.TOMLDecodeError as error:
            reasons.append(f".kitchen/checks.toml does not parse: {error}")
        else:
            missing = [t for t in TIERS if t not in tiers]
            if not missing:
                return criterion("PASS", f".kitchen/checks.toml declares {', '.join(TIERS)}")
            reasons.append(f".kitchen/checks.toml declares no {', '.join(missing)}")
    if not reasons:
        reasons.append("no bin/check and no .kitchen/checks.toml")
    return criterion("FAIL", "; ".join(reasons),
                     next="Add an executable bin/check whose tier table declares commit, integrate, nightly and verify-tree "
                          "(and prints them with --list), or declare those tiers in .kitchen/checks.toml.")


def pre_commit_hook(repo: Repo, hooks: dict) -> dict:
    if hooks["active"]:
        return criterion("PASS", f"{hooks['pre_commit']} is executable ({hooks['source']})")
    candidates = [f for f in repo.files if PurePosixPath(f).name == "pre-commit"]
    if hooks["exists"]:
        proof = f"{hooks['pre_commit']} exists but is not executable ({hooks['source']})"
        step = f"Make it executable: chmod +x {hooks['pre_commit']}"
    else:
        proof = f"no {hooks['pre_commit']} ({hooks['source']})"
        if candidates:
            step = f"Activate the tracked hook in this clone: git config core.hooksPath {parent(candidates[0]) or '.'}"
        elif ".pre-commit-config.yaml" in repo.fileset:
            step = "Activate the pre-commit framework in this clone: pre-commit install"
        else:
            step = "Add a tracked pre-commit hook that runs `bin/check commit`, then point core.hooksPath at its folder."
    if candidates and not hooks["exists"]:
        proof += f"; tracked but inactive: {', '.join(candidates)}"
    return criterion("FAIL", proof, next=step)


def agents_md(repo: Repo, verify_skills: list[str]) -> dict:
    if "AGENTS.md" not in repo.fileset:
        also = " (CLAUDE.md exists; Codex reads AGENTS.md)" if "CLAUDE.md" in repo.fileset else ""
        return criterion("FAIL", f"no AGENTS.md{also}",
                         next="Write a short AGENTS.md (under 200 lines): verified commands, the verify command, one-way doors. No generated prose.")
    text = repo.read("AGENTS.md") or ""
    count = len(text.splitlines())
    if count >= MAX_AGENTS_LINES:
        return criterion("FAIL", f"AGENTS.md has {count} lines (must be under {MAX_AGENTS_LINES})",
                         next=f"Trim AGENTS.md from {count} to under {MAX_AGENTS_LINES} lines; move detail into skills or referenced docs.")
    wanted = re.compile("|".join([re.escape(s) for s in verify_skills] + [r"bin/check\b"])) if verify_skills else VERIFY_NAME
    for number, line in enumerate(text.splitlines(), start=1):
        match = wanted.search(line)
        if match:
            return criterion("PASS", f"AGENTS.md has {count} lines; line {number} names {match.group(0)}")
    names = ", ".join(verify_skills) if verify_skills else "a verify-<repo> skill, bin/check or bin/verify"
    return criterion("FAIL", f"AGENTS.md has {count} lines but names no verify command ({names})",
                     next="Name the verify command in AGENTS.md (the verify-<repo> skill or bin/check).")


def test_files(repo: Repo) -> list[str]:
    def is_test(rel: str) -> bool:
        path = PurePosixPath(rel)
        return path.suffix in SOURCE_SUFFIXES and (
            bool(TEST_DIRS & {p.lower() for p in path.parts[:-1]}) or "test" in path.name.lower())
    return [f for f in repo.files if is_test(f) and not f.startswith(".agents/skills/")]


def verify_skill(repo: Repo, verify_skills: list[str], gates: list[tuple[str, str]]) -> dict:
    if not verify_skills:
        return criterion("FAIL", "no .agents/skills/verify-*/SKILL.md",
                         next="Create .agents/skills/verify-<repo>/ from the kitchen's templates/verify, with a features/ map and a guard.")
    findings = []
    for name in verify_skills:
        features = [f for f in repo.files if f.startswith(f".agents/skills/{name}/features/") and f.endswith(".md")]
        guards = []
        gate = first_hit(gates, lambda line, n=name: n in line and re.search(r"coverage|feature", line, re.IGNORECASE))
        if gate:
            guards.append(gate)
        named = lambda rel: not re.search(r"feature|map|coverage|guard", PurePosixPath(rel).name, re.IGNORECASE)
        for rel in sorted(test_files(repo), key=named):  # a FeatureMapGuard test is better proof than any test naming the skill
            text = repo.read(rel) or ""
            if name in text and re.search(r"coverage|feature", text, re.IGNORECASE):
                line = next(n for n, l in enumerate(text.splitlines(), start=1) if name in l)
                guards.append(f"{rel}:{line}")
                break
        if features and guards:
            return criterion("PASS", f"{name}: {len(features)} feature files; guard {', '.join(guards)}")
        findings.append(f"{name}: {len(features)} feature files, {'guard ' + guards[0] if guards else 'no guard in a gate or test'}")
    step = ("Add a guard (a test, or a hook or bin/check step) that fails when an entry point is missing from features/."
            if any("feature files, no guard" in f for f in findings) else "Add the feature map under features/ and a guard that enforces it.")
    return criterion("FAIL", "; ".join(findings), next=step)


def decisions(repo: Repo) -> dict:
    if "decisions.md" in repo.fileset:
        return criterion("PASS", "decisions.md")
    return criterion("FAIL", "no decisions.md at the repo root",
                     next="Create decisions.md (date, decision, scope, when to revisit); owed decisions as `- [ ]`.")


def secret_scan(repo: Repo, hooks: dict) -> dict:
    scope = hook_scope(repo, hooks)
    found: list[str] = []
    def scanner(line: str) -> bool:
        match = SECRET_SCANNER.search(line)
        if match:
            found.append(match.group(0))
        return bool(match)
    step = "Add a secret scan to the pre-commit hook, e.g. `gitleaks git --pre-commit --staged`."
    if scope:
        hit = first_hit(scope, scanner)
        if hit:
            return criterion("PASS", f"{found[0]} at {hit}")
        return criterion("FAIL", f"no secret scanner in the active hook or the files it references ({', '.join(l for l, _ in scope)})", next=step)
    inactive = [(f, repo.read(f) or "") for f in repo.files if PurePosixPath(f).name in ("pre-commit", ".pre-commit-config.yaml")]
    hit = first_hit(inactive, scanner)
    if hit:
        return criterion("FAIL", f"a scanner is referenced at {hit}, but no pre-commit hook is active", next="Activate the pre-commit hook (see above).")
    return criterion("FAIL", "no active pre-commit hook, so no secret scan runs", next=step)


def baseline_candidates(repo: Repo) -> list[str]:
    def is_baseline(rel: str) -> bool:
        path = PurePosixPath(rel)
        if TEST_DIRS & {p.lower() for p in path.parts[:-1]}:
            return False
        if path.name in ("eslint-suppressions.json", ".betterer.results"):
            return True
        return bool(re.search(r"baseline|ratchet", path.name, re.IGNORECASE)) and path.suffix in (".json", ".toml", ".yml", ".yaml", ".txt", ".csv", ".xml")
    return [f for f in repo.files if is_baseline(f)]


def baseline_ratchet(repo: Repo, gates: list[tuple[str, str]]) -> dict:
    candidates = baseline_candidates(repo)
    if not candidates:
        return criterion("FAIL", "no baseline file (*baseline*/*ratchet* data file, eslint-suppressions.json, .betterer.results)",
                         next="Record a baseline of today's violations and check it in a gate so the count can only go down.")
    for rel in candidates:
        path = PurePosixPath(rel)
        if path.name == "eslint-suppressions.json":
            lint_script = ""
            try:
                lint_script = str(json.loads(repo.read(join(parent(rel), "package.json")) or "{}").get("scripts", {}).get("lint", ""))
            except (json.JSONDecodeError, AttributeError):
                pass
            test = lambda line: "eslint" in line or ("eslint" in lint_script and re.search(r"\blint\b", line))
        else:
            stem = path.stem
            test = lambda line, s=stem: s in line and RATCHET_WORD.search(line)
        hit = first_hit(gates, test)
        if hit:
            return criterion("PASS", f"{rel} is checked at {hit}")
    gate_names = ", ".join(l for l, _ in gates) or "no gate files"
    return criterion("FAIL", f"baseline {', '.join(candidates)} is not checked by any gate ({gate_names})",
                     next=f"Make a gate (hook, bin/check or CI) check {candidates[0]} so new violations fail (a ratchet, not a report).")


def skills_linked(repo: Repo, skills: list[str]) -> dict:
    if not skills:
        return criterion("FAIL", "no project skills under .agents/skills to link",
                         next="Keep project skills in .agents/skills/ (shared by Codex and Claude) and link them into .claude/skills/.")
    linked, missing = [], []
    for name in skills:
        link = repo.root / ".claude" / "skills" / name
        (linked if link.exists() and link.resolve() == (repo.root / ".agents" / "skills" / name).resolve() else missing).append(name)
    if not missing:
        return criterion("PASS", f".claude/skills links {', '.join(linked)}")
    commands = "; ".join(f"ln -s ../../.agents/skills/{n} .claude/skills/{n}" for n in missing)
    return criterion("FAIL", f".claude/skills lacks {', '.join(missing)}" + (f" (linked: {', '.join(linked)})" if linked else ""),
                     next=f"Link them in this clone: mkdir -p .claude/skills; {commands}")


def gh_get(endpoint: str) -> tuple[object | None, str | None]:
    gh = os.environ.get("KITCHEN_GH") or "gh"
    env = {**os.environ, "GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1", "NO_COLOR": "1"}
    try:
        result = subprocess.run([gh, "api", "-H", "Accept: application/vnd.github+json", endpoint],
                                capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS, env=env)
    except FileNotFoundError:
        return None, "gh is not installed"
    except subprocess.TimeoutExpired:
        return None, f"gh api {endpoint} timed out after {GH_TIMEOUT_SECONDS}s"
    if result.returncode != 0:
        lines = [l for l in result.stderr.strip().splitlines() if l.strip()]
        return None, f"gh api {endpoint}: {lines[-1] if lines else 'exit ' + str(result.returncode)}"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, f"gh api {endpoint} did not return JSON"


def branch_protection(repo: Repo, branch: str | None) -> dict:
    door = ("[one-way door: printed, never executed] Owner decision: require a status check on the shared branch with a "
            "ruleset (Settings > Rules > Rulesets, rule 'Require status checks to pass').")
    url = repo.git("config", "--get", "remote.origin.url") or ""
    match = GITHUB_REMOTE.search(url)
    if not match:
        return criterion("unknown", "origin is not a GitHub remote, so protection cannot be read",
                         next="Push to GitHub (or check the host's branch rules by hand); then rerun.")
    slug = f"{match.group(1)}/{match.group(2)}"
    if not branch:
        meta, error = gh_get(f"repos/{slug}")
        if error:
            return criterion("unknown", error, next=f"Install and authenticate gh, then rerun. If unprotected: {door}", one_way_door=True)
        branch = str(meta.get("default_branch")) if isinstance(meta, dict) else None
        if not branch:
            return criterion("unknown", f"gh api repos/{slug} returned no default_branch", next=door, one_way_door=True)
    classic, classic_error = gh_get(f"repos/{slug}/branches/{branch}")
    rules, rules_error = gh_get(f"repos/{slug}/rules/branches/{branch}")
    if isinstance(rules, list):
        for rule in rules:
            if isinstance(rule, dict) and rule.get("type") == "required_status_checks":
                checks = rule.get("parameters", {}).get("required_status_checks", [])
                names = ", ".join(sorted(str(c.get("context")) for c in checks if isinstance(c, dict))) or "no contexts"
                return criterion("PASS", f"gh api repos/{slug}/rules/branches/{branch}: required_status_checks ({names})")
    if isinstance(classic, dict):
        required = (classic.get("protection") or {}).get("required_status_checks") or {}
        contexts = sorted(set(required.get("contexts") or []) | {str(c.get("context")) for c in required.get("checks") or [] if isinstance(c, dict)})
        if required.get("enforcement_level", "off") != "off" and contexts:
            return criterion("PASS", f"gh api repos/{slug}/branches/{branch}: required status {', '.join(contexts)}")
    errors = [e for e in (classic_error, rules_error) if e]
    if errors:
        return criterion("unknown", "; ".join(errors), next=f"Fix gh access and rerun. If unprotected: {door}", one_way_door=True)
    types = sorted({str(r.get("type")) for r in rules if isinstance(r, dict)}) if isinstance(rules, list) else []
    return criterion("FAIL", f"{branch}: no required status in gh api repos/{slug}/branches/{branch} (classic) "
                             f"or repos/{slug}/rules/branches/{branch} (rules: {', '.join(types) or 'none'})",
                     next=door.replace("the shared branch", branch), one_way_door=True)


# ---- report -------------------------------------------------------------------------------------

def check(path: Path, branch: str | None = None) -> dict:
    repo = Repo(path.resolve())
    hooks = hook_state(repo)
    gates = gate_scope(repo, hooks)
    skills = project_skills(repo)
    verify_skills = [s for s in skills if s.startswith("verify-")]
    evidence, unsupported = stacks(repo)
    results = {
        "check-contract": check_contract(repo),
        "pre-commit-hook": pre_commit_hook(repo, hooks),
        "agents-md": agents_md(repo, verify_skills),
        "verify-skill": verify_skill(repo, verify_skills, gates),
        "decisions": decisions(repo),
        "secret-scan": secret_scan(repo, hooks),
        "baseline-ratchet": baseline_ratchet(repo, gates),
        "skills-linked": skills_linked(repo, skills),
        "branch-protection": branch_protection(repo, branch),
    }
    must_haves = [{"id": key, "label": label, **results[key]} for key, label in MUST_HAVES]
    next_steps = [{"n": i, "id": m["id"], "step": m.get("next", ""), "one_way_door": bool(m.get("one_way_door"))}
                  for i, m in enumerate((m for m in must_haves if m["status"] != "PASS"), start=1)]
    for m in must_haves:
        m.pop("next", None)
        m.pop("one_way_door", None)
    missing = sum(1 for m in must_haves if m["status"] != "PASS")
    return {
        "path": str(repo.root),
        "head": repo.git("rev-parse", "--short", "HEAD"),
        "read_only": True,
        "stacks": evidence if evidence else {},
        "stack_status": "detected" if evidence else "unsupported",
        "unsupported": unsupported,
        "components": components(repo),
        "hooks": {k: v for k, v in hooks.items() if not k.startswith("_")},
        "agent_files": {
            "AGENTS.md": len((repo.read("AGENTS.md") or "").splitlines()) if "AGENTS.md" in repo.fileset else None,
            "CLAUDE.md": len((repo.read("CLAUDE.md") or "").splitlines()) if "CLAUDE.md" in repo.fileset else None,
            "project_skills": skills,
            "verify_skills": verify_skills,
            "decisions.md": "decisions.md" in repo.fileset,
        },
        "ci": ci_files(repo),
        "must_haves": must_haves,
        "missing": missing,
        "failed": sum(1 for m in must_haves if m["status"] == "FAIL"),
        "unknown": sum(1 for m in must_haves if m["status"] == "unknown"),
        "next_steps": next_steps,
    }


def summarize(files: list[str], limit: int = 3) -> str:
    shown = ", ".join(files[:limit])
    return shown + (f" +{len(files) - limit} more" if len(files) > limit else "")


def render(report: dict) -> str:
    out = [f"kitchen adopt --check {report['path']}  (read-only: ran no repository code)", f"HEAD {report['head'] or 'none'}", "", "Stacks"]
    for stack, files in report["stacks"].items():
        out.append(f"  {stack:<12} {summarize(files)}")
    if report["stack_status"] == "unsupported":
        out.append("  unsupported  no .NET, Node or Python manifest")
    if report["unsupported"]:
        out.append(f"  unsupported  {summarize(report['unsupported'])}")
    out.append(f"Components ({len(report['components'])})")
    for c in report["components"]:
        parts = [f"  {c['path']:<28} {c['stack']:<7} {c['manifest']}"]
        if "lockfile" in c:
            parts.append(f"lockfile {c['lockfile']['status']} {c['lockfile']['proof']}")
        parts.append(f"lint {c['lint']['status']} {c['lint']['proof']}")
        out.append("  ·  ".join(parts))
    h = report["hooks"]
    out += ["Hooks", f"  {h['source']}; pre-commit {h['pre_commit']}: {'active' if h['active'] else 'present, not executable' if h['exists'] else 'missing'}",
            f"  managers: {', '.join(h['managers']) or 'none'}"]
    a = report["agent_files"]
    lines = lambda value: "missing" if value is None else f"{value} line{'' if value == 1 else 's'}"
    out += ["Agent files", f"  AGENTS.md {lines(a['AGENTS.md'])}; CLAUDE.md {lines(a['CLAUDE.md'])}; decisions.md {'yes' if a['decisions.md'] else 'missing'}",
            f"  project skills: {', '.join(a['project_skills']) or 'none'}; verify: {', '.join(a['verify_skills']) or 'none'}"]
    out += ["CI", f"  {summarize(report['ci'], 5) if report['ci'] else 'none'}", "", "Must-haves"]
    for m in report["must_haves"]:
        out.append(f"  {m['status']:<8} {m['label']:<34} {m['proof']}")
    total = len(report["must_haves"])
    out += ["", f"Missing {report['missing']} of {total} must-haves ({report['failed']} FAIL, {report['unknown']} unknown)"]
    if report["next_steps"]:
        out.append("Next steps (printed only; nothing was changed)")
        out += [f"  {s['n']}. {s['step']}" for s in report["next_steps"]]
    return "\n".join(out)
