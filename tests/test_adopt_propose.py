"""`kitchen adopt --propose` and `--prove` on fixture repos in temp dirs: what is written, what is never touched, and
whether the proof can tell a gate that works from one that cannot fail.

Expected files, statuses and commands are written by hand from each fixture's design, not recomputed the way
propose.py does. Regenerate the golden report with KITCHEN_UPDATE_GOLDEN=1, then review the diff by hand.
"""
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from tests.test_adopt import GOLDEN, KITCHEN, RAN, AdoptFixture

BRANCH = "kitchen/adopt"


def node_supports_typescript():
    """Node runs .ts tests without a loader from 22.18 (type stripping on by default)."""
    if not (shutil.which("node") and shutil.which("npm")):
        return False
    out = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip().lstrip("v")
    major, minor = (int(part) for part in out.split(".")[:2])
    return (major, minor) >= (22, 18)


def dotnet_major():
    if not shutil.which("dotnet"):
        return None
    out = subprocess.run(["dotnet", "--version"], capture_output=True, text=True)
    return int(out.stdout.split(".")[0]) if out.returncode == 0 and out.stdout[:1].isdigit() else None


PYTHON_FILES = {
    "pyproject.toml": '[project]\nname = "calc"\n',
    "calc.py": "def add(a, b):\n    return a + b\n",
    "tests/test_calc.py": textwrap.dedent("""\
        import unittest

        import calc


        class Add(unittest.TestCase):
            def test_add(self):
                self.assertEqual(calc.add(2, 3), 5)
        """),
    "AGENTS.md": "# Calc\n\nRun the tests.\n",
    "README.md": "# Calc\n",
}

NODE_FILES = {
    "package.json": '{"name": "calc", "private": true, "type": "module", "scripts": {"test": "node --test"}}\n',
    "package-lock.json": '{"name": "calc", "lockfileVersion": 3, "requires": true, "packages": {"": {"name": "calc"}}}\n',
    "tsconfig.json": '{"compilerOptions": {"strict": true, "module": "nodenext", "allowImportingTsExtensions": true, "noEmit": true}}\n',
    "src/calc.ts": "export function add(a: number, b: number): number {\n  return a + b;\n}\n",
    "test/calc.test.ts": textwrap.dedent("""\
        import { test } from "node:test";
        import assert from "node:assert/strict";
        import { add } from "../src/calc.ts";

        test("add", () => {
          assert.equal(add(2, 3), 5);
        });
        """),
    "decisions.md": "# Decisions\n\n- [x] 2026-01-02 ship as an npm package\n",
}


def dotnet_files(major=10):
    return {
        "Shop.csproj": f'<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <TargetFramework>net{major}.0</TargetFramework>\n  </PropertyGroup>\n</Project>\n',
        "Calc.cs": "namespace Shop;\n\npublic static class Calc\n{\n    public static int Add(int a, int b) => a + b;\n}\n",
        ".gitignore": "bin/\nobj/\n",
    }


# Declares every tier, so --check calls it a contract, and can never fail.
CANNOT_FAIL = "#!/bin/sh\ncase \"$1\" in\n  --list) printf '%s\\n' commit integrate nightly verify-tree ;;\n  commit|integrate|nightly|verify-tree) exit 0 ;;\nesac\n"


