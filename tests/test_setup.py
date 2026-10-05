"""install and doctor for the agent hooks, doctor's environment checks, and the path-scoped `check --fast`."""
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from tests.test_kitchen import KITCHEN, KitchenFixture

ROOT = KITCHEN.parent.parent
GUARDS = ["deny-no-verify", "deny-recursive-rm", "deny-shared-push"]


def environment():
    sys.path.insert(0, str(ROOT / "lib"))
    try:
        from kitchen import environment as module
    finally:
        sys.path.pop(0)
    return module


class HooksFixture(KitchenFixture):
    def setUp(self):
        super().setUp()
        shutil.copytree(ROOT / "hooks", self.repo / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
        self.claude = self.home / ".claude" / "settings.json"
        self.codex = self.home / ".codex" / "hooks.json"

    def commands(self, path, matcher):
        data = json.loads(path.read_text())
        return [h["command"] for g in data["hooks"]["PreToolUse"] if g.get("matcher") == matcher for h in g["hooks"]]

    def kitchen_commands(self):
        return [str(self.repo.resolve() / "hooks" / name) for name in GUARDS]


class HookInstallTests(HooksFixture):
    def test_install_adds_the_guards_to_claude_and_codex(self):
        result = self.kitchen("install")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.commands(self.claude, "Bash"), self.kitchen_commands())
        self.assertEqual(self.commands(self.codex, "^Bash$"), self.kitchen_commands())

    def test_install_keeps_the_users_settings_and_hooks(self):
        mine = {"type": "command", "command": "/opt/my-hook.sh"}
        settings = {"model": "opus", "permissions": {"allow": ["Bash(ls)"]},
                    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [mine]}],
                              "PostToolUse": [{"matcher": "Edit", "hooks": [mine]}]}}
        self.claude.parent.mkdir(parents=True)
        self.claude.write_text(json.dumps(settings))

        result = self.kitchen("install")

        data = json.loads(self.claude.read_text())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((data["model"], data["permissions"], data["hooks"]["PostToolUse"]),
                         ("opus", settings["permissions"], settings["hooks"]["PostToolUse"]))
        self.assertEqual(data["hooks"]["PreToolUse"][0], {"matcher": "Bash", "hooks": [mine]})
        self.assertEqual(self.commands(self.claude, "Bash"), ["/opt/my-hook.sh"] + self.kitchen_commands())

    def test_install_is_idempotent_for_hooks(self):
        self.kitchen("install")
        before = (self.claude.read_bytes(), self.codex.read_bytes())

        second = self.kitchen("install")

        self.assertEqual((self.claude.read_bytes(), self.codex.read_bytes()), before)
        self.assertNotIn("hooks      ", second.stdout)

    def test_install_drops_the_handler_of_a_removed_guard(self):
        self.kitchen("install")
        (self.repo / "hooks" / "deny-shared-push").unlink()

        self.kitchen("install")

        self.assertEqual(self.commands(self.codex, "^Bash$"), self.kitchen_commands()[:2])

    def test_install_refuses_a_hook_file_it_cannot_merge(self):
        self.add_skill("alpha")
        self.codex.parent.mkdir(parents=True)
        self.codex.write_text("{ not json")

        result = self.kitchen("install")

        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{self.codex}: not valid JSON", result.stdout)
        self.assertEqual(self.codex.read_text(), "{ not json")
        self.assertFalse((self.home / ".claude" / "skills" / "alpha").exists())
        self.assertFalse(self.claude.exists())

    def test_install_backup_moves_an_unmergeable_hook_file_aside(self):
        self.codex.parent.mkdir(parents=True)
        self.codex.write_text("{ not json")

        result = self.kitchen("install", "--backup")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual([b.read_text() for b in (self.home / ".kitchen-backups").rglob("hooks.json")], ["{ not json"])
        self.assertEqual(self.commands(self.codex, "^Bash$"), self.kitchen_commands())


