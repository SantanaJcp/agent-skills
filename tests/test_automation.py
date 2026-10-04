import datetime
import fcntl
import json
import os
import signal
import subprocess
import tempfile
import time
import textwrap
import unittest
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parent.parent / "automation"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def clean_env(**extra):
    """os.environ without GIT_* (a git hook exports GIT_DIR and GIT_INDEX_FILE), plus a fixed identity."""
    return {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, **GIT_ENV, **extra}


class AutomationFixture(unittest.TestCase):
    """A local origin repo, fake external tools, and throwaway config and state."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.origin, self.bin, self.config, self.state = root / "origin", root / "fakebin", root / "config", root / "state"
        self.calls = root / "calls.log"
        for folder in (self.origin, self.bin, self.config / "automation"):
            folder.mkdir(parents=True)
        env = clean_env()
        for args in (["init", "-q", "-b", "dev"], ["commit", "-q", "--allow-empty", "-m", "init"]):
            subprocess.run(["git", "-C", str(self.origin), *args], check=True, env=env)
        self.fake("gh", 'echo "gh $*" >> "$CALLS"; [ "${GH_FAIL:-0}" = 1 ] && exit 1\n'
                        'case "$1 $2" in "pr list") echo "${OPEN_PRS:-0}";; "pr create") echo "https://example.test/pull/1";; esac')
        self.fake("claude", 'echo "claude" >> "$CALLS"; exit "${CLAUDE_EXIT:-0}"')

    def tearDown(self):
        self.tmp.cleanup()

    def fake(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/usr/bin/env bash\n{body}\n")
        path.chmod(0o755)

    def configure(self, steps, cleanup="true", metrics="", needs_docker=0, project="shop", extra=""):
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
            """) + extra + f"\nGUARD_STEPS=(\n{step_lines}\n)\n")

    def run_job(self, job, *args, **env):
        full_env = {**clean_env(), "KITCHEN_CONFIG": str(self.config), "KITCHEN_STATE": str(self.state),
                    "KITCHEN_REAL_GH": str(self.bin / "gh"), "CALLS": str(self.calls), "DOCKER_WAIT_TRIES": "1", "DOCKER_WAIT_SECONDS": "0", **env}
        return subprocess.run(["bash", str(AUTOMATION / "bin" / job), *args], env=full_env, capture_output=True, text=True)

    def nightly(self, project="shop"):
        return [json.loads(line) for line in (self.state / "nightly" / f"{project}.jsonl").read_text().splitlines()]

    def calls_log(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                              env=clean_env()).stdout.strip()

    def origin_branches(self):
        return self.git(self.origin, "for-each-ref", "--format=%(refname:short)", "refs/heads/").splitlines()

    def commit_to_origin(self, files):
        for name, (text, mode) in files.items():
            path = self.origin / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            path.chmod(mode)
        self.git(self.origin, "add", "-A")
        self.git(self.origin, "commit", "-q", "-m", "files")


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

    def test_green_verdict_keeps_cleanup_and_metrics_failures_as_warnings(self):
        self.configure(["ok|true"], cleanup="false", metrics="exit 3")

        self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        run = self.nightly()[-1]
        self.assertEqual(run["status"], "green")
        self.assertEqual(run["warnings"], ["cleanup failed", "metrics failed"])

    def test_failing_issue_report_is_a_warning_and_the_run_still_cleans_and_records(self):
        cleaned = Path(self.tmp.name) / "cleaned"
        self.configure(["bad|false"], cleanup=f"touch {cleaned}")

        result = self.run_job("nightly-guard", "shop", GH_FAIL="1")

        runs = self.nightly()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(len(runs), 1)
        self.assertEqual((runs[0]["status"], runs[0]["failed_step"]), ("red", "bad"))
        self.assertIn("issue report failed", runs[0]["warnings"])
        self.assertTrue(cleaned.exists())

    def test_failing_green_report_is_a_warning(self):
        self.configure(["ok|true"])

        result = self.run_job("nightly-guard", "shop", GH_FAIL="1")

        run = self.nightly()[-1]
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((run["status"], run["warnings"]), ("green", ["issue report failed"]))

    def test_invalid_metrics_json_is_recorded_not_fatal(self):
        self.configure(["ok|true"], metrics="echo not-json")

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        run = self.nightly()[-1]
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((run["status"], run["metrics"], run["warnings"]), ("green", "failed", ["metrics failed"]))

    def test_interrupted_run_is_cleaned_and_recorded_as_incomplete(self):
        cleaned = Path(self.tmp.name) / "cleaned"
        self.configure(["ok|true", "slow|kill -TERM \\$PPID", "after|true"], cleanup=f"touch {cleaned}")

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        runs = self.nightly()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(runs), 1)
        self.assertEqual((runs[0]["status"], runs[0]["failed_step"]), ("incomplete", "slow"))
        self.assertTrue(cleaned.exists())

    def test_record_carries_the_full_sha(self):
        self.configure(["ok|true"])

        self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        self.assertEqual(self.nightly()[-1]["sha"], self.git(self.origin, "rev-parse", "HEAD"))

    def test_issue_body_is_redacted(self):
        token = "ghp_" + "a" * 30
        self.configure([f"leak|echo password=hunter2hunter2; echo {token}; exit 1"])

        self.run_job("nightly-guard", "shop")

        calls = self.calls_log()
        self.assertIn("gh issue create", calls)
        self.assertIn("[REDACTED]", calls)
        self.assertNotIn("hunter2hunter2", calls)
        self.assertNotIn(token, calls)

    def test_project_hooks_keep_working_next_to_the_push_guard(self):
        marks = Path(self.tmp.name)
        self.commit_to_origin({
            "scripts/hooks/pre-commit": (f"#!/bin/sh\ntouch {marks}/pre-commit-ran\n", 0o755),
            "scripts/hooks/pre-push": (f"#!/bin/sh\ncat > {marks}/pre-push-input\n", 0o755),
        })
        self.configure(["hooks|git commit -q --allow-empty -m x && git push -q origin HEAD:refs/heads/kitchen-ok"
                        " && ! git push -q origin HEAD:refs/heads/main"], extra='HOOKS_PATH="scripts/hooks"')

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((marks / "pre-commit-ran").exists())
        self.assertIn("refs/heads/kitchen-ok", (marks / "pre-push-input").read_text())
        self.assertIn("kitchen-ok", self.origin_branches())
        self.assertNotIn("main", self.origin_branches())

    def test_hooks_path_set_by_the_project_is_kept_on_the_next_sync(self):
        marks = Path(self.tmp.name)
        self.commit_to_origin({"scripts/hooks/pre-commit": (f"#!/bin/sh\ntouch {marks}/pre-commit-ran\n", 0o755)})
        self.configure(["setup|git config core.hooksPath scripts/hooks"])
        self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")
        self.configure(["commit|git commit -q --allow-empty -m x"])

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((marks / "pre-commit-ran").exists())

    def test_inherited_git_dir_never_redirects_the_job(self):
        decoy = Path(self.tmp.name) / "decoy"
        self.git(self.origin, "clone", "-q", str(self.origin), str(decoy))
        before = self.git(decoy, "rev-parse", "HEAD")
        self.configure(["commit|git commit -q --allow-empty -m from-the-guard"])

        result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1",
                              GIT_DIR=str(decoy / ".git"), GIT_INDEX_FILE=str(decoy / ".git" / "index"))

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.git(decoy, "rev-parse", "HEAD"), before)
        self.assertEqual(self.git(decoy, "config", "--get", "core.bare"), "false")

    def test_busy_project_lock_skips_the_run_and_records_it(self):
        marker = Path(self.tmp.name) / "ran"
        self.configure([f"step|touch {marker}"])
        lock = self.state / "automation" / "shop" / "job.lock"
        lock.parent.mkdir(parents=True)

        with open(lock, "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1", LOCK_WAIT_SECONDS="1", LOCK_POLL_SECONDS="0.1")

        self.assertEqual(result.returncode, 75, result.stdout)
        self.assertEqual(self.nightly()[-1]["status"], "skipped: busy")
        self.assertFalse(marker.exists())

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


    def test_lock_of_a_killed_job_is_released(self):
        started = Path(self.tmp.name) / "started"
        self.configure([f"slow|touch {started}; sleep 30"])
        env = {**clean_env(), "KITCHEN_CONFIG": str(self.config), "KITCHEN_STATE": str(self.state),
               "KITCHEN_REAL_GH": str(self.bin / "gh"), "CALLS": str(self.calls), "GUARD_NO_REPORT": "1"}
        first = subprocess.Popen(["bash", str(AUTOMATION / "bin" / "nightly-guard"), "shop"], env=env, start_new_session=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                if started.exists():
                    break
                time.sleep(0.1)
            self.assertTrue(started.exists())
            first.kill()
            first.wait()
            self.configure(["ok|true"])

            result = self.run_job("nightly-guard", "shop", GUARD_NO_REPORT="1", LOCK_WAIT_SECONDS="10", LOCK_POLL_SECONDS="0.1")
        finally:
            os.killpg(first.pid, signal.SIGKILL)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.nightly()[-1]["status"], "green")

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


    def test_busy_project_lock_skips_the_gardener(self):
        self.configure([])
        lock = self.state / "automation" / "shop" / "job.lock"
        lock.parent.mkdir(parents=True)

        with open(lock, "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            result = self.run_job("weekly-gardener", "shop", LOCK_WAIT_SECONDS="1", LOCK_POLL_SECONDS="0.1")

        self.assertEqual(result.returncode, 75, result.stdout)
        self.assertIn("gardener skipped: busy", result.stdout)
        self.assertNotIn("claude", self.calls_log())


class GardenerPublicationTests(AutomationFixture):
    """The agent only commits locally; the job publishes what passes its checks."""

    def agent(self, script):
        self.fake("claude", 'echo "claude" >> "$CALLS"\n' + script)

    def commit_script(self, branch='"${GARDENER_BRANCH_PREFIX}tidy"', path="notes.txt", lines=3):
        return textwrap.dedent(f"""\
            git checkout -q -b {branch}
            mkdir -p "$(dirname {path})"
            seq 1 {lines} > {path}
            git add {path}
            git commit -q -m "Tidy notes"
            printf '# Tidy the notes\\n\\nWhy and how verified.\\n' > "$GARDENER_SUMMARY_FILE"
            """)

    def test_agent_runs_without_any_way_to_publish(self):
        probe = Path(self.tmp.name) / "probe"
        self.configure([])
        self.agent(textwrap.dedent(f"""\
            gh api repos/owner/shop/pulls/1/merge -X PUT; echo "gh=$?" >> {probe}
            echo "token=${{GH_TOKEN:-unset}} ${{GITHUB_TOKEN:-unset}} real=${{KITCHEN_REAL_GH:-unset}}" >> {probe}
            echo "prompt=$GIT_TERMINAL_PROMPT helper=[$(git config --get credential.helper)]" >> {probe}
            "$GIT_SSH_COMMAND" git@github.com true; echo "ssh=$?" >> {probe}
            git push -q origin HEAD:refs/heads/sneaky; echo "push=$?" >> {probe}
            """))

        result = self.run_job("weekly-gardener", "shop", GH_TOKEN="tok", GITHUB_TOKEN="tok")

        lines = probe.read_text()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("gh=1", lines)
        self.assertNotIn("gh api", self.calls_log())
        self.assertIn("token=unset unset real=unset", lines)
        self.assertIn("prompt=0 helper=[]", lines)
        self.assertIn("ssh=1", lines)
        self.assertNotIn("push=0", lines)
        self.assertNotIn("sneaky", self.origin_branches())

    def test_job_publishes_the_agents_branch_with_the_label_and_summary(self):
        branch = f"gardener/{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d}-tidy"
        self.configure([])
        self.agent(self.commit_script())

        result = self.run_job("weekly-gardener", "shop")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(branch, self.origin_branches())
        pr_create = [line for line in self.calls_log().splitlines() if line.startswith("gh pr create")]
        self.assertEqual(len(pr_create), 1)
        self.assertIn(f"--head {branch}", pr_create[0])
        self.assertIn("--label gardener", pr_create[0])
        self.assertIn("--title Tidy the notes", pr_create[0])
        self.assertIn("GARDENER-RESULT: https://example.test/pull/1", result.stdout)

    def assert_refused(self, result, reason):
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(f"GARDENER-RESULT: refused - ", result.stdout)
        self.assertIn(reason, result.stdout)
        self.assertEqual([b for b in self.origin_branches() if b.startswith("gardener/")], [])
        self.assertNotIn("gh pr create", self.calls_log())

    def test_oversized_diff_is_not_published(self):
        self.configure([], extra="GARDENER_MAX_CHANGED_LINES=5")
        self.agent(self.commit_script(lines=10))

        self.assert_refused(self.run_job("weekly-gardener", "shop"), "the bound is 5")

    def test_protected_path_is_not_published(self):
        self.configure([])
        self.agent(self.commit_script(path=".github/workflows/ci.yml"))

        self.assert_refused(self.run_job("weekly-gardener", "shop"), "protected path .github/workflows/ci.yml")

    def test_branch_with_another_name_is_not_published(self):
        self.configure([])
        self.agent(self.commit_script(branch="gardener/misc"))

        self.assert_refused(self.run_job("weekly-gardener", "shop"), "is not named gardener/")

    def test_branch_without_a_summary_is_not_published(self):
        self.configure([])
        self.agent(self.commit_script() + 'rm "$GARDENER_SUMMARY_FILE"\n')

        self.assert_refused(self.run_job("weekly-gardener", "shop"), "no PR summary")


class ShimTests(AutomationFixture):
    def test_gh_shim_blocks_merging_and_passes_everything_else(self):
        env = {**clean_env(), "KITCHEN_REAL_GH": str(self.bin / "gh"), "CALLS": str(self.calls)}
        shim = str(AUTOMATION / "shims" / "gh")

        merge = subprocess.run([shim, "pr", "merge", "7"], env=env, capture_output=True, text=True)
        view = subprocess.run([shim, "pr", "view", "7"], env=env, capture_output=True, text=True)

        self.assertEqual(merge.returncode, 1)
        self.assertIn("blocked", merge.stderr)
        self.assertEqual(view.returncode, 0)
        self.assertEqual(self.calls_log().strip(), "gh pr view 7")


if __name__ == "__main__":
    unittest.main()
