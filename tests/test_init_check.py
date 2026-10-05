"""`kitchen init --check`: golden reports on fixture repos, and proof that it writes and runs nothing.

Expected verdicts are written by hand from each fixture's design, not recomputed the way repocheck.py does.
Regenerate the golden text files with KITCHEN_UPDATE_GOLDEN=1, then review the diff by hand.
"""
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

KITCHEN = Path(__file__).resolve().parent.parent / "bin" / "kitchen"
GOLDEN = Path(__file__).resolve().parent / "golden" / "init"
MUST_HAVE_IDS = ["check-contract", "pre-commit-hook", "agents-md", "verify-skill", "decisions",
                 "secret-scan", "baseline-ratchet", "skills-linked", "branch-protection", "agent-hooks", "principles"]
KITCHEN_HOOKS = KITCHEN.parent.parent / "hooks"
GUARDS = ("deny-no-verify", "deny-recursive-rm", "deny-shared-push")


def vendored_hooks():
    """A repo's copy of the kitchen's guards, and a .claude/settings.json that runs each one."""
    files = {f".kitchen/hooks/{name}": (KITCHEN_HOOKS / name).read_text() for name in GUARDS + ("shellparse.py",)}
    hooks = [{"type": "command", "command": f".kitchen/hooks/{name}"} for name in GUARDS]
    files[".claude/settings.json"] = json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": hooks}]}})
    return files

# Every executable a fixture ships touches $INIT_MARKER when run: init must never create it.
RAN = 'touch "$INIT_MARKER"\n'

BIN_CHECK = "#!/bin/sh\n" + RAN + textwrap.dedent("""\
    case "$1" in
      --list) printf '%s\\n' commit integrate nightly verify-tree ;;
      commit) python3 scripts/baseline.py --check quality/baseline.json ;;
      integrate|nightly) python3 -m unittest ;;
      verify-tree) python3 -m unittest discover -s tests ;;
      *) echo "unknown tier: $1" >&2; exit 2 ;;
    esac
    """)