class ProposeFixture(AdoptFixture):
    def setUp(self):
        super().setUp()
        self.tmpdir = self.root / "tmp"
        self.tmpdir.mkdir()

    def env(self, gh=None):
        env = super().env(gh)
        env.update({"TMPDIR": str(self.tmpdir), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                    "GIT_COMMITTER_EMAIL": "t@t", "GIT_AUTHOR_DATE": "2026-01-02T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-02T00:00:00Z",
                    "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
                    "MSBUILDDISABLENODEREUSE": "1", "DOTNET_CLI_USE_MSBUILD_SERVER": "0", "npm_config_update_notifier": "false"})
        return env

    def propose(self, repo, *extra, gh=None):
        return subprocess.run([sys.executable, str(KITCHEN), "adopt", "--propose", str(repo), *extra],
                              capture_output=True, text=True, env=self.env(gh))

    def propose_json(self, repo, *extra, gh=None, code=0):
        result = self.propose(repo, "--json", *extra, gh=gh)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
                              env={**self.env(), "GIT_OPTIONAL_LOCKS": "0"}).stdout

    def tree(self, repo, ref):
        """{path: (mode, blob sha)} for every file at ref."""
        out = self.git(repo, "ls-tree", "-r", "-z", ref)
        entries = {}
        for record in filter(None, out.split("\0")):
            meta, path = record.split("\t", 1)
            mode, _, sha = meta.split()
            entries[path] = (mode, sha)
        return entries

    def show(self, repo, ref, path):
        return self.git(repo, "show", f"{ref}:{path}")

    def branch_sha(self, repo):
        out = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"refs/heads/{BRANCH}"],
                             capture_output=True, text=True, env=self.env())
        return out.stdout.strip() or None

    def added(self, repo):
        main, proposal = self.tree(repo, "main"), self.tree(repo, BRANCH)
        self.assertEqual({p: proposal[p] for p in main}, main, "a file that existed on main changed on the proposal branch")
        return sorted(set(proposal) - set(main))

    def states(self, result):
        return {f["path"]: f["state"] for f in result["files"]}


