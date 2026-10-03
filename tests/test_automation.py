import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parent.parent / "automation"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


class AutomationFixture(unittest.TestCase):
    """A local origin repo, fake external tools, and throwaway config and state."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.origin, self.bin, self.config, self.state = root / "origin", root / "fakebin", root / "config", root / "state"
        self.calls = root / "calls.log"
        for folder in (self.origin, self.bin, self.config / "automation"):
            folder.mkdir(parents=True)
        env = {**os.environ, **GIT_ENV}
        for args in (["init", "-q", "-b", "dev"], ["commit", "-q", "--allow-empty", "-m", "init"]):
            subprocess.run(["git", "-C", str(self.origin), *args], check=True, env=env)
        self.fake("gh", 'echo "gh $*" >> "$CALLS"; case "$1 $2" in "pr list") echo "${OPEN_PRS:-0}";; esac')
        self.fake("claude", 'echo "claude" >> "$CALLS"; exit "${CLAUDE_EXIT:-0}"')

    def tearDown(self):
        self.tmp.cleanup()

    def fake(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/usr/bin/env bash\n{body}\n")
        path.chmod(0o755)

    def configure(self, steps, cleanup="true", metrics="", needs_docker=0, project="shop"):
        step_lines = "\n".join(f'  "{s}"' for s in steps)
        (self.config / "automation" / f"{project}.env").write_text(textwrap.dedent(f"""\
            REPO_URL="{self.origin}"
            GH_REPO="owner/shop"
            BRANCH="dev"
            EXTRA_PATH="{self.bin}"
            NEEDS_DOCKER={needs_docker}
            GUARD_LABEL="nightly-guard"
            GARDENER_LABEL="gardener"
            CLEANUP_CMD="{cleanup}"
            METRICS_CMD="{metrics}"
            """) + f"GUARD_STEPS=(\n{step_lines}\n)\n")

    def run_job(self, job, *args, **env):
        full_env = {**os.environ, **GIT_ENV, "KITCHEN_CONFIG": str(self.config), "KITCHEN_STATE": str(self.state),
                    "KITCHEN_REAL_GH": str(self.bin / "gh"), "CALLS": str(self.calls), "DOCKER_WAIT_TRIES": "1", "DOCKER_WAIT_SECONDS": "0", **env}
        return subprocess.run(["bash", str(AUTOMATION / "bin" / job), *args], env=full_env, capture_output=True, text=True)

    def nightly(self, project="shop"):
        return [json.loads(line) for line in (self.state / "nightly" / f"{project}.jsonl").read_text().splitlines()]

    def calls_log(self):
        return self.calls.read_text() if self.calls.exists() else ""


class NightlyGuardTests(AutomationFixture):
    def test_red_run_stops_at_the_first_failure_reports_it_and_records_it(self):
        marker = Path(self.tmp.name) / "never-ran"
        self.configure(["ok|true", "bad|false", f"after|touch {marker}"])

        result = self.run_job("nightly-guard", "shop")

        run = self.nightly()[-1]
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual((run["status"], run["failed_step"]), ("red", "bad"))
        self.assertFalse(marker.exists())
        self.assertIn("gh issue create", self.calls_log())

    def test_green_run_records_metrics_and_cleanup(self):
        self.configure(["ok|true"], metrics="echo '{\\\"tests\\\": 3}'")

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        run = self.nightly()[-1]
        history = (self.state / "automation" / "shop" / "history" / "history.jsonl").read_text()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((run["status"], run["cleanup"], run["metrics"]), ("green", "ok", "ok"))
        self.assertEqual(json.loads(history)["metrics"], {"tests": 3})

    def test_failed_cleanup_and_metrics_are_recorded_not_hidden(self):
        self.configure(["ok|true"], cleanup="false", metrics="exit 3")

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        run = self.nightly()[-1]
        self.assertEqual((run["cleanup"], run["metrics"]), ("failed", "failed"))
        self.assertIn("cleanup FAILED", result.stdout)
        self.assertIn("metrics FAILED", result.stdout)

    def test_missing_docker_fails_the_run(self):
        self.configure(["ok|true"], needs_docker=1)
        self.fake("docker", "exit 1")
        self.fake("open", "exit 1")

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        run = self.nightly()[-1]
        self.assertEqual(result.returncode, 1)
        self.assertEqual((run["status"], run["failed_step"]), ("red", "docker"))


    def test_trial_run_is_neither_recorded_nor_reported(self):
        self.configure(["build|true", "tests|true"], metrics="echo '{}'")

        result = self.run_job("nightly-guard", "shop", GUARD_ONLY="build")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.state / "nightly" / "shop.jsonl").exists())
        self.assertFalse((self.state / "automation" / "shop" / "history" / "history.jsonl").exists())
        self.assertNotIn("gh issue", self.calls_log())


class GardenerTests(AutomationFixture):
    def test_claude_failure_is_the_job_status_and_cleanup_still_runs(self):
        cleaned = Path(self.tmp.name) / "cleaned"
        self.configure([], cleanup=f"touch {cleaned}")

        result = self.run_job("weekly-gardener", "shop", CLAUDE_EXIT="3")

        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertTrue(cleaned.exists())
        self.assertIn("gardener end: status=3", result.stdout)

    def test_skips_while_a_gardener_pr_is_open(self):
        self.configure([])

        result = self.run_job("weekly-gardener", "shop", OPEN_PRS="1")

        self.assertEqual(result.returncode, 0)
        self.assertIn("gardener skipped", result.stdout)
        self.assertNotIn("claude", self.calls_log())

    def test_missing_docker_stops_the_gardener(self):
        self.configure([], needs_docker=1)
        self.fake("docker", "exit 1")
        self.fake("open", "exit 1")

        result = self.run_job("weekly-gardener", "shop")

        self.assertEqual(result.returncode, 1)
        self.assertNotIn("claude", self.calls_log())


class ShimTests(AutomationFixture):
    def test_gh_shim_blocks_merging_and_passes_everything_else(self):
        env = {**os.environ, "KITCHEN_REAL_GH": str(self.bin / "gh"), "CALLS": str(self.calls)}
        shim = str(AUTOMATION / "shims" / "gh")

        merge = subprocess.run([shim, "pr", "merge", "7"], env=env, capture_output=True, text=True)
        view = subprocess.run([shim, "pr", "view", "7"], env=env, capture_output=True, text=True)

        self.assertEqual(merge.returncode, 1)
        self.assertIn("blocked", merge.stderr)
        self.assertEqual(view.returncode, 0)
        self.assertEqual(self.calls_log().strip(), "gh pr view 7")


if __name__ == "__main__":
    unittest.main()
