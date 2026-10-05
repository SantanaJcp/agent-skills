"""The agent hooks in hooks/ against their attack corpus, through the real PreToolUse interface.

Each case is sent as the JSON payload Claude Code and Codex write on stdin; a guard allows with exit 0 and blocks
with exit 2 and an actionable message on stderr. HOME, TMPDIR and the kitchen config are throwaway; HOME is created
outside /tmp so "outside the temp dir" means something on Linux too.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"
CORPUS = json.loads((Path(__file__).resolve().parent / "corpus" / "hooks" / "cases.json").read_text(encoding="utf-8"))
GUARDS = ("deny-no-verify", "deny-shared-push", "deny-recursive-rm")
# Each block names its way out: what to do instead.
ADVICE = {"deny-no-verify": "Run it without", "deny-shared-push": "Push your own branch", "deny-recursive-rm": "trash "}
GIT_ID = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.test", "GIT_COMMITTER_NAME": "t",
          "GIT_COMMITTER_EMAIL": "t@example.test"}


def clean_env(**extra):
    return {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, **extra}


class HookFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir="/var/tmp")
        root = Path(self.tmp.name).resolve()
        self.home, self.tmpdir, self.config = root / "home", root / "tmp", root / "config"
        for folder in (self.home, self.tmpdir, self.config):
            folder.mkdir()
        (self.config / "shared-branches.txt").write_text("\n".join(CORPUS["defaults"]["shared_branches_file"]) + "\n")
        self.repos = {}

    def tearDown(self):
        self.tmp.cleanup()

    def repo(self, branch, upstream=None, push_default=None, push_config=None):
        key = (branch, upstream, push_default, push_config)
        if key not in self.repos:
            path = self.home / "projects" / f"p{len(self.repos)}"
            env = clean_env(**GIT_ID)
            for args in (["init", "-q", "-b", branch, str(path)], ["-C", str(path), "commit", "-q", "--allow-empty", "-m", "init"]):
                subprocess.run(["git", *args], check=True, env=env, capture_output=True)
            config = {"remote.origin.url": "https://example.test/r.git"}
            if upstream:
                config.update({f"branch.{branch}.remote": "origin", f"branch.{branch}.merge": f"refs/heads/{upstream}"})
            if push_default:
                config["push.default"] = push_default
            if push_config:
                config["remote.origin.push"] = push_config
            for name, value in config.items():
                subprocess.run(["git", "-C", str(path), "config", name, value], check=True, env=env)
            self.repos[key] = path
        return self.repos[key]

    def env(self):
        return clean_env(HOME=str(self.home), TMPDIR=str(self.tmpdir), KITCHEN_CONFIG=str(self.config))

    def run_guard(self, guard, payload, python=None):
        command = [python, str(HOOKS / guard)] if python else [str(HOOKS / guard)]
        data = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(command, input=data, capture_output=True, text=True, env=self.env(), timeout=30)

    def payload(self, command, cwd):
        return {"session_id": "s", "transcript_path": str(self.home / "t.jsonl"), "cwd": str(cwd), "permission_mode": "default",
                "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command, "description": "x"},
                "tool_use_id": "toolu_1"}

    def case_cwd(self, case):
        defaults = CORPUS["defaults"]
        if case.get("cwd", defaults["cwd"]) == "tmp":
            return self.tmpdir
        return self.repo(case.get("branch", defaults["branch"]), case.get("upstream"), case.get("push_default"), case.get("push_config"))


class HookCorpusTests(HookFixture):
    def test_every_guard_has_positive_negative_and_bypass_cases(self):
        for guard in GUARDS:
            kinds = {case["kind"] for case in CORPUS["cases"] if case["guard"] == guard}
            self.assertLessEqual({"positive", "negative", "bypass"}, kinds, guard)
            self.assertTrue((HOOKS / guard).is_file() and os.access(HOOKS / guard, os.X_OK), guard)
        for case in CORPUS["cases"]:
            expected = {"positive": "deny", "bypass": "deny", "negative": "allow", "known-limit": "allow"}[case["kind"]]
            self.assertEqual(case["expect"], expected, case["id"])
            if case["kind"] == "known-limit":
                self.assertTrue(case.get("limit"), f"{case['id']}: a known limit says why the guard misses it")

    def test_corpus(self):
        for case in CORPUS["cases"]:
            result = self.run_guard(case["guard"], self.payload(case["command"], self.case_cwd(case)))
            with self.subTest(case["id"], guard=case["guard"], kind=case["kind"]):
                if case["expect"] == "deny":
                    self.assertEqual(result.returncode, 2, f"{case['command']!r} was allowed")
                    self.assertIn(f"Blocked by the kitchen hook {case['guard']}", result.stderr)
                    if "unterminated" not in case["id"]:
                        self.assertIn(ADVICE[case["guard"]], result.stderr)
                else:
                    self.assertEqual((result.returncode, result.stderr), (0, ""), f"{case['command']!r} was blocked")


class HookPayloadTests(HookFixture):
    def test_codex_payload_with_an_argv_command_is_checked(self):
        payload = {"session_id": "s", "turn_id": "t", "model": "gpt", "cwd": str(self.home), "hook_event_name": "PreToolUse",
                   "permission_mode": "default", "tool_name": "Bash", "tool_input": {"command": ["bash", "-lc", "git push origin dev"]}}

        result = self.run_guard("deny-shared-push", payload)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("shared branch", result.stderr)

    def test_a_tool_that_is_not_a_shell_passes(self):
        payload = {"cwd": str(self.home), "hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"patch": "x"}}

        for guard in GUARDS:
            with self.subTest(guard):
                self.assertEqual(self.run_guard(guard, payload).returncode, 0)

    def test_unreadable_input_blocks_instead_of_passing(self):
        bad = {"not json": "{oops", "bash without command": json.dumps({"tool_name": "Bash", "tool_input": {}})}
        for guard in GUARDS:
            for label, data in bad.items():
                with self.subTest(guard, input=label):
                    result = self.run_guard(guard, data)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("cannot read the hook input", result.stderr)

    @unittest.skipUnless(Path("/usr/bin/python3").exists(), "no system python3")
    def test_guards_run_on_the_system_python(self):
        """The hooks run on whatever python3 the agent finds; macOS ships 3.9 at /usr/bin/python3."""
        cases = {"deny-no-verify": "git commit -n -m x", "deny-shared-push": "git push origin dev", "deny-recursive-rm": "rm -rf ~"}
        for guard, command in cases.items():
            with self.subTest(guard):
                result = self.run_guard(guard, self.payload(command, self.home), python="/usr/bin/python3")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(ADVICE[guard], result.stderr)


if __name__ == "__main__":
    unittest.main()