class HookDoctorTests(HooksFixture):
    def test_doctor_fails_until_the_hooks_are_installed(self):
        before = self.kitchen("doctor")
        self.kitchen("install")
        after = self.kitchen("doctor")

        self.assertEqual(before.returncode, 1)
        self.assertIn("FAIL  Claude Code hooks not installed (deny-no-verify, deny-recursive-rm, deny-shared-push)", before.stdout)
        self.assertIn("FAIL  Codex hooks not installed", before.stdout)
        self.assertEqual(after.returncode, 0, after.stdout)
        self.assertIn("INFO  Claude Code hooks installed", after.stdout)
        self.assertIn("INFO  Codex runs a new or changed hook only after you trust it", after.stdout)

    def test_doctor_fails_when_hooks_are_disabled(self):
        self.kitchen("install")
        data = json.loads(self.claude.read_text())
        self.claude.write_text(json.dumps({**data, "disableAllHooks": True}))
        (self.home / ".codex" / "config.toml").write_text("[features]\nhooks = false\n")

        result = self.kitchen("doctor")

        self.assertEqual(result.returncode, 1)
        self.assertIn("disableAllHooks is true", result.stdout)
        self.assertIn("Codex hooks are disabled: [features] hooks = false", result.stdout)

    def test_doctor_fails_when_a_guard_does_not_block(self):
        self.kitchen("install")
        (self.repo / "hooks" / "deny-shared-push").write_text("#!/bin/sh\nexit 0\n")

        result = self.kitchen("doctor")

        self.assertEqual(result.returncode, 1)
        self.assertIn("hook deny-shared-push did not block its probe", result.stdout)


class EnvironmentDoctorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def fake(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/bin/sh\n{body}\n")
        path.chmod(0o755)

    def test_missing_agent_clis_and_srt_are_reported(self):
        config = self.root / "config"
        (config / "automation").mkdir(parents=True)
        (config / "automation" / "shop.env").write_text("BRANCH=dev\n")

        with mock.patch.dict(os.environ, {"PATH": str(self.bin)}):
            report = environment().tools(self.root / "repo", config)

        lines = [f"{level}  {message}" for level, message in report]
        self.assertIn("WARN  `claude` is not on PATH: Codex sessions run second-opinion reviewers with it", lines)
        self.assertIn("WARN  `codex` is not on PATH: Claude Code sessions run second-opinion reviewers with it", lines)
        self.assertIn("WARN  srt is not installed, and the automation needs it: npm ci --ignore-scripts --prefix automation "
                      "(automation configured for: shop)", lines)

    def test_a_launchagent_present_but_not_loaded_is_flagged(self):
        agents = self.root / "Library" / "LaunchAgents"
        agents.mkdir(parents=True)
        for label in ("com.kitchen.shop.nightly-guard", "com.kitchen.shop.weekly-gardener"):
            (agents / f"{label}.plist").write_bytes(plistlib.dumps({"Label": label}))
        self.fake("launchctl", 'printf "PID\\tStatus\\tLabel\\n-\\t0\\tcom.kitchen.shop.nightly-guard\\n-\\t0\\tcom.apple.x\\n"')

        with mock.patch.dict(os.environ, {"PATH": str(self.bin)}):
            report = environment().schedules("Darwin", self.root)

        self.assertIn(("INFO", "schedule com.kitchen.shop.nightly-guard loaded"), report)
        warnings = [m for level, m in report if level == "WARN"]
        self.assertEqual(len(warnings), 1, report)
        self.assertIn("com.kitchen.shop.weekly-gardener.plist is present but not loaded by launchctl", warnings[0])

    def test_a_plist_without_a_label_is_reported_not_guessed_from_its_name(self):
        agents = self.root / "Library" / "LaunchAgents"
        agents.mkdir(parents=True)
        (agents / "com.kitchen.shop.nightly-guard.plist").write_bytes(plistlib.dumps({"ProgramArguments": ["true"]}))
        self.fake("launchctl", 'printf "PID\\tStatus\\tLabel\\n-\\t0\\tcom.kitchen.shop.nightly-guard\\n"')

        with mock.patch.dict(os.environ, {"PATH": str(self.bin)}):
            report = environment().schedules("Darwin", self.root)

        self.assertEqual(report, [("WARN", f"{agents / 'com.kitchen.shop.nightly-guard.plist'} has no Label, so launchd cannot load it")])

    def test_a_systemd_timer_present_but_inactive_is_flagged(self):
        units = self.root / ".config" / "systemd" / "user"
        units.mkdir(parents=True)
        for name in ("kitchen-shop-nightly-guard.timer", "kitchen-shop-weekly-gardener.timer"):
            (units / name).write_text("[Timer]\n")
        self.fake("systemctl", '[ "$3" = kitchen-shop-nightly-guard.timer ] && { echo active; exit 0; }; echo inactive; exit 3')

        with mock.patch.dict(os.environ, {"PATH": str(self.bin), "XDG_CONFIG_HOME": ""}):
            report = environment().schedules("Linux", self.root)

        self.assertIn(("INFO", "timer kitchen-shop-nightly-guard.timer active"), report)
        warnings = [m for level, m in report if level == "WARN"]
        self.assertEqual(len(warnings), 1, report)
        self.assertIn("kitchen-shop-weekly-gardener.timer is present but inactive", warnings[0])

    def test_unreadable_launchctl_is_reported_not_skipped(self):
        agents = self.root / "Library" / "LaunchAgents"
        agents.mkdir(parents=True)
        (agents / "com.kitchen.retro.plist").write_bytes(plistlib.dumps({"Label": "com.kitchen.retro"}))
        self.fake("launchctl", "exit 1")

        with mock.patch.dict(os.environ, {"PATH": str(self.bin)}):
            report = environment().schedules("Darwin", self.root)

        self.assertEqual(report, [("WARN", "cannot read `launchctl list`, so 1 kitchen schedules were not checked")])


class FastCheckTests(KitchenFixture):
    """`check --fast` runs the test modules the staged paths need; plain `check` runs all of them."""

    MODULE = textwrap.dedent("""\
        import os
        import unittest
        from pathlib import Path


        class Ran(unittest.TestCase):
            def test_mark(self):
                Path(os.environ["MARKS"], "{name}").touch()
        """)

    def setUp(self):
        super().setUp()
        self.marks = self.home / "marks"
        self.marks.mkdir()
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "__init__.py").write_text("")
        for name in ("test_automation", "test_kitchen"):
            (self.repo / "tests" / f"{name}.py").write_text(self.MODULE.format(name=name))
        srt = self.repo / "automation" / "node_modules" / ".bin" / "srt"
        srt.parent.mkdir(parents=True)
        srt.write_text("#!/bin/sh\necho 0.0.78\n")
        srt.chmod(0o755)

    def stage(self, *paths):
        for path in paths:
            (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / path).write_text("change\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "--", *paths], check=True)

    def check(self, *args):
        result = self.kitchen("check", *args, env_extra={"MARKS": str(self.marks)})
        return result, sorted(p.name for p in self.marks.iterdir())

    def test_a_docs_only_commit_runs_no_tests(self):
        self.stage("README.md", "global/AGENTS.md")

        result, ran = self.check("--fast")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(ran, [])
        self.assertIn("SKIP  tests/test_automation.py: no staged path under automation/, lib/ or tests/test_automation.py", result.stdout)

    def test_a_docs_only_commit_still_runs_the_principles_suite(self):
        (self.repo / "tests" / "test_principles.py").write_text(self.MODULE.format(name="test_principles"))
        self.stage("PRINCIPLES.md")

        result, ran = self.check("--fast")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(ran, ["test_principles"])

    def test_a_cli_change_runs_the_other_modules_but_not_automation(self):
        self.stage("bin/helper.py")

        result, ran = self.check("--fast")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(ran, ["test_kitchen"])

    def test_automation_lib_and_its_tests_trigger_the_automation_suite(self):
        for path in ("automation/bin/job", "lib/kitchen/x.py", "tests/test_automation.py"):
            with self.subTest(path):
                for mark in self.marks.iterdir():
                    mark.unlink()
                subprocess.run(["git", "-C", str(self.repo), "reset", "-q"], check=True)
                if path == "tests/test_automation.py":
                    subprocess.run(["git", "-C", str(self.repo), "add", "--", path], check=True)
                else:
                    self.stage(path)

                result, ran = self.check("--fast")

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("test_automation", ran)

    def test_plain_check_runs_every_module_whatever_is_staged(self):
        self.stage("README.md")

        result, ran = self.check()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(ran, ["test_automation", "test_kitchen"])

    def test_missing_srt_is_one_actionable_line_not_test_failures(self):
        shutil.rmtree(self.repo / "automation")

        result, ran = self.check()

        self.assertEqual(result.returncode, 1)
        self.assertEqual([line for line in result.stdout.splitlines() if line.startswith("FAIL")],
                         ["FAIL  srt is not installed, and the automation needs it: npm ci --ignore-scripts --prefix automation"])
        self.assertEqual(ran, [])
        self.assertEqual(result.stderr, "")


class HelpTests(KitchenFixture):
    def test_help_leads_with_examples(self):
        result = self.kitchen("--help")

        self.assertIn("examples:\n  kitchen install", result.stdout)
        self.assertIn("kitchen check --fast", result.stdout)

    def test_install_points_to_doctor_next(self):
        self.assertIn("next:      kitchen doctor", self.kitchen("install").stdout)