FAKE_GH = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    with open(os.environ["FAKE_GH_LOG"], "a") as log:
        log.write(json.dumps(sys.argv[1:]) + "\\n")
    responses = json.load(open(os.environ["FAKE_GH_RESPONSES"]))
    endpoint = sys.argv[-1]
    if endpoint in responses:
        print(json.dumps(responses[endpoint]))
        sys.exit(0)
    print("gh: Not Found (HTTP 404)", file=sys.stderr)
    sys.exit(1)
    """)

PROTECTED = {
    "repos/example/shop": {"default_branch": "main"},
    "repos/example/shop/branches/main": {"protected": True, "protection": {"required_status_checks": {"enforcement_level": "off", "contexts": [], "checks": []}}},
    "repos/example/shop/rules/branches/main": [{"type": "deletion"}, {"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "check"}]}}],
}


def complete_files():
    return {
        "bin/check": BIN_CHECK,
        ".githooks/pre-commit": "#!/bin/sh\n" + RAN + "gitleaks git --pre-commit --staged\nexec bin/check commit\n",
        "scripts/baseline.py": "import sys\n" + RAN.replace("touch", "# touch"),
        "quality/baseline.json": '{"todo_comments": ["src/app.py:3"]}\n',
        "AGENTS.md": "# Shop\n\nProve behavior with the `verify-shop` skill; `bin/check commit` runs on every commit.\n"
                     "Principles: `.kitchen/PRINCIPLES.md`.\n",
        ".kitchen/PRINCIPLES.md": (KITCHEN.parent.parent / "PRINCIPLES.md").read_text(),
        "CLAUDE.md": "@AGENTS.md\n",
        "decisions.md": "# Decisions\n\n- [x] 2026-01-02 keep one check contract\n",
        ".agents/skills/verify-shop/SKILL.md": "---\nname: verify-shop\ndescription: Prove the shop works.\n---\n",
        ".agents/skills/verify-shop/features/README.md": "# Features\n\n- orders.md\n",
        ".agents/skills/verify-shop/features/orders.md": "# Orders\n",
        "tests/test_feature_map.py": "# Every route needs a row in the verify-shop feature map.\nMAP = '.agents/skills/verify-shop/features'\n",
        "pyproject.toml": "[project]\nname = \"shop\"\n\n[tool.ruff]\nline-length = 100\n",
        "src/app.py": "print('shop')\n",
        ".gitignore": ".claude/skills/\n",
        **vendored_hooks(),
    }


class InitFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        (self.home / ".gitconfig").write_text("")
        self.marker = self.root / "repository-code-ran"
        self.gh_log = self.root / "gh.log"
        self.gh_responses = self.root / "gh.json"
        self.gh_responses.write_text("{}")
        fake = self.root / "fake-gh"
        fake.write_text(FAKE_GH)
        fake.chmod(0o755)
        self.fake_gh = fake

    def tearDown(self):
        self.tmp.cleanup()

    def env(self, gh=None):
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update({"HOME": str(self.home), "GIT_CONFIG_GLOBAL": str(self.home / ".gitconfig"), "GIT_CONFIG_NOSYSTEM": "1",
                    "INIT_MARKER": str(self.marker), "KITCHEN_GH": str(gh or self.root / "no-such-gh"),
                    "FAKE_GH_LOG": str(self.gh_log), "FAKE_GH_RESPONSES": str(self.gh_responses)})
        return env

    def make_repo(self, name, files, executable=(), origin=None, hooks_path=None):
        repo = self.root / name
        for rel, text in files.items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        for rel in executable:
            (repo / rel).chmod(0o755)
        env = {**self.env(), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
        run = lambda *args: subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)
        run("init", "-q", "-b", "main")
        run("add", "-A")
        run("commit", "-q", "-m", "init")
        if origin:
            run("remote", "add", "origin", origin)
        if hooks_path:
            run("config", "core.hooksPath", hooks_path)
        return repo

    def make_complete(self):
        files = complete_files()
        repo = self.make_repo("complete", files, executable=("bin/check", ".githooks/pre-commit", *(f".kitchen/hooks/{g}" for g in GUARDS)),
                              origin="https://github.com/example/shop.git", hooks_path=".githooks")
        (repo / ".claude" / "skills").mkdir(parents=True)
        (repo / ".claude" / "skills" / "verify-shop").symlink_to("../../.agents/skills/verify-shop")
        self.gh_responses.write_text(json.dumps(PROTECTED))
        return repo

    def init_check(self, repo, *extra, gh=None):
        return subprocess.run([sys.executable, str(KITCHEN), "init", "--check", str(repo), *extra],
                              capture_output=True, text=True, env=self.env(gh))

    def report(self, repo, gh=None):
        result = self.init_check(repo, "--json", gh=gh)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, report["missing"], result.stderr)
        return report

    def statuses(self, report):
        return {m["id"]: m["status"] for m in report["must_haves"]}

    def assert_golden(self, name, repo, gh=None):
        result = self.init_check(repo, gh=gh)
        text = result.stdout.replace(str(repo), "<repo>")
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        text = text.replace(f"HEAD {head}", "HEAD <sha>") if head else text  # the complete fixture copies the kitchen's guards
        golden = GOLDEN / f"{name}.txt"
        if os.environ.get("KITCHEN_UPDATE_GOLDEN"):
            golden.parent.mkdir(parents=True, exist_ok=True)
            golden.write_text(text)
        self.assertEqual(text, golden.read_text(), f"golden {golden.name} differs; review, then rerun with KITCHEN_UPDATE_GOLDEN=1")
        return result


class GoldenReports(InitFixture):
    def test_dotnet_repo(self):
        repo = self.make_repo("dotnet", {
            "Shop.sln": "Microsoft Visual Studio Solution File\n",
            "global.json": '{"sdk": {"version": "10.0.100"}}\n',
            "src/Shop.Api/Shop.Api.csproj": "<Project Sdk=\"Microsoft.NET.Sdk.Web\"></Project>\n",
            "tests/Shop.Tests/Shop.Tests.csproj": "<Project Sdk=\"Microsoft.NET.Sdk\"></Project>\n",
            ".editorconfig": "[*.cs]\ndotnet_diagnostic.CA2007.severity = error\n",
        })

        result = self.assert_golden("dotnet", repo)

        report = self.report(repo)
        self.assertEqual(list(report["stacks"]), ["dotnet"])
        self.assertEqual([(c["path"], c["stack"], c["lint"]["status"]) for c in report["components"]], [(".", "dotnet", "PASS")])
        self.assertEqual(self.statuses(report), {**{i: "FAIL" for i in MUST_HAVE_IDS}, "branch-protection": "unknown"})
        self.assertEqual(result.returncode, 11)

    def test_typescript_monorepo(self):
        repo = self.make_repo("typescript", {
            "package.json": '{"private": true, "workspaces": ["packages/*"], "scripts": {"lint": "eslint ."}}\n',
            "package-lock.json": "{}\n",
            "eslint.config.js": "export default [];\n",
            "packages/web/package.json": '{"name": "web"}\n',
            "packages/web/src/index.ts": "export const x = 1;\n",
            "tools/ui/package.json": '{"name": "ui"}\n',
            ".husky/pre-commit": "npx lint-staged\n",
            "AGENTS.md": "# Web\n\nRun npm test.\n",
        }, hooks_path=".husky")

        self.assert_golden("typescript", repo)

        report = self.report(repo)
        components = {c["path"]: (c["lockfile"]["status"], c["lint"]["status"]) for c in report["components"]}
        self.assertEqual(components, {".": ("PASS", "PASS"), "packages/web": ("PASS", "PASS"), "tools/ui": ("PASS", "PASS")})
        statuses = self.statuses(report)
        self.assertEqual(statuses["pre-commit-hook"], "FAIL", "the husky hook is not executable, so git skips it")
        self.assertEqual(statuses["agents-md"], "FAIL", "AGENTS.md names no verify command")

    def test_python_repo(self):
        repo = self.make_repo("python", {
            "pyproject.toml": "[project]\nname = \"tool\"\n",
            "requirements-dev.txt": "pytest\n",
            "services/api/requirements.txt": "flask\n",
            "services/api/setup.cfg": "[flake8]\nmax-line-length = 100\n",
            "decisions.md": "# Decisions\n",
        })

        self.assert_golden("python", repo)

        report = self.report(repo)
        components = {c["path"]: (c["manifest"], c["lint"]["status"]) for c in report["components"]}
        self.assertEqual(components, {".": ("pyproject.toml", "FAIL"), "services/api": ("services/api/requirements.txt", "PASS")})
        self.assertEqual(self.statuses(report)["decisions"], "PASS")

    def test_unknown_stack_is_unsupported_not_guessed(self):
        repo = self.make_repo("unknown", {"go.mod": "module example.com/x\n", "main.go": "package main\n", "Makefile": "all:\n"})

        result = self.assert_golden("unknown", repo)

        report = self.report(repo)
        self.assertEqual((report["stack_status"], report["stacks"], report["components"]), ("unsupported", {}, []))
        self.assertEqual(report["unsupported"], ["go.mod"])
        self.assertIn("unsupported  no .NET, Node or Python manifest", result.stdout)
        self.assertEqual(result.returncode, 11)

    def test_complete_repo_passes_every_must_have(self):
        repo = self.make_complete()

        result = self.assert_golden("complete", repo, gh=self.fake_gh)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(set(self.statuses(self.report(repo, gh=self.fake_gh)).values()), {"PASS"})
        self.assertNotIn("Next steps", result.stdout)


class ReadOnly(InitFixture):
    def snapshot(self, repo):
        """Every path under the repo (including .git) with its mtime, size and mode, plus git's own view."""
        entries = {}
        for folder, dirs, files in os.walk(repo):
            for name in dirs + files:
                path = Path(folder) / name
                info = path.lstat()
                entries[str(path.relative_to(repo))] = (info.st_mtime_ns, info.st_size, stat.S_IFMT(info.st_mode), info.st_mode)
        git_status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain=v2", "--ignored", "--branch"],
                                    capture_output=True, text=True, env={**self.env(), "GIT_OPTIONAL_LOCKS": "0"}).stdout
        return entries, git_status

    def test_writes_nothing_and_runs_no_repository_code(self):
        repo = self.make_complete()
        (repo / "src" / "untracked.py").write_text("x = 1\n")
        before = self.snapshot(repo)

        text = self.init_check(repo, gh=self.fake_gh)
        machine = self.init_check(repo, "--json", gh=self.fake_gh)

        self.assertEqual((text.returncode, machine.returncode), (0, 0), text.stdout)
        self.assertEqual(self.snapshot(repo), before)
        self.assertFalse(self.marker.exists(), "init executed a hook or bin/check from the inspected repo")

    def test_output_is_idempotent(self):
        repo = self.make_complete()

        runs = [self.init_check(repo, *flags, gh=self.fake_gh).stdout for flags in ((), (), ("--json",), ("--json",))]

        self.assertEqual(runs[0], runs[1])
        self.assertEqual(runs[2], runs[3])

    def test_gh_calls_are_get_only(self):
        repo = self.make_complete()

        self.init_check(repo, gh=self.fake_gh)

        calls = [json.loads(line) for line in self.gh_log.read_text().splitlines()]
        self.assertEqual([c[0] for c in calls], ["api"] * 3)
        for call in calls:
            self.assertFalse({"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input"} & set(call), call)


