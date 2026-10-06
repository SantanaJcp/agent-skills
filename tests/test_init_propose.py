"""`kitchen init` and `--prove` on fixture repos in temp dirs: what is written, what is never touched, and
whether the proof can tell a gate that works from one that cannot fail.

Expected files, statuses and commands are written by hand from each fixture's design, not recomputed the way
propose.py does. Regenerate the golden report with KITCHEN_UPDATE_GOLDEN=1, then review the diff by hand.
"""
import hashlib
import json
import os
import pty
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import textwrap
import time
import unittest
from pathlib import Path

from tests.test_init_check import GOLDEN, GUARDS, KITCHEN, KITCHEN_HOOKS, RAN, InitFixture, vendored_hooks

BRANCH = "kitchen/init"


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


class ProposeFixture(InitFixture):
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
        return subprocess.run([sys.executable, str(KITCHEN), "init", str(repo), "--yes", "--base", "main", *extra],
                              capture_output=True, text=True, env=self.env(gh))

    def owner_commit(self, repo, change):
        checkout = self.root / "checkout"
        self.git(repo, "worktree", "add", "--quiet", str(checkout), BRANCH)
        change(checkout)
        self.git(checkout, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "owner edit")
        self.git(repo, "worktree", "remove", "--force", str(checkout))

    def configure(self, text):
        path = self.home / ".config" / "kitchen" / "integrate.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def fill_check(self, repo):
        """What the agent does first: init writes its guess, the agent turns it into the project's own bin/check."""
        self.propose_json(repo)
        def fill(checkout):
            path = checkout / "bin" / "check"
            path.write_text("".join(l for l in path.read_text().splitlines(True) if "# unverified:" not in l))
        self.owner_commit(repo, fill)

    def propose_json(self, repo, *extra, gh=None, code=0):
        result = self.propose(repo, "--json", *extra, gh=gh)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout)["proposal"]

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
                                            ".claude/settings.json", ".githooks/pre-commit", ".kitchen/PRINCIPLES.md", ".kitchen/baseline.json",
                                            ".kitchen/hooks/deny-no-verify", ".kitchen/hooks/deny-recursive-rm",
                                            ".kitchen/hooks/deny-shared-push", ".kitchen/hooks/shellparse.py", ".kitchen/init.json",
                                            "KITCHEN-INIT.md", "bin/check", "decisions.md"])
        tree = self.tree(repo, BRANCH)
        self.assertEqual((tree["bin/check"][0], tree[".githooks/pre-commit"][0]), ("100755", "100755"))
        self.assertEqual((tree[".kitchen/hooks/deny-shared-push"][0], tree[".kitchen/hooks/shellparse.py"][0]), ("100755", "100644"))
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
                                                  "baseline-ratchet": "FAIL", "skills-linked": "FAIL", "branch-protection": "unknown", "agent-hooks": "FAIL", "principles": "FAIL"})
        manifest = json.loads(self.show(repo, BRANCH, ".kitchen/init.json"))
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
        text = re.sub(r"Branch kitchen/init @ [0-9a-f]{7}", "Branch kitchen/init @ <sha>", text)  # the branch holds the kitchen's guards
        golden = GOLDEN / "propose-python.txt"
        if os.environ.get("KITCHEN_UPDATE_GOLDEN"):
            golden.write_text(text)
        self.assertEqual(text, golden.read_text(), f"golden {golden.name} differs; review, then rerun with KITCHEN_UPDATE_GOLDEN=1")
        report_md = self.show(repo, BRANCH, "KITCHEN-INIT.md")
        self.assertNotIn(str(self.root), report_md, "KITCHEN-INIT.md is committed into the target repo: no absolute paths")
        for section in ("Files", "Unverified", "Readiness", "One-way doors"):
            self.assertIn(section, report_md)

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

        self.assertEqual(self.added(repo), [".claude/settings.json", ".kitchen/PRINCIPLES.md", ".kitchen/hooks/deny-no-verify", ".kitchen/hooks/deny-recursive-rm",
                                            ".kitchen/hooks/deny-shared-push", ".kitchen/hooks/shellparse.py",
                                            ".kitchen/init.json", "KITCHEN-INIT.md", "decisions.md"])
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
        self.fill_check(repo)

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assert_proved(result, "tests/test_calc.py")
        self.assertEqual(self.show(repo, BRANCH, "tests/test_calc.py"), PYTHON_FILES["tests/test_calc.py"], "the control was not reverted")
        self.assertIn("negative control went red", self.show(repo, BRANCH, "KITCHEN-INIT.md"))

    @unittest.skipUnless(node_supports_typescript(), "needs node >= 22.18 (runs .ts tests natively) and npm")
    def test_node_negative_control_goes_red(self):
        repo = self.make_repo("web", NODE_FILES)
        self.fill_check(repo)

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assert_proved(result, "test/calc.test.ts")

    @unittest.skipUnless(dotnet_major(), "dotnet is not installed")
    def test_dotnet_negative_control_goes_red(self):
        repo = self.make_repo("shop", dotnet_files(dotnet_major()))
        self.fill_check(repo)

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
        self.fill_check(repo)

        result = self.propose(repo, "--prove")

        self.assertIn("RUNS REPOSITORY CODE", result.stderr)

    def test_check_takes_no_answers(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        result = subprocess.run([sys.executable, str(KITCHEN), "init", "--check", "--prove", str(repo)],
                                capture_output=True, text=True, env=self.env())
        self.assertEqual(result.returncode, 2)
        self.assertIn("--check only reads", result.stderr)



class GuessAndConfig(ProposeFixture):
    """init never times its own guess of the commands; it starts bin/check from the owner's integrate.toml when it can."""

    def test_a_guessed_bin_check_is_never_proved(self):
        repo = self.make_repo("calc", PYTHON_FILES)

        result = self.propose_json(repo, "--prove", code=1)

        self.assertFalse(result["ran_repository_code"])
        self.assertIn("still kitchen's guess", result["readiness"]["checks_run_green"]["detail"])
        self.assertTrue(any("hand the rest to your agent" in line for line in result["next"]))
        self.assertEqual(os.listdir(self.tmpdir), [])

    def test_bin_check_starts_from_integrate_toml_and_is_proved(self):
        self.configure('[projects.calc]\nbase = "main"\npath = ["~/.dotnet", "/opt/private/bin"]\n'
                       'checks = ["python3 -m unittest discover -s tests"]\n')
        repo = self.make_repo("calc", PYTHON_FILES)

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        check = self.show(repo, BRANCH, "bin/check")
        self.assertIn("# from your integrate.toml [projects.calc].checks", check)
        self.assertIn('PATH="$HOME/.dotnet:$PATH"; export PATH', check)
        self.assertNotIn("/opt/private/bin", check)
        self.assertNotIn("# unverified:", check)
        self.assertEqual(result["readiness"]["checks_run_green"]["state"], "yes", result["readiness"])
        self.assertIn("tests/test_calc.py", result["readiness"]["negative_control_went_red"]["detail"])

    def test_a_long_check_reports_its_progress(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        self.owner_commit(repo, lambda c: (c / "bin" / "check").write_text("#!/bin/sh\necho compiling step one\nsleep 3\n"))

        result = subprocess.run([sys.executable, str(KITCHEN), "init", str(repo), "--yes", "--base", "main", "--prove"],
                                capture_output=True, text=True, env={**self.env(), "KITCHEN_PROGRESS_SECONDS": "1"})

        self.assertIn("bin/check commit (run 1 of 2) still running", result.stderr)
        self.assertIn("last line: compiling step one", result.stderr)


class ConfigReview(ProposeFixture):
    """Round 1 of the review of the integrate.toml seed; each test was red at 8cf9dbd."""

    def test_a_check_that_runs_bin_check_is_not_copied_into_it(self):  # P1: bin/check would call itself
        self.configure('[projects.calc]\nbase = "main"\nchecks = ["bin/check integrate"]\n')
        repo = self.make_repo("calc", PYTHON_FILES)

        self.propose_json(repo)

        tier = self.show(repo, BRANCH, "bin/check").split("tier_commit() {", 1)[1].split("}", 1)[0]
        self.assertNotIn("bin/check", tier)

    def test_the_owner_home_becomes_home_in_committed_files(self):
        self.configure(f'[projects.calc]\nbase = "main"\nchecks = ["{self.home}/tools/check --commit"]\n')
        repo = self.make_repo("calc", PYTHON_FILES)

        self.propose_json(repo)

        for path in ("bin/check", "KITCHEN-INIT.md"):
            self.assertNotIn(str(self.home), self.show(repo, BRANCH, path), path)
        self.assertIn("$HOME/tools/check --commit", self.show(repo, BRANCH, "bin/check"))

    def test_a_path_folder_with_shell_syntax_stays_out(self):
        self.configure('[projects.calc]\nbase = "main"\npath = ["~/tools$(touch pwned)"]\nchecks = ["true"]\n')
        repo = self.make_repo("calc", PYTHON_FILES)

        self.propose_json(repo)

        check = self.show(repo, BRANCH, "bin/check")
        self.assertNotIn("pwned", check)
        self.assertIn("characters the shell would interpret", check)

    def test_wrong_types_in_integrate_toml_are_an_error(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        for text in ('[projects.calc]\nchecks = "true"\n', '[projects.calc]\nchecks = false\n', "projects = 1\n"):
            with self.subTest(text=text):
                self.configure(text)
                result = self.propose(repo)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("must be", result.stderr)

    def test_an_edited_manifest_does_not_vouch_for_a_guess(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)

        def edit_check_and_its_digest(checkout):
            check = checkout / "bin" / "check"
            check.write_text(check.read_text().replace("python3 -m unittest discover -s tests", "python3 -m unittest discover -s tests -q"))
            manifest_path = checkout / ".kitchen" / "init.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["bin/check"]["sha256"] = hashlib.sha256(check.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")  # the seal is now stale
        self.owner_commit(repo, edit_check_and_its_digest)

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assertTrue(result["ran_repository_code"], result["readiness"])


class AgentHooks(ProposeFixture):
    """The guards travel with the repo: the copy on the branch runs from .claude/settings.json and fails closed."""

    def hook_commands(self, repo):
        settings = json.loads(self.show(repo, BRANCH, ".claude/settings.json"))
        return [h["command"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]

    def run_hook(self, command, project_dir, shell_command):
        payload = json.dumps({"tool_name": "Bash", "cwd": str(project_dir), "tool_input": {"command": shell_command}})
        return subprocess.run(["sh", "-c", command], input=payload, capture_output=True, text=True,
                              env={**self.env(), "CLAUDE_PROJECT_DIR": str(project_dir)})

    def test_the_copied_guards_block_and_allow_like_the_kitchen(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        checkout = self.root / "checkout"
        self.git(repo, "worktree", "add", "--quiet", str(checkout), BRANCH)
        commands = self.hook_commands(repo)
        self.assertEqual(len(commands), len(GUARDS))
        push = next(c for c in commands if "deny-shared-push" in c)

        blocked = self.run_hook(push, checkout, "git push origin main")
        allowed = self.run_hook(push, checkout, "ls")

        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertIn("Blocked by the kitchen hook deny-shared-push", blocked.stderr)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_a_missing_copy_blocks_instead_of_passing(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        broken = self.root / "settings-without-guards"
        (broken / ".claude").mkdir(parents=True)
        (broken / ".claude" / "settings.json").write_text(self.show(repo, BRANCH, ".claude/settings.json"))

        result = self.run_hook(self.hook_commands(repo)[0], broken, "ls")

        self.assertEqual(result.returncode, 2)
        self.assertIn("kitchen: guard missing", result.stderr)

    def test_an_unknown_project_or_a_broken_settings_link_still_blocks(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        command = self.hook_commands(repo)[0]
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        unset = subprocess.run(["sh", "-c", command], input=payload, capture_output=True, text=True,
                               env={k: v for k, v in self.env().items() if k != "CLAUDE_PROJECT_DIR"})
        dangling = self.root / "dangling"
        (dangling / ".claude").mkdir(parents=True)
        (dangling / ".claude" / "settings.json").symlink_to(self.root / "nowhere.json")

        broken = self.run_hook(command, dangling, "ls")

        self.assertEqual((unset.returncode, broken.returncode), (2, 2), unset.stderr + broken.stderr)
        self.assertIn("CLAUDE_PROJECT_DIR is not set", unset.stderr)
        self.assertIn("guard missing", broken.stderr)

    def test_a_checkout_without_project_settings_is_not_locked(self):
        # measured 2026-10-05: a Claude Code session that loaded the settings on kitchen/init, then switched to a branch
        # from before init, kept the hooks; the missing copy blocked every Bash call
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose_json(repo)
        before_init = self.root / "before-init"
        before_init.mkdir()

        result = self.run_hook(self.hook_commands(repo)[0], before_init, "ls")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_stale_copy_fails_the_check_and_is_not_overwritten(self):
        files = {**PYTHON_FILES, **vendored_hooks()}
        files[".kitchen/hooks/deny-shared-push"] += "# an older copy\n"
        repo = self.make_repo("calc", files)

        report = json.loads(subprocess.run([sys.executable, str(KITCHEN), "init", "--check", str(repo), "--json"],
                                           capture_output=True, text=True, env=self.env()).stdout)
        result = self.propose_json(repo)

        verdict = next(m for m in report["must_haves"] if m["id"] == "agent-hooks")
        self.assertEqual(verdict["status"], "FAIL")
        self.assertIn("deny-shared-push differ from this kitchen's copy", verdict["proof"])
        self.assertTrue(self.show(repo, BRANCH, ".kitchen/hooks/deny-shared-push").endswith("# an older copy\n"))
        self.assertIn("agent-hooks", {p["id"] for p in result["proposals"]})

    def test_existing_settings_get_a_proposal_not_an_edit(self):
        files = {**PYTHON_FILES, ".claude/settings.json": '{"permissions": {"allow": []}}\n'}
        repo = self.make_repo("calc", files)

        result = self.propose_json(repo)

        self.assertEqual(self.show(repo, BRANCH, ".claude/settings.json"), '{"permissions": {"allow": []}}\n')
        text = next(p["text"] for p in result["proposals"] if p["id"] == "agent-hooks")
        self.assertIn("kitchen left it alone", text)
        self.assertIn("deny-shared-push", text)


class Refresh(ProposeFixture):
    """init follows the kitchen: a copy it wrote and nobody edited is refreshed; an edited copy is left alone."""

    def older_kitchen(self):
        """A copy of this kitchen whose deny-shared-push differs: what a repo initialized last month received."""
        old = self.root / "old-kitchen"
        for part in ("bin", "lib", "hooks", "templates"):
            shutil.copytree(KITCHEN.parent.parent / part, old / part, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(KITCHEN.parent.parent / "PRINCIPLES.md", old / "PRINCIPLES.md")
        guard = old / "hooks" / "deny-shared-push"
        guard.write_text(guard.read_text() + "# an older release\n")
        return old

    def init_with(self, kitchen, repo):
        result = subprocess.run([sys.executable, str(kitchen / "bin" / "kitchen"), "init", str(repo), "--yes", "--base", "main", "--json"],
                                capture_output=True, text=True, env=self.env())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)["proposal"]

    def state(self, result, path):
        return next(f["state"] for f in result["files"] if f["path"] == path)

    def test_an_untouched_copy_follows_the_kitchen(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.init_with(self.older_kitchen(), repo)

        result = self.propose_json(repo)

        self.assertEqual(self.state(result, ".kitchen/hooks/deny-shared-push"), "refreshed")
        self.assertEqual(self.show(repo, BRANCH, ".kitchen/hooks/deny-shared-push"), (KITCHEN_HOOKS / "deny-shared-push").read_text())
        manifest = json.loads(self.show(repo, BRANCH, ".kitchen/init.json"))
        recorded = manifest["files"][".kitchen/hooks/deny-shared-push"]["sha256"]
        self.assertEqual(recorded, hashlib.sha256((KITCHEN_HOOKS / "deny-shared-push").read_bytes()).hexdigest())
        again = self.propose_json(repo)
        self.assertEqual(self.state(again, ".kitchen/hooks/deny-shared-push"), "unchanged")

    def test_an_edited_manifest_vouches_for_nothing(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.init_with(self.older_kitchen(), repo)

        def edit_copy_and_its_manifest_entry(checkout):
            guard = checkout / ".kitchen" / "hooks" / "deny-shared-push"
            guard.write_text(guard.read_text() + "# owner custom guard\n")
            manifest_path = checkout / ".kitchen" / "init.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"][".kitchen/hooks/deny-shared-push"]["sha256"] = hashlib.sha256(guard.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")  # its own sha256 is now stale
        self.owner_commit(repo, edit_copy_and_its_manifest_entry)

        result = self.propose_json(repo)

        self.assertNotEqual(self.state(result, ".kitchen/hooks/deny-shared-push"), "refreshed")
        self.assertTrue(self.show(repo, BRANCH, ".kitchen/hooks/deny-shared-push").endswith("# owner custom guard\n"))

    def test_a_mode_change_is_the_owners_edit(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.init_with(self.older_kitchen(), repo)
        self.owner_commit(repo, lambda checkout: (checkout / ".kitchen" / "hooks" / "deny-shared-push").chmod(0o644))

        result = self.propose_json(repo)

        self.assertNotEqual(self.state(result, ".kitchen/hooks/deny-shared-push"), "refreshed")
        self.assertEqual(self.tree(repo, BRANCH)[".kitchen/hooks/deny-shared-push"][0], "100644")

    def test_settings_kitchen_wrote_follow_the_kitchen(self):
        old = self.older_kitchen()
        source = old / "lib" / "kitchen" / "repocheck.py"
        source.write_text(source.read_text().replace('[ -e "$s" ] || [ -L "$s" ] || exit 0; ', ""))  # the command before the lockout fix
        repo = self.make_repo("calc", PYTHON_FILES)
        self.init_with(old, repo)
        commands = lambda: " ".join(AgentHooks.hook_commands(self, repo))
        self.assertNotIn('|| exit 0', commands())

        result = self.propose_json(repo)

        self.assertEqual(self.state(result, ".claude/settings.json"), "refreshed")
        self.assertIn('|| exit 0', commands())

    def test_a_proof_with_nothing_new_still_updates_the_report(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.fill_check(repo)
        first = self.git(repo, "rev-parse", BRANCH).strip()
        self.assertIn("checks run green            not run", self.show(repo, BRANCH, "KITCHEN-INIT.md"))

        result = self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assertEqual([f for f in result["files"] if f["state"] in ("written", "refreshed")], [])
        self.assertNotEqual(self.git(repo, "rev-parse", BRANCH).strip(), first)
        report = self.show(repo, BRANCH, "KITCHEN-INIT.md")
        self.assertNotIn("checks run green            not run", report)
        self.assertIn("negative control went red", report)

    def test_a_report_whose_mode_the_owner_changed_is_left_alone(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.fill_check(repo)
        self.owner_commit(repo, lambda checkout: (checkout / "KITCHEN-INIT.md").chmod(0o755))
        before = self.show(repo, BRANCH, "KITCHEN-INIT.md")

        self.propose_json(repo, "--prove", code=0 if shutil.which("gitleaks") else 1)

        self.assertEqual(self.tree(repo, BRANCH)["KITCHEN-INIT.md"][0], "100755")
        self.assertEqual(self.show(repo, BRANCH, "KITCHEN-INIT.md"), before)

    def test_an_edited_copy_is_left_alone(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.init_with(self.older_kitchen(), repo)
        checkout = self.root / "checkout"
        self.git(repo, "worktree", "add", "--quiet", str(checkout), BRANCH)
        guard = checkout / ".kitchen" / "hooks" / "deny-shared-push"
        guard.write_text(guard.read_text() + "# the owner's change\n")
        self.git(checkout, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "owner edit")
        self.git(repo, "worktree", "remove", "--force", str(checkout))

        result = self.propose_json(repo)

        self.assertEqual(self.state(result, ".kitchen/hooks/deny-shared-push"), "edited by owner")
        self.assertTrue(self.show(repo, BRANCH, ".kitchen/hooks/deny-shared-push").endswith("# the owner's change\n"))


class Ask(ProposeFixture):
    """`kitchen init` asks numbered questions in a terminal and writes only what was answered yes."""

    def run_tty(self, argv, replies):
        pid, fd = pty.fork()
        if pid == 0:
            os.execve(sys.executable, [sys.executable, str(KITCHEN), *argv], self.env())
        output, pending = b"", list(replies)
        while True:
            ready, _, _ = select.select([fd], [], [], 60)
            if not ready:  # waiting on input nobody will type: end it, so the test fails instead of hanging
                os.kill(pid, signal.SIGKILL)
                break
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            output += data
            if output.rstrip(b" ").endswith(b">") and pending:
                os.write(fd, (pending.pop(0) + "\n").encode())
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status), output.decode(errors="replace"), pending

    def config(self, name):
        path = self.home / ".config" / "kitchen" / name
        return path.read_text() if path.exists() else None

    def test_answers_decide_what_is_written(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        # branch: yes; personal: yes; the base is unknown (no origin/HEAD), so it is asked: dev. No prove question:
        # bin/check would be kitchen's guess of the commands
        code, output, left = self.run_tty(["init", str(repo)], ["1", "1", "dev"])
        self.assertEqual((code, left), (0, []), output)
        self.assertIn("1. Write the missing pieces on branch kitchen/init?", output)
        self.assertIn("Which branch is the shared base", output)
        self.assertTrue(self.git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/kitchen/init"), output)
        self.assertEqual(self.config("projects.txt"), f"{repo}\n")
        self.assertEqual(self.config("integrate.toml"), '[projects.calc]\nbase = "dev"\nchecks = ["bin/check integrate"]\n')
        self.assertNotIn("Prove the gate", output)
        self.assertIn("not proved bin/check holds kitchen's guess", output)

    def test_no_writes_nothing(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        code, output, left = self.run_tty(["init", str(repo)], ["2", "2"])  # branch: no; personal: no (prove is not asked)
        self.assertEqual((code, left), (0, []), output)
        self.assertEqual(self.git(repo, "branch", "--list", "kitchen/init").strip(), "")
        self.assertIsNone(self.config("projects.txt"))
        self.assertIsNone(self.config("integrate.toml"))

    def test_yes_refuses_to_guess_an_unknown_base(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        result = subprocess.run([sys.executable, str(KITCHEN), "init", str(repo), "--yes"], capture_output=True, text=True, env=self.env())
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("pass --base", result.stderr)
        self.assertIsNone(self.config("integrate.toml"))

    def test_rerun_adds_the_personal_layer_once(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        self.propose(repo)
        again = self.propose(repo)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(self.config("projects.txt"), f"{repo}\n")
        self.assertEqual(self.config("integrate.toml").count("[projects.calc]"), 1)

    def test_an_unreadable_integrate_toml_is_an_error(self):
        repo = self.make_repo("calc", PYTHON_FILES)
        path = self.home / ".config" / "kitchen" / "integrate.toml"
        path.parent.mkdir(parents=True)
        path.write_text("[projects\n")
        result = self.propose(repo)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("cannot parse", result.stderr)
        self.assertEqual(path.read_text(), "[projects\n")


class ReviewRound1(ProposeFixture):
    """One test per finding of the first review of PR #35; each was red at 1520825."""

    def test_filters_never_run_without_prove(self):  # P1-1
        repo = self.make_repo("calc", {**PYTHON_FILES, ".gitattributes": "*.py filter=probe\n*.md filter=probe\n"})
        self.git(repo, "config", "filter.probe.smudge", 'touch "$INIT_MARKER"; cat')
        self.git(repo, "config", "filter.probe.clean", 'touch "$INIT_MARKER"; cat')

        result = self.propose_json(repo)

        self.assertFalse(self.marker.exists(), "a filter of the target repo ran during --propose")
        self.assertFalse(result["ran_repository_code"])
        self.assertIn("bin/check", self.added(repo))
        self.owner_commit(repo, lambda c: (c / "bin" / "check").write_text("#!/bin/sh\nexit 0\n"))
        prove = self.propose(repo, "--prove")
        self.assertIn("filters", prove.stderr)

    def test_a_symlinked_kitchen_folder_is_refused_before_anything_is_touched(self):  # P1-2
        outside = self.root / "outside"
        outside.mkdir()
        manifest = outside / "init.json"
        manifest.write_text('{"files": {}, "owner": "keep"}\n')
        repo = self.make_repo("calc", {**PYTHON_FILES, "quality/baseline.json": "{}\n"})
        (repo / ".kitchen").symlink_to(outside, target_is_directory=True)
        self.git(repo, "add", ".kitchen")
        self.git(repo, "commit", "-qm", "symlink")

        result = self.propose(repo)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(manifest.read_text(), '{"files": {}, "owner": "keep"}\n')
        self.assertIsNone(self.branch_sha(repo))

    def test_a_symbolic_proposal_branch_is_refused(self):  # P1-3
        repo = self.make_repo("calc", PYTHON_FILES)
        self.git(repo, "symbolic-ref", "refs/heads/kitchen/init", "refs/heads/main")
        main = self.git(repo, "rev-parse", "main").strip()

        result = self.propose(repo)

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("symbolic", result.stderr)
        self.assertEqual(self.git(repo, "rev-parse", "main").strip(), main)
        self.assertEqual(self.git(repo, "symbolic-ref", "refs/heads/kitchen/init").strip(), "refs/heads/main")
        self.assertEqual(self.git(repo, "status", "--porcelain"), "")

    def test_a_check_that_swallows_failures_and_fails_once_is_untrusted(self):  # P1-4
        check = "#!/bin/sh\npython3 -m unittest discover -s tests || true\nmkdir .check-once\n"
        repo = self.make_repo("calc", {**PYTHON_FILES, "bin/check": check}, executable=("bin/check",))

        result = self.propose_json(repo, "--prove", code=1)

        trust = {t["path"]: t for t in result["trust"]}
        self.assertEqual(trust["bin/check"]["state"], "untrusted")
        self.assertIn("not stable", trust["bin/check"]["why"])
        self.assertNotEqual(result["readiness"]["checks_run_green"]["state"], "yes")

    def test_red_that_never_names_the_broken_file_is_untrusted(self):  # P1-4
        repo = self.make_repo("calc", {**PYTHON_FILES, "bin/check": "#!/bin/sh\ngit diff --quiet\n"}, executable=("bin/check",))

        result = self.propose_json(repo, "--prove", code=1)

        trust = {t["path"]: t for t in result["trust"]}
        self.assertEqual(trust["bin/check"]["state"], "untrusted")
        self.assertIn("never names tests/test_calc.py", trust["bin/check"]["why"])
        self.assertEqual(result["readiness"]["negative_control_went_red"]["state"], "no")

    def test_a_signal_stops_the_check_and_removes_the_worktree(self):  # P1-5
        pid_file = Path(f"{self.marker}.pid")
        check = f'#!/bin/sh\necho $$ > "{pid_file}"\nsleep 120\n'
        repo = self.make_repo("calc", {**PYTHON_FILES, "bin/check": check}, executable=("bin/check",))
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            with self.subTest(signal=signum.name):
                pid_file.unlink(missing_ok=True)
                process = subprocess.Popen([sys.executable, str(KITCHEN), "init", "--yes", "--base", "main", "--prove", str(repo), "--json"],
                                           env=self.env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for _ in range(400):
                    if pid_file.exists() and pid_file.read_text().strip():
                        break
                    time.sleep(0.05)
                self.assertTrue(pid_file.exists(), "bin/check never started")
                process.send_signal(signum)
                process.communicate(timeout=30)
                pid = int(pid_file.read_text())
                alive = subprocess.run(["kill", "-0", str(pid)], capture_output=True).returncode == 0
                if alive:
                    os.kill(pid, signal.SIGKILL)
                self.assertFalse(alive, "the check kept running after kitchen was stopped")
                self.assertEqual(process.returncode, 128 + signum)
                listing = self.git(repo, "worktree", "list", "--porcelain").splitlines()
                self.assertEqual([line for line in listing if line.startswith("worktree ")], [f"worktree {repo}"])
                self.assertEqual(os.listdir(self.tmpdir), [])

    def test_an_owner_manifest_is_left_alone(self):  # P2-6
        owner = '{"files": {}, "owner": "keep"}\n'
        repo = self.make_repo("calc", {**PYTHON_FILES, ".kitchen/init.json": owner})

        result = self.propose_json(repo)

        self.assertEqual(self.show(repo, BRANCH, ".kitchen/init.json"), owner)
        self.assertIn("bin/check", self.added(repo))
        self.assertTrue(any(".kitchen/init.json" in note for note in result["notes"]), result["notes"])

    def test_an_edited_kitchen_manifest_keeps_the_owner_fields(self):  # P2-6
        repo = self.make_repo("calc", {**PYTHON_FILES, "quality/baseline.json": "{}\n"})
        self.propose_json(repo)
        self.git(repo, "checkout", "-q", BRANCH)
        data = json.loads((repo / ".kitchen" / "init.json").read_text())
        data["owner"] = "keep"
        (repo / ".kitchen" / "init.json").write_text(json.dumps(data, indent=2) + "\n")
        self.git(repo, "rm", "-q", "quality/baseline.json")
        self.git(repo, "commit", "-qam", "owner edits")
        self.git(repo, "checkout", "-q", "main")
        edited = self.show(repo, BRANCH, ".kitchen/init.json")

        result = self.propose_json(repo)

        self.assertIn(".kitchen/baseline.json", self.tree(repo, BRANCH), "the newly missing baseline was not written")
        self.assertEqual(self.show(repo, BRANCH, ".kitchen/init.json"), edited)
        self.assertTrue(any(".kitchen/init.json" in note for note in result["notes"]), result["notes"])

    def test_control_characters_in_paths_never_reach_generated_scripts(self):  # P2-7
        folder = 'pkg\ntouch "$INIT_MARKER"\n#'
        repo = self.make_repo("oddpath", {f"{folder}/package.json": '{"name": "x", "scripts": {"test": "true"}}\n'})

        self.propose_json(repo)

        check = self.show(repo, BRANCH, "bin/check")
        self.assertFalse([line for line in check.splitlines() if line.lstrip().startswith("touch")], check)
        self.git(repo, "checkout", "-q", BRANCH)
        subprocess.run([str(repo / "bin" / "check"), "commit"], cwd=repo, env=self.env(), capture_output=True)
        self.assertFalse(self.marker.exists(), "a path injected a command into bin/check")


if __name__ == "__main__":
    unittest.main()