class Proposal(ProposeFixture):
    def test_python_writes_only_the_missing_pieces(self):
        repo = self.make_repo("calc", PYTHON_FILES)

        result = self.propose_json(repo)

        self.assertEqual(self.added(repo), [".agents/skills/verify-calc/SKILL.md", ".agents/skills/verify-calc/features/README.md",
                                            ".githooks/pre-commit", ".kitchen/adopt.json", ".kitchen/baseline.json",
                                            "ADOPT.md", "bin/check", "decisions.md"])
        tree = self.tree(repo, BRANCH)
        self.assertEqual((tree["bin/check"][0], tree[".githooks/pre-commit"][0]), ("100755", "100755"))
        check = self.show(repo, BRANCH, "bin/check")
        self.assertRegex(check, r"# unverified: [^\n]*tests/\n\s*python3 -m unittest discover -s tests\n")
        self.assertIn("commit) tier_commit ;;", check)
        self.assertIn("--list)", check)
        hook = self.show(repo, BRANCH, ".githooks/pre-commit")
        self.assertIn("gitleaks git --pre-commit --staged", hook)
        self.assertIn("brew install gitleaks", hook)
        self.assertIn("exec bin/check commit", hook)
        decisions = self.show(repo, BRANCH, "decisions.md")
        self.assertEqual(len(re.findall(r"^- \[ \] ", decisions, re.MULTILINE)), 4, decisions)
        self.assertIn("verify-calc", self.show(repo, BRANCH, ".agents/skills/verify-calc/SKILL.md"))
        baseline = json.loads(self.show(repo, BRANCH, ".kitchen/baseline.json"))
        self.assertEqual(baseline["mode"], "measure-only")
        self.assertEqual(baseline["must_haves"], {"check-contract": "FAIL", "pre-commit-hook": "FAIL", "agents-md": "FAIL",
                                                  "verify-skill": "FAIL", "decisions": "FAIL", "secret-scan": "FAIL",
                                                  "baseline-ratchet": "FAIL", "skills-linked": "FAIL", "branch-protection": "unknown"})
        manifest = json.loads(self.show(repo, BRANCH, ".kitchen/adopt.json"))
        for path in ("bin/check", ".githooks/pre-commit", "decisions.md", ".kitchen/baseline.json",
                     ".agents/skills/verify-calc/SKILL.md", ".agents/skills/verify-calc/features/README.md"):
            blob = subprocess.run(["git", "-C", str(repo), "show", f"{BRANCH}:{path}"], capture_output=True, check=True).stdout
            self.assertEqual(manifest["files"][path]["sha256"], hashlib.sha256(blob).hexdigest(), path)
        self.assertEqual(set(self.states(result).values()), {"written"})
        agents = next(p for p in result["proposals"] if p["id"] == "agents-md")
        self.assertIn("names no verify command", agents["text"])
        self.assertEqual(self.show(repo, BRANCH, "AGENTS.md"), PYTHON_FILES["AGENTS.md"])
        self.assertEqual(result["readiness"]["checks_run_green"]["state"], "not run")
        self.assertEqual(result["readiness"]["unattended_ready"]["state"], "not assessed")
        self.assertFalse(result["ran_repository_code"])

    def test_golden_report(self):
        repo = self.make_repo("calc", PYTHON_FILES)

        result = self.propose(repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        text = result.stdout.replace(str(repo), "<repo>")
        golden = GOLDEN / "propose-python.txt"
        if os.environ.get("KITCHEN_UPDATE_GOLDEN"):
            golden.write_text(text)
        self.assertEqual(text, golden.read_text(), f"golden {golden.name} differs; review, then rerun with KITCHEN_UPDATE_GOLDEN=1")
        adopt_md = self.show(repo, BRANCH, "ADOPT.md")
        self.assertNotIn(str(self.root), adopt_md, "ADOPT.md is committed into the target repo: no absolute paths")
        for section in ("Files", "Unverified", "Readiness", "One-way doors"):
            self.assertIn(section, adopt_md)

    def test_node_reads_the_npm_test_script(self):
        repo = self.make_repo("web", NODE_FILES)

        self.propose_json(repo)

        self.assertNotIn("decisions.md", self.added(repo), "decisions.md existed; it must not be rewritten")
        check = self.show(repo, BRANCH, "bin/check")
        self.assertRegex(check, r"# unverified: from package\.json scripts\.test\n\s*npm test\n")

    def test_dotnet_builds_the_project_and_bin_check_is_tracked_despite_gitignore(self):
        repo = self.make_repo("shop", dotnet_files())

        result = self.propose_json(repo)

        self.assertIn("bin/check", self.added(repo))
        check = self.show(repo, BRANCH, "bin/check")
        self.assertRegex(check, r"# unverified: from Shop\.csproj\n\s*dotnet build Shop\.csproj\n")
        self.assertIn("no test project", check)
        self.assertTrue(any("bin/check" in note and ".gitignore" in note for note in result["notes"]), result["notes"])

    def test_unknown_stack_gets_no_guessed_commands_and_no_agents_prose(self):
        repo = self.make_repo("tool", {"go.mod": "module example.com/tool\n", "main.go": "package main\n"})

        result = self.propose_json(repo)

        added = self.added(repo)
        self.assertNotIn("bin/check", added)
        self.assertNotIn("AGENTS.md", added)
        self.assertIn(".githooks/pre-commit", added)
        self.assertIn("decisions.md", added)
        proposals = {p["id"]: p["text"] for p in result["proposals"]}
        self.assertIn("unsupported", proposals["check-contract"])
        self.assertIn("CLAUDE_CODE_NEW_INIT=1", proposals["agents-md"])
        self.assertIn("/init", proposals["agents-md"])

    def test_complete_repo_gets_no_branch(self):
        repo = self.make_complete()
        before = self.tree(repo, "main")

        result = self.propose_json(repo)

        self.assertIsNone(self.branch_sha(repo))
        self.assertEqual(result["files"], [])
        self.assertEqual(result["readiness"]["files_proposed"]["state"], "no")
        self.assertEqual(self.tree(repo, "main"), before)
        self.assertFalse(self.marker.exists(), "--propose without --prove ran repository code")

    def test_existing_incomplete_pieces_are_listed_not_edited(self):
        files = dict(PYTHON_FILES)
        files.update({
            "bin/check": "#!/bin/sh\nexec python3 -m unittest discover -s tests\n",
            ".githooks/pre-commit": "#!/bin/sh\nexec bin/check\n",
            ".agents/skills/verify-calc/SKILL.md": "---\nname: verify-calc\ndescription: Prove calc.\n---\n",
            "quality/baseline.json": "{}\n",
        })
        repo = self.make_repo("calc", files, executable=("bin/check", ".githooks/pre-commit"))
        main = self.tree(repo, "main")

        result = self.propose_json(repo)

        self.assertEqual(self.added(repo), [".kitchen/adopt.json", "ADOPT.md", "decisions.md"])
        for path in ("bin/check", ".githooks/pre-commit", ".agents/skills/verify-calc/SKILL.md", "quality/baseline.json", "AGENTS.md"):
            self.assertEqual(self.tree(repo, BRANCH)[path], main[path], path)
        self.assertEqual({p["id"] for p in result["proposals"]} >= {"check-contract", "pre-commit-hook", "verify-skill",
                                                                    "baseline-ratchet", "agents-md", "secret-scan"}, True,
                         result["proposals"])


class Rerun(ProposeFixture):
    def test_second_run_gives_no_diff(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        first = self.branch_sha(repo)

        again = self.propose_json(repo)
        third = self.propose(repo)

        self.assertEqual(self.branch_sha(repo), first)
        self.assertEqual(self.git(repo, "diff", first, BRANCH), "")
        self.assertEqual(set(self.states(again).values()), {"unchanged"})
        self.assertFalse(again["changed"])
        self.assertIn("nothing new", third.stdout)

    def test_owner_edits_are_detected_and_left_alone(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        self.git(repo, "checkout", "-q", BRANCH)
        edited = self.show(repo, BRANCH, "bin/check").replace("tier_integrate() {", "tier_integrate() {\n  echo owner")
        (repo / "bin" / "check").write_text(edited)
        (repo / "decisions.md").unlink()
        self.git(repo, "commit", "-qam", "owner edits")
        self.git(repo, "checkout", "-q", "main")
        owner = self.branch_sha(repo)

        result = self.propose_json(repo)

        self.assertEqual(self.branch_sha(repo), owner, "the rerun committed over the owner's edits")
        self.assertEqual(self.show(repo, BRANCH, "bin/check"), edited)
        self.assertNotIn("decisions.md", self.tree(repo, BRANCH))
        states = self.states(result)
        self.assertEqual((states["bin/check"], states["decisions.md"]), ("edited by owner", "deleted by owner"))
        self.assertEqual(states[".githooks/pre-commit"], "unchanged")

    def test_branch_checked_out_elsewhere_is_refused(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        self.git(repo, "checkout", "-q", BRANCH)
        sha = self.branch_sha(repo)

        result = self.propose(repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn("is checked out", result.stderr)
        self.assertEqual(self.branch_sha(repo), sha)


class Isolation(ProposeFixture):
    HOOKS = ("post-checkout", "post-commit", "commit-msg", "pre-commit", "reference-transaction", "post-index-change", "pre-push")

    def snapshot(self, repo):
        """Every path in the checkout and in .git, except the objects and the proposal branch's own ref and log."""
        entries = {}
        for folder, dirs, files in os.walk(repo):
            for name in dirs + files:
                path = Path(folder) / name
                rel = path.relative_to(repo).as_posix()
                # .git's own mtime moves when `.git/worktrees` comes and goes; every entry inside .git is still compared
                if rel.startswith((".git/objects", ".git/refs/heads/kitchen", ".git/logs/refs/heads/kitchen")) or rel in (".git", ".git/logs/refs/heads", ".git/refs/heads"):
                    continue
                info = path.lstat()
                entries[rel] = (info.st_mtime_ns, info.st_size, stat.S_IFMT(info.st_mode), info.st_mode)
        return entries

    def make_isolated(self, files):
        origin = self.root / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, env=self.env())
        repo = self.make_repo("calc", files, origin=str(origin))
        hooks = self.root / "local-hooks"
        hooks.mkdir()
        for name in self.HOOKS:  # pre-commit too: an active hook must not run while the proposal is committed
            hook = hooks / name
            hook.write_text("#!/bin/sh\n" + RAN)
            hook.chmod(0o755)
        self.git(repo, "config", "core.hooksPath", str(hooks))
        return repo, origin

    def test_propose_runs_no_code_and_writes_nothing_outside_its_branch(self):
        repo, origin = self.make_isolated(PYTHON_FILES)
        before, origin_refs = self.snapshot(repo), self.git(origin, "for-each-ref")
        status = self.git(repo, "status", "--porcelain=v2", "--branch", "--ignored")

        result = self.propose_json(repo)

        self.assertFalse(self.marker.exists(), "a hook or other repository code ran during --propose")
        self.assertEqual(self.snapshot(repo), before)
        self.assertEqual(self.git(repo, "status", "--porcelain=v2", "--branch", "--ignored"), status)
        self.assertEqual(self.git(origin, "for-each-ref"), origin_refs, "something was pushed")
        self.assertEqual(os.listdir(self.tmpdir), [], "the temporary worktree was left behind")
        listing = self.git(repo, "worktree", "list", "--porcelain").splitlines()
        self.assertEqual([line for line in listing if line.startswith("worktree ")], [f"worktree {repo}"])
        self.assertIsNotNone(self.branch_sha(repo))
        self.assertTrue(result["changed"])

    def test_gh_calls_stay_get_only(self):
        repo = self.make_repo("shop", PYTHON_FILES, origin="https://github.com/example/shop.git")

        result = self.propose_json(repo, gh=self.fake_gh)

        calls = [json.loads(line) for line in self.gh_log.read_text().splitlines()]
        self.assertTrue(calls)
        for call in calls:
            self.assertEqual(call[0], "api")
            self.assertFalse({"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input"} & set(call), call)
        doors = "\n".join(d["command"] for d in result["doors"])
        self.assertIn("repos/example/shop/rulesets", doors)


class Hook(ProposeFixture):
    def hook_repo(self):
        """A scratch repo with the generated hook and a bin/check that only records that it ran."""
        source = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(source)
        repo = self.make_repo("scratch", {"README.md": "x\n", "app.py": "x = 1\n",
                                           "bin/check": "#!/bin/sh\n" + RAN,
                                           ".githooks/pre-commit": self.show(source, BRANCH, ".githooks/pre-commit")},
                              executable=("bin/check", ".githooks/pre-commit"))
        return repo

    def run_hook(self, repo, path):
        return subprocess.run([str(repo / ".githooks" / "pre-commit")], cwd=repo, capture_output=True, text=True,
                              env={**self.env(), "PATH": path})

    def test_missing_gitleaks_fails_with_the_install_command(self):
        repo = self.hook_repo()
        tools = self.root / "tools"
        tools.mkdir()
        for tool in ("git", "grep", "sh"):
            (tools / tool).symlink_to(shutil.which(tool))
        path = f"{tools}{os.pathsep}/usr/bin{os.pathsep}/bin"
        if shutil.which("gitleaks", path=path):
            self.skipTest("gitleaks is installed in the system bin, so it cannot be hidden")
        (repo / "app.py").write_text("x = 2\n")
        self.git(repo, "add", "app.py")

        result = self.run_hook(repo, path)

        self.assertEqual(result.returncode, 1)
        self.assertIn("brew install gitleaks", result.stderr)
        self.assertFalse(self.marker.exists())

    @unittest.skipUnless(shutil.which("gitleaks"), "gitleaks is not installed")
    def test_hook_is_path_scoped(self):
        repo = self.hook_repo()
        (repo / "README.md").write_text("docs only\n")
        self.git(repo, "add", "README.md")

        docs = self.run_hook(repo, os.environ["PATH"])

        self.assertEqual(docs.returncode, 0, docs.stderr)
        self.assertFalse(self.marker.exists(), "bin/check ran for a docs-only commit")
        (repo / "app.py").write_text("x = 2\n")
        self.git(repo, "add", "app.py")
        code = self.run_hook(repo, os.environ["PATH"])
        self.assertEqual(code.returncode, 0, code.stderr)
        self.assertTrue(self.marker.exists(), "bin/check did not run for a code change")


class Prove(ProposeFixture):
    def assert_proved(self, result, broken):
        readiness = result["readiness"]
        self.assertEqual(readiness["files_proposed"]["state"], "yes")
        self.assertEqual(readiness["checks_run_green"]["state"], "yes", readiness)
        self.assertIn(broken, readiness["negative_control_went_red"]["detail"])
        trust = {t["path"]: t["state"] for t in result["trust"]}
        self.assertEqual(trust["bin/check"], "trusted", result["trust"])
        if shutil.which("gitleaks"):
            self.assertEqual(readiness["negative_control_went_red"]["state"], "yes", readiness)
            self.assertEqual(trust[".githooks/pre-commit"], "trusted", result["trust"])
        self.assertEqual(readiness["unattended_ready"]["state"], "not assessed")
        self.assertTrue(result["ran_repository_code"])
        self.assertEqual(os.listdir(self.tmpdir), [], "the temporary worktree was left behind")

    def test_python_negative_control_goes_red(self):
        repo = self.make_repo("calc", PYTHON_FILES)

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assert_proved(result, "tests/test_calc.py")
        self.assertEqual(self.show(repo, BRANCH, "tests/test_calc.py"), PYTHON_FILES["tests/test_calc.py"], "the control was not reverted")
        self.assertIn("negative control went red", self.show(repo, BRANCH, "ADOPT.md"))

    @unittest.skipUnless(node_supports_typescript(), "needs node >= 22.18 (runs .ts tests natively) and npm")
    def test_node_negative_control_goes_red(self):
        repo = self.make_repo("web", NODE_FILES)

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assert_proved(result, "test/calc.test.ts")

    @unittest.skipUnless(dotnet_major(), "dotnet is not installed")
    def test_dotnet_negative_control_goes_red(self):
        repo = self.make_repo("shop", dotnet_files(dotnet_major()))

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assert_proved(result, "Calc.cs")

    def test_a_check_that_cannot_fail_is_untrusted(self):
        files = dict(PYTHON_FILES)
        files["bin/check"] = CANNOT_FAIL
        repo = self.make_repo("calc", files, executable=("bin/check",))

        result = self.propose_json(repo, "--prove", code=1)

        self.assertEqual(self.tree(repo, BRANCH)["bin/check"], self.tree(repo, "main")["bin/check"])
        readiness = result["readiness"]
        self.assertEqual(readiness["checks_run_green"]["state"], "yes")
        self.assertEqual(readiness["negative_control_went_red"]["state"], "no")
        trust = {t["path"]: t for t in result["trust"]}
        self.assertEqual(trust["bin/check"]["state"], "untrusted")
        self.assertIn("stayed green", trust["bin/check"]["why"])

    def test_prove_says_it_runs_repository_code(self):
        repo = self.make_repo("calc", PYTHON_FILES)

        result = self.propose(repo, "--prove")

        self.assertIn("RUNS REPOSITORY CODE", result.stderr)

    def test_prove_needs_propose(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        result = subprocess.run([sys.executable, str(KITCHEN), "adopt", "--check", "--prove", str(repo)],
                                capture_output=True, text=True, env=self.env())
        self.assertEqual(result.returncode, 2)
        self.assertIn("--prove needs --propose", result.stderr)


if __name__ == "__main__":
    unittest.main()