class MustHaves(InitFixture):
    def agent_hooks_verdict(self, settings=None, executable=True):
        files = {"README.md": "x\n", **vendored_hooks()}
        if settings is not None:
            files[".claude/settings.json"] = json.dumps(settings)
        repo = self.make_repo("hooks", files, executable=tuple(f".kitchen/hooks/{g}" for g in GUARDS) if executable else ())
        return next(m for m in self.report(repo)["must_haves"] if m["id"] == "agent-hooks")

    def test_agent_hooks_pass_only_when_bash_runs_each_guard(self):
        def group(matcher, command):
            return {"hooks": {"PreToolUse": [{"matcher": matcher, "hooks": [{"type": "command", "command": command.format(g)} for g in GUARDS]}]}}

        self.assertEqual(self.agent_hooks_verdict()["status"], "PASS")
        cases = {
            "another tool's matcher": group("Read", ".kitchen/hooks/{}"),
            "a command that only names the path": group("Bash", "echo .kitchen/hooks/{}"),
        }
        for label, settings in cases.items():
            with self.subTest(label):
                verdict = self.agent_hooks_verdict(settings)
                self.assertEqual(verdict["status"], "FAIL", verdict)
                self.assertIn("does not run deny-no-verify", verdict["proof"])
        self.assertEqual(self.agent_hooks_verdict(group("^Bash$", '"$CLAUDE_PROJECT_DIR"/.kitchen/hooks/{}'))["status"], "PASS")

    def test_agent_hooks_fail_when_a_copy_is_not_executable(self):
        verdict = self.agent_hooks_verdict(executable=False)

        self.assertEqual(verdict["status"], "FAIL")
        self.assertIn("not executable", verdict["proof"])

    def test_without_gh_branch_protection_is_unknown_never_pass(self):
        repo = self.make_complete()

        report = self.report(repo)  # KITCHEN_GH points at a missing binary

        verdict = next(m for m in report["must_haves"] if m["id"] == "branch-protection")
        self.assertEqual((verdict["status"], verdict["proof"]), ("unknown", "gh is not installed"))
        self.assertEqual(report["missing"], 1)

    def test_unprotected_branch_fails_and_prints_a_one_way_door(self):
        repo = self.make_complete()
        unprotected = {**PROTECTED, "repos/example/shop/rules/branches/main": [{"type": "deletion"}]}
        self.gh_responses.write_text(json.dumps(unprotected))

        result = self.init_check(repo, gh=self.fake_gh)

        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL     required status on shared branch", result.stdout)
        self.assertIn("1. [one-way door: printed, never executed]", result.stdout)

    def test_gh_error_on_one_endpoint_is_unknown(self):
        repo = self.make_complete()
        partial = {k: v for k, v in PROTECTED.items() if "rules" not in k}
        self.gh_responses.write_text(json.dumps(partial))

        self.assertEqual(self.statuses(self.report(repo, gh=self.fake_gh))["branch-protection"], "unknown")

    def test_branch_flag_reads_that_branch(self):
        repo = self.make_complete()
        self.gh_responses.write_text(json.dumps({
            "repos/example/shop/branches/dev": PROTECTED["repos/example/shop/branches/main"],
            "repos/example/shop/rules/branches/dev": PROTECTED["repos/example/shop/rules/branches/main"],
        }))

        result = self.init_check(repo, "--branch", "dev", gh=self.fake_gh)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("rules/branches/dev: required_status_checks (check)", result.stdout)

    def check_contract(self, files, executable=("bin/check",)):
        repo = self.make_repo("contract", files, executable=executable)
        return next(m for m in self.report(repo)["must_haves"] if m["id"] == "check-contract")

    def test_check_contract_needs_every_tier(self):
        self.assertEqual(self.check_contract({"bin/check": BIN_CHECK})["status"], "PASS")
        partial = self.check_contract({"bin/check": BIN_CHECK.replace("verify-tree)", "tree)").replace(" verify-tree ;;", " ;;")})
        self.assertEqual(partial["status"], "FAIL")
        self.assertIn("verify-tree", partial["proof"])

    def test_check_contract_ignores_tiers_named_only_in_comments(self):
        commented = "#!/bin/sh\n# tiers: commit integrate nightly verify-tree\nexec make all\n"
        self.assertEqual(self.check_contract({"bin/check": commented})["status"], "FAIL")

    def test_a_shell_variable_named_like_a_tier_is_not_a_tier(self):
        script = '#!/bin/sh\ncommit=$(git rev-parse HEAD)\ncase "$1" in\n  integrate|nightly|verify-tree) exit 0 ;;\nesac\n'
        verdict = self.check_contract({"bin/check": script})
        self.assertEqual(verdict["status"], "FAIL")
        self.assertIn("for commit", verdict["proof"])

    def test_check_contract_needs_an_executable_script(self):
        verdict = self.check_contract({"bin/check": BIN_CHECK}, executable=())
        self.assertEqual((verdict["status"], verdict["proof"]), ("FAIL", "bin/check is not executable"))

    def test_check_contract_from_checks_toml(self):
        toml = "".join(f'[tiers.{t}]\nrun = ["true"]\n' for t in ("commit", "integrate", "nightly")) + '[tiers."verify-tree"]\nrun = ["true"]\n'
        self.assertEqual(self.check_contract({".kitchen/checks.toml": toml}, executable=())["status"], "PASS")

    def test_python_tier_choices_count_as_a_tier_table(self):
        script = '#!/usr/bin/env python3\nimport argparse\np = argparse.ArgumentParser()\np.add_argument("tier", choices=(\n    "commit", "integrate",\n    "nightly", "verify-tree"))\n'
        self.assertEqual(self.check_contract({"bin/check": script})["status"], "PASS")

    def test_agents_md_must_be_under_200_lines(self):
        files = complete_files()
        files["AGENTS.md"] = "Use verify-shop.\n" + "line\n" * 198
        self.assertEqual(self.statuses(self.report(self.make_repo("short", files)))["agents-md"], "PASS")
        files["AGENTS.md"] += "line\n"
        verdict = next(m for m in self.report(self.make_repo("long", files))["must_haves"] if m["id"] == "agents-md")
        self.assertEqual((verdict["status"], verdict["proof"]), ("FAIL", "AGENTS.md has 200 lines (must be under 200)"))

    def test_commented_secret_scanner_does_not_count(self):
        files = complete_files()
        files[".githooks/pre-commit"] = "#!/bin/sh\n# TODO: gitleaks git --staged\nexec bin/check commit\n"
        repo = self.make_repo("commented", files, executable=("bin/check", ".githooks/pre-commit"), hooks_path=".githooks")
        self.assertEqual(self.statuses(self.report(repo))["secret-scan"], "FAIL")

    def test_scanner_in_an_inactive_hook_is_reported_but_fails(self):
        files = complete_files()
        repo = self.make_repo("inactive", files, executable=("bin/check", ".githooks/pre-commit"))  # no core.hooksPath
        verdict = next(m for m in self.report(repo)["must_haves"] if m["id"] == "secret-scan")
        self.assertEqual(verdict["status"], "FAIL")
        self.assertIn("referenced at .githooks/pre-commit:3, but no pre-commit hook is active", verdict["proof"])

    def test_baseline_needs_a_gate_and_test_fixtures_are_not_baselines(self):
        files = complete_files()
        files["bin/check"] = BIN_CHECK.replace("python3 scripts/baseline.py --check quality/baseline.json", "true")
        files["tests/fixtures/baseline.json"] = "{}\n"
        repo = self.make_repo("noratchet", files, executable=("bin/check", ".githooks/pre-commit"), hooks_path=".githooks")
        verdict = next(m for m in self.report(repo)["must_haves"] if m["id"] == "baseline-ratchet")
        self.assertEqual(verdict["status"], "FAIL")
        self.assertIn("baseline quality/baseline.json is not checked", verdict["proof"])

    def test_a_copied_skill_is_not_a_link(self):
        repo = self.make_complete()
        link = repo / ".claude" / "skills" / "verify-shop"
        link.unlink()
        link.mkdir()
        (link / "SKILL.md").write_text("copy\n")
        self.assertEqual(self.statuses(self.report(repo, gh=self.fake_gh))["skills-linked"], "FAIL")

    def test_feature_map_without_a_guard_fails(self):
        files = complete_files()
        del files["tests/test_feature_map.py"]
        repo = self.make_repo("noguard", files, executable=("bin/check", ".githooks/pre-commit"), hooks_path=".githooks")
        self.assertEqual(self.statuses(self.report(repo))["verify-skill"], "FAIL")

    def test_not_a_repository_exits_64(self):
        plain = self.root / "plain"
        plain.mkdir()
        result = self.init_check(plain)
        self.assertEqual(result.returncode, 64)
        self.assertIn("is not a git repository", result.stderr)

    def test_without_a_terminal_init_asks_for_flags_and_writes_nothing(self):
        repo = self.make_repo("calc", {"pyproject.toml": "[project]\nname = 'calc'\n", "calc.py": "x = 1\n"})
        result = subprocess.run([sys.executable, str(KITCHEN), "init", str(repo)], capture_output=True, text=True,
                                env=self.env(), stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("--yes", result.stderr)
        self.assertIn("Write the missing pieces on branch kitchen/init?", result.stderr)
        branches = subprocess.run(["git", "-C", str(repo), "branch", "--list", "kitchen/init"], capture_output=True, text=True, env=self.env())
        self.assertEqual(branches.stdout.strip(), "", "init wrote a branch without an answer")
        self.assertFalse((self.home / ".config" / "kitchen" / "projects.txt").exists(), "init wrote personal config without an answer")


if __name__ == "__main__":
    unittest.main()
