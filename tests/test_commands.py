import datetime
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.test_kitchen import KITCHEN, KitchenFixture


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def local_ts(days_ago, hour=3, minute=0):
    """A timestamp `days_ago` days back at a local hour, as the nightly writes it."""
    day = datetime.datetime.now().astimezone() - datetime.timedelta(days=days_ago)
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()


def ago(**delta):
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(**delta)).isoformat(timespec="seconds")


class ProjectFixture(KitchenFixture):
    """Fake notifiers on PATH record what would be shown: a test never pops a real notification."""

    def setUp(self):
        super().setUp()
        self.fakebin = Path(self.tmp.name) / "fakebin"
        self.fakebin.mkdir()
        self.notified = Path(self.tmp.name) / "notified.log"
        for notifier in ("osascript", "notify-send"):
            self.fake(notifier, f'echo "$(basename "$0") $*" >> "{self.notified}"')
        self.extra_env = {"KITCHEN_AGENT": "claude", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                          "GIT_COMMITTER_EMAIL": "t@t", "PATH": f"{self.fakebin}{os.pathsep}{os.environ['PATH']}"}

    def fake(self, name, body):
        path = self.fakebin / name
        path.write_text(f"#!/usr/bin/env bash\n{body}\n")
        path.chmod(0o755)

    def notifications(self):
        return self.notified.read_text().splitlines() if self.notified.exists() else []

    def make_project(self, name="shop"):
        project = self.home / "work" / name
        project.mkdir(parents=True)
        git(project, "init", "-q", "-b", "main")
        (project / "README.md").write_text("x\n")
        git(project, "add", ".")
        git(project, "commit", "-q", "-m", "init")
        return project

    def list_projects(self, *paths):
        (self.home / "config").mkdir(exist_ok=True)
        (self.home / "config" / "projects.txt").write_text("# projects\n" + "\n".join(str(p) for p in paths) + "\n")

    def configure_base(self, base, project="shop", extra=""):
        (self.home / "config").mkdir(exist_ok=True)
        (self.home / "config" / "integrate.toml").write_text(f'[projects.{project}]\nbase = "{base}"\nchecks = ["true"]\n{extra}')

    def commit(self, project, name, text, message="change"):
        (project / name).write_text(text)
        git(project, "add", name)
        git(project, "commit", "-q", "-m", message)
        return self.rev(project, "HEAD")

    def rev(self, project, ref):
        return subprocess.run(["git", "-C", str(project), "rev-parse", ref], capture_output=True, text=True, check=True).stdout.strip()

    def write_record(self, kind, runs, project="shop"):
        folder = self.home / "state" / kind
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{project}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))


class LogAndStatusTests(ProjectFixture):
    def test_log_records_repo_branch_sha_and_agent(self):
        project = self.make_project()

        result = self.kitchen("log", "migrated the cursor", "--status", "done", cwd=project)

        entry = json.loads((self.home / "state" / "log.jsonl").read_text().splitlines()[-1])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(entry["repo"]).resolve(), project.resolve())
        self.assertEqual((entry["branch"], entry["agent"], entry["status"]), ("main", "claude", "done"))
        self.assertTrue(entry["sha"])

    def test_status_shows_blocked_entries_first_and_owed_decisions(self):
        project = self.make_project()
        self.kitchen("log", "step one done", "--status", "done", cwd=project)
        self.kitchen("log", "needs the prod password", "--status", "blocked", cwd=project)
        self.commit(project, "decisions.md", "- [x] 2026-10-01 use uuids later\n- [ ] keep the old route?\n- [ ] drop the table?\n")
        self.configure_base("main")
        self.list_projects(project)

        out = self.kitchen("status").stdout

        self.assertIn("2 entries, 1 blocked", out)
        self.assertLess(out.index("needs the prod password"), out.index("step one done"))
        self.assertIn("2 owed by you", out)

    def test_status_reports_nightly_green_streak_and_failed_step(self):
        project = self.make_project("shop")
        nightly = self.home / "state" / "nightly"
        nightly.mkdir(parents=True)
        t3 = ago(hours=2)
        runs = [{"ts": local_ts(2), "sha": "a", "status": "red", "failed_step": "tests"}, {"ts": local_ts(1), "sha": "b", "status": "green"},
                {"ts": t3, "sha": "c", "status": "green"}]
        (nightly / "shop.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))

        out = self.kitchen("status", str(project)).stdout

        self.assertIn(f"green at {t3} on c", out)  # not ✓: short SHAs and no base leave the distance to the base unknown
        self.assertIn("green streak 2 nights", out)
        self.assertNotIn("overdue", out)

    def test_status_shows_unknown_when_git_status_fails(self):
        project = self.make_project()
        (project / ".git" / "index").write_bytes(b"not an index")

        out = self.kitchen("status", str(project)).stdout

        self.assertIn("dirty: unknown", out)

    def test_status_matches_nightly_by_full_sha_and_shows_its_warnings(self):
        project = self.make_project("shop")
        head = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        nightly = self.home / "state" / "nightly"
        nightly.mkdir(parents=True)
        run = {"ts": "t1", "sha": head, "status": "green", "warnings": ["cleanup failed", "metrics skipped"]}
        (nightly / "shop.jsonl").write_text(json.dumps(run) + "\n")

        out = self.kitchen("status", str(project)).stdout

        self.assertIn(f"on {head[:8]} (= HEAD)", out)
        self.assertNotIn(head, out)
        self.assertIn("warnings: cleanup failed; metrics skipped", out)

    def test_status_never_matches_a_short_nightly_sha(self):
        project = self.make_project("shop")
        head = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        nightly = self.home / "state" / "nightly"
        nightly.mkdir(parents=True)
        (nightly / "shop.jsonl").write_text(json.dumps({"ts": "t1", "sha": head[:8], "status": "green"}) + "\n")

        out = self.kitchen("status", str(project)).stdout

        self.assertIn(f"on {head[:8]} ·", out)

    def test_checkpoint_logged_from_a_worktree_shows_under_its_repo(self):
        project = self.make_project("shop")
        worktree = self.home / "work" / "shop-feature"
        git(project, "worktree", "add", "-q", "-b", "feature", str(worktree))
        self.kitchen("log", "worktree step done", "--status", "done", cwd=worktree)

        out = self.kitchen("status", str(project)).stdout

        self.assertIn("worktree step done", out)

    def test_status_never_reports_prs_it_could_not_read_as_none(self):
        project = self.make_project()

        out = self.kitchen("status", str(project)).stdout

        self.assertIn("PRs        unknown:", out)

    def test_status_accepts_a_configured_project_name(self):
        project = self.make_project("shop")
        self.list_projects(project)

        out = self.kitchen("status", "shop", cwd=self.home).stdout

        self.assertIn("shop  main @", out)

    def test_status_reports_a_missing_project_instead_of_skipping_it(self):
        self.list_projects(self.home / "gone")

        out = self.kitchen("status").stdout

        self.assertIn("gone  ✗ path does not exist", out)


    def test_status_reads_decisions_from_the_base_ref_and_names_it(self):
        project = self.make_project("shop")
        git(project, "checkout", "-q", "-b", "dev")
        dev = self.commit(project, "decisions.md", "- [ ] keep the old route?\n- [ ] drop the table?\n")
        git(project, "checkout", "-q", "main")
        self.configure_base("dev")

        out = self.kitchen("status", str(project)).stdout

        self.assertIn(f"decisions  2 owed by you (read from dev @ {dev[:8]})", out)

    def test_status_without_a_base_reports_decisions_unknown_instead_of_reading_the_checkout(self):
        project = self.make_project("shop")
        (project / "decisions.md").write_text("- [ ] keep the old route?\n")

        out = self.kitchen("status", str(project)).stdout

        self.assertIn("decisions  unknown: no base for 'shop'", out)

    def test_status_shows_how_far_the_nightly_sha_is_behind_the_base(self):
        project = self.make_project("shop")
        tested = self.rev(project, "HEAD")
        for number in range(3):
            self.commit(project, f"f{number}", "x\n")
        self.configure_base("main")
        self.write_record("nightly", [{"ts": ago(hours=1), "sha": tested, "status": "green"}])

        out = self.kitchen("status", str(project)).stdout

        self.assertIn("3 behind main", out)

    def test_status_shows_entries_of_no_listed_project_as_unattached(self):
        project = self.make_project("shop")
        other = self.make_project("lab")
        self.kitchen("log", "logged outside any repo", "--status", "blocked", cwd=self.home)
        self.kitchen("log", "logged in an unlisted repo", cwd=other)
        self.kitchen("log", "logged in shop", cwd=project)
        self.list_projects(project)

        out = self.kitchen("status").stdout

        unattached = out[out.index("unattached"):]
        self.assertIn("unattached  2 entries, 1 blocked", unattached)
        self.assertIn("logged outside any repo", unattached)
        self.assertIn("logged in an unlisted repo", unattached)
        self.assertNotIn("logged in shop", unattached)

    def test_status_bounds_the_gh_call_and_prints_unknown_when_it_times_out(self):
        project = self.make_project("shop")
        self.fake("gh", "sleep 10; echo '[]'")

        result = self.kitchen("status", str(project), env_extra={"KITCHEN_GH_TIMEOUT_SECONDS": "1"})

        self.assertIn("PRs        unknown: gh timed out after 1s", result.stdout)
        self.assertNotIn("PRs        none", result.stdout)

    def test_status_counts_the_green_streak_in_nights_and_marks_an_old_nightly_overdue(self):
        project = self.make_project("shop")
        runs = [{"ts": local_ts(4), "sha": "a", "status": "red", "failed_step": "tests"},
                {"ts": local_ts(3), "sha": "b", "status": "green"},
                {"ts": local_ts(2, hour=3), "sha": "c", "status": "green"},
                {"ts": local_ts(2, hour=5), "sha": "c", "status": "green"}]  # a rerun the same night
        self.write_record("nightly", runs)

        out = self.kitchen("status", str(project)).stdout

        self.assertIn("green streak 2 nights", out)
        self.assertIn("overdue", out)
        self.assertIn("nightly    ✗ green at", out)

    def test_status_shows_the_gardeners_last_result_and_its_age(self):
        project = self.make_project("shop")
        before = self.kitchen("status", str(project)).stdout
        self.write_record("gardener", [{"ts": ago(days=8), "status": "published", "detail": "https://example.test/pull/1"},
                                       {"ts": ago(hours=2, minutes=5), "status": "refused", "detail": "no independent verification configured"}])

        after = self.kitchen("status", str(project)).stdout

        self.assertIn("gardener   unknown: no local record", before)
        self.assertIn("gardener   ✗ refused: no independent verification configured · 2h 5m ago", after)

    def green_project(self):
        project = self.make_project("shop")
        self.fake("gh", "echo '[]'")
        self.configure_base("main")
        self.write_record("nightly", [{"ts": ago(hours=1), "sha": self.rev(project, "HEAD"), "status": "green"}])
        self.write_record("gardener", [{"ts": ago(days=1), "status": "published", "detail": "https://example.test/pull/1"}])
        self.list_projects(project)
        return project

    def test_status_exceptions_prints_only_non_green_lines_and_exits_1_when_any(self):
        project = self.green_project()
        green = self.kitchen("status", "--exceptions")
        self.write_record("nightly", [{"ts": ago(hours=1), "sha": self.rev(project, "HEAD"), "status": "red", "failed_step": "tests"}])
        self.kitchen("log", "needs the prod password", "--status", "blocked", cwd=self.home)

        red = self.kitchen("status", "--exceptions")

        self.assertEqual((green.returncode, green.stdout), (0, ""), green.stderr)
        self.assertEqual(red.returncode, 1, red.stdout + red.stderr)
        lines = red.stdout.splitlines()
        self.assertTrue(any(line.startswith("shop  nightly    ✗ red") for line in lines), red.stdout)
        self.assertTrue(any(line.startswith("unattached") and "needs the prod password" in line for line in lines), red.stdout)
        for green_line in ("PRs", "gardener", "decisions", "journal window"):
            self.assertNotIn(green_line, red.stdout)

    def test_a_remote_gardener_is_informational_never_green_and_never_an_exception(self):
        self.green_project()
        (self.home / "state" / "gardener" / "shop.jsonl").unlink()
        self.configure_base("main", extra='gardener = "remote:build-host"\n')

        remote = self.kitchen("status", "--exceptions")
        out = self.kitchen("status").stdout
        self.configure_base("main", extra='gardener = "elsewhere"\n')
        malformed = self.kitchen("status", "--exceptions")
        self.configure_base("main")
        local = self.kitchen("status", "--exceptions")

        self.assertEqual((remote.returncode, remote.stdout), (0, ""), remote.stdout + remote.stderr)
        self.assertIn("  gardener   remote (build-host): not read here", out)
        self.assertNotIn("✓", out[out.index("gardener"):].splitlines()[0])
        self.assertEqual(malformed.returncode, 1, malformed.stdout)
        self.assertIn("shop  gardener   unknown: gardener = 'elsewhere'", malformed.stdout)
        self.assertEqual(local.returncode, 1, local.stdout)
        self.assertIn("shop  gardener   unknown: no local record", local.stdout)

    def test_a_nightly_whose_sha_is_not_in_the_repo_is_not_green(self):
        self.green_project()
        self.write_record("nightly", [{"ts": ago(hours=1), "sha": "f" * 40, "status": "green"}])

        result = self.kitchen("status", "--exceptions")

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("shop  nightly    ✗ green", result.stdout)
        self.assertIn("behind base: unknown", result.stdout)

    def test_a_gardener_record_with_an_unreadable_time_is_not_green(self):
        self.green_project()
        self.write_record("gardener", [{"ts": "yesterday", "status": "published", "detail": "https://example.test/pull/1"}])

        result = self.kitchen("status", "--exceptions")

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("shop  gardener   ✗ published: https://example.test/pull/1 · unknown ago", result.stdout)

    def test_a_local_gardener_record_older_than_a_week_and_a_day_is_overdue_unless_remote(self):
        self.green_project()
        old = [{"ts": ago(days=8, hours=1), "status": "published", "detail": "https://example.test/pull/1"}]
        self.write_record("gardener", [{"ts": ago(days=7, hours=23), "status": "none", "detail": "no gardener branch was committed"}])
        within = self.kitchen("status", "--exceptions")
        self.write_record("gardener", old)
        late = self.kitchen("status", "--exceptions")
        self.configure_base("main", extra='gardener = "remote:build-host"\n')
        remote = self.kitchen("status", "--exceptions")

        self.assertEqual((within.returncode, within.stdout), (0, ""), within.stdout + within.stderr)
        self.assertEqual(late.returncode, 1, late.stdout + late.stderr)
        self.assertIn("shop  gardener   ✗ published: https://example.test/pull/1 · 8d 1h ago"
                      " · overdue: last record 8d 1h ago, cadence weekly plus a day", late.stdout)
        self.assertEqual((remote.returncode, remote.stdout), (0, ""), remote.stdout + remote.stderr)

    def test_journal_entries_with_an_unreadable_time_are_counted_never_dropped(self):
        project = self.make_project("shop")
        self.list_projects(project)
        (self.home / "state").mkdir(exist_ok=True)
        entry = {"ts": "not a time", "repo": str(self.home), "project": None, "agent": "claude", "status": "blocked", "message": "clock broke"}
        (self.home / "state" / "log.jsonl").write_text(json.dumps(entry) + "\n")

        out = self.kitchen("status").stdout

        self.assertIn("unattached  1 entries, 1 blocked, 1 with unknown time", out)
        self.assertIn("clock broke", out)

    def test_log_notifies_only_blocked_and_decision_checkpoints_redacted(self):
        project = self.make_project("shop")
        secret = "tok" + "en=" + "abcd1234efgh5678"

        for message, state in (("step one done", "done"), (f"needs the prod {secret}", "blocked"), ("route a or b?", "decision")):
            self.assertEqual(self.kitchen("log", message, "--status", state, cwd=project).returncode, 0)

        sent = self.notifications()
        self.assertEqual(len(sent), 2, sent)
        self.assertIn("blocked", sent[0])
        self.assertIn("[REDACTED]", sent[0])
        self.assertNotIn("abcd1234efgh5678", sent[0])
        self.assertIn("route a or b?", sent[1])


class NotifyTests(unittest.TestCase):
    """One local notifier for every exception; nothing leaves the machine."""

    def notify(self, system, found, returncode=0):
        sys.path.insert(0, str(KITCHEN.parent.parent / "lib"))
        try:
            from kitchen import notify
        finally:
            sys.path.pop(0)
        calls = []

        def run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, returncode, "", "it broke\n")

        with mock.patch.object(notify.platform, "system", return_value=system), \
                mock.patch.object(notify.shutil, "which", side_effect=lambda name: f"/bin/{name}" if name in found else None), \
                mock.patch.object(notify.subprocess, "run", side_effect=run):
            code, text = notify.notify("kitchen nightly: shop red", "pass" + "word=hunter2hunter2 in the log")
        return code, text, calls

    def test_macos_uses_display_notification_with_the_text_as_arguments(self):
        code, _, calls = self.notify("Darwin", {"osascript"})

        self.assertEqual(code, 0)
        self.assertEqual(calls[0][0], "/bin/osascript")
        self.assertIn("display notification (item 2 of argv) with title (item 1 of argv)", calls[0])
        self.assertEqual(calls[0][-2:], ["kitchen nightly: shop red", "[REDACTED] in the log"])

    def test_linux_uses_notify_send_when_present(self):
        code, _, calls = self.notify("Linux", {"notify-send"})

        self.assertEqual((code, calls), (0, [["/bin/notify-send", "kitchen nightly: shop red", "[REDACTED] in the log"]]))

    def test_without_a_notifier_it_says_so_and_sends_nothing(self):
        code, text, calls = self.notify("Linux", set())

        self.assertEqual((code, calls), (2, []))
        self.assertIn("no notifier available", text)
        self.assertNotIn("hunter2", text)

    def test_a_failing_notifier_is_reported(self):
        code, text, _ = self.notify("Darwin", {"osascript"}, returncode=1)

        self.assertEqual(code, 1)
        self.assertIn("it broke", text)

class IntegrateTests(ProjectFixture):
    """A source repo where feature-a and feature-b each pass alone and break together."""

    CHECK = 'if [ -f feature-a ] && [ -f feature-b ]; then echo "a and b collide"; exit 1; fi'

    def setUp(self):
        super().setUp()
        self.source = self.make_project("shop")
        (self.source / "shared.txt").write_text("base\n")
        git(self.source, "add", ".")
        git(self.source, "commit", "-q", "-m", "base")
        for name in ("a", "b"):
            git(self.source, "checkout", "-q", "-b", f"feature-{name}", "main")
            (self.source / f"feature-{name}").write_text(f"{name}\n")
            git(self.source, "add", ".")
            git(self.source, "commit", "-q", "-m", f"add {name}")
        git(self.source, "checkout", "-q", "main")
        self.configure(f"checks = [{json.dumps(self.CHECK)}]")

    def configure(self, body, project="shop"):
        (self.home / "config").mkdir(exist_ok=True)
        (self.home / "config" / "integrate.toml").write_text(f"[projects.{project}]\nbase = \"main\"\n{body}\n")

    def integrate(self, *args, env_extra=None):
        return self.kitchen("integrate", "--repo", str(self.source), *args, env_extra=env_extra)

    def records(self):
        return [json.loads(line) for line in (self.home / "state" / "integrate" / "shop.jsonl").read_text().splitlines()]

    def sha(self, ref):
        return subprocess.run(["git", "-C", str(self.source), "rev-parse", ref], capture_output=True, text=True, check=True).stdout.strip()

    def test_branches_green_alone_and_red_together_fail_together(self):
        alone = [self.integrate(branch) for branch in ("feature-a", "feature-b")]
        together = self.integrate("feature-a", "feature-b")

        self.assertEqual([r.returncode for r in alone], [0, 0], [r.stdout for r in alone])
        self.assertEqual(together.returncode, 1, together.stdout)
        self.assertIn("check failed after feature-b", together.stdout)
        vector = [self.sha("main"), self.sha("feature-a"), self.sha("feature-b")]
        self.assertEqual((self.records()[-1]["vector"], self.records()[-1]["status"]), (vector, "FAIL"))
        self.assertIn(f"[{' '.join(s[:8] for s in vector)}]", together.stdout)

    def test_a_pass_is_bound_to_the_exact_shas_and_a_moved_head_invalidates_it(self):
        self.integrate("feature-a")
        before = self.integrate("feature-a", "--recorded")
        git(self.source, "checkout", "-q", "feature-a")
        (self.source / "more").write_text("x\n")
        git(self.source, "add", ".")
        git(self.source, "commit", "-q", "-m", "more")
        after = self.integrate("feature-a", "--recorded")

        self.assertEqual(before.returncode, 0, before.stdout)
        self.assertEqual(after.returncode, 1, after.stdout)
        self.assertIn("stale: feature-a", after.stdout)

    def test_a_recorded_pass_is_reused_only_while_the_configured_checks_are_unchanged(self):
        self.integrate("feature-a")
        self.configure(f"checks = [{json.dumps(self.CHECK)}, \"true\"]")
        changed = self.integrate("feature-a", "--recorded")
        self.configure(f"checks = [{json.dumps(self.CHECK)}]")
        restored = self.integrate("feature-a", "--recorded")

        self.assertEqual(changed.returncode, 1, changed.stdout)
        self.assertIn("the check configuration changed", changed.stdout)
        self.assertEqual(restored.returncode, 0, restored.stdout)

    def test_without_a_base_integrate_fails_instead_of_using_origin_main(self):
        git(self.source, "update-ref", "refs/remotes/origin/main", self.sha("main"))
        (self.home / "config" / "integrate.toml").write_text(f"[projects.shop]\nchecks = [{json.dumps(self.CHECK)}]\n")

        results = [self.integrate("feature-a"), self.integrate("feature-a", "--recorded")]

        for result in results:
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("no base for 'shop'", result.stdout)
        self.assertEqual(self.integrate("feature-a", "--base", "main").returncode, 0)

    def test_a_recorded_pass_is_not_reused_once_the_configured_path_changes(self):
        tools = {}
        for name, code in (("good", 0), ("bad", 1)):
            folder = self.home / name
            folder.mkdir()
            (folder / "shop-check").write_text(f"#!/bin/sh\nexit {code}\n")
            (folder / "shop-check").chmod(0o755)
            tools[name] = folder
        self.configure(f'checks = ["shop-check"]\npath = ["{tools["good"]}"]')
        self.assertEqual(self.integrate("feature-a").returncode, 0)
        self.configure(f'checks = ["shop-check"]\npath = ["{tools["bad"]}"]')

        recorded = self.integrate("feature-a", "--recorded")
        real = self.integrate("feature-a")

        self.assertEqual(real.returncode, 1, real.stdout)
        self.assertEqual(recorded.returncode, 1, recorded.stdout)
        self.assertIn("stale: the check configuration changed", recorded.stdout)

    def test_a_merge_conflict_fails_at_that_branch(self):
        for name in ("c1", "c2"):
            git(self.source, "checkout", "-q", "-b", name, "main")
            (self.source / "shared.txt").write_text(f"{name}\n")
            git(self.source, "commit", "-qam", name)
        git(self.source, "checkout", "-q", "main")

        result = self.integrate("c1", "c2")

        self.assertEqual(result.returncode, 1)
        self.assertIn("merge conflict at c2", result.stdout)

    def test_missing_check_config_fails_instead_of_passing(self):
        (self.home / "config" / "integrate.toml").unlink()

        result = self.integrate("feature-a", "--base", "main")

        self.assertEqual(result.returncode, 1)
        self.assertIn("no check commands", result.stdout)

    def test_nothing_it_runs_inherits_git_variables_and_the_source_is_untouched(self):
        self.configure('checks = ["env | grep ^GIT_ && exit 1 || exit 0"]')
        decoy = self.make_project("decoy")
        hook_env = {"GIT_DIR": str(decoy / ".git"), "GIT_INDEX_FILE": str(decoy / ".git" / "index")}
        refs_before = subprocess.run(["git", "-C", str(self.source), "for-each-ref"], capture_output=True, text=True).stdout

        result = self.integrate("feature-a", "feature-b", "--check", "env | grep ^GIT_ && exit 1 || exit 0", env_extra=hook_env)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        refs_after = subprocess.run(["git", "-C", str(self.source), "for-each-ref"], capture_output=True, text=True).stdout
        self.assertEqual(refs_after, refs_before)
        self.assertEqual(subprocess.run(["git", "-C", str(decoy), "log", "--oneline"], capture_output=True, text=True).stdout.count("\n"), 1)

    def test_pr_heads_are_fetched_into_the_clone_only(self):
        origin = self.home / "origin.git"
        git(self.home, "clone", "-q", "--bare", str(self.source), str(origin))
        git(origin, "update-ref", "refs/pull/7/head", self.sha("feature-a"))
        git(self.source, "remote", "add", "origin", str(origin))

        result = self.integrate("pr:7")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.records()[-1]["branches"], [{"ref": "pr:7", "sha": self.sha("feature-a")}])
        self.assertNotIn("pull", subprocess.run(["git", "-C", str(self.source), "for-each-ref"], capture_output=True, text=True).stdout)


class InventoryTests(ProjectFixture):
    def add_user_skill(self, base, name, body):
        folder = self.home / base / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(body)

    def test_inventory_flags_same_skill_with_different_content(self):
        self.add_user_skill(".claude/skills", "deploy", "v1\n")
        self.add_user_skill(".agents/skills", "deploy", "v2\n")

        out = self.kitchen("inventory").stdout

        self.assertIn("drift: deploy has different content", out)

    def test_inventory_does_not_flag_links_to_one_source(self):
        self.add_skill("alpha")
        self.kitchen("install")

        out = self.kitchen("inventory").stdout

        self.assertNotIn("drift: alpha", out)
        self.assertIn("alpha (kitchen)", out)

    def test_inventory_lists_paused_automations_and_disabled_codex_skills(self):
        automation = self.home / ".codex" / "automations" / "brief"
        automation.mkdir(parents=True)
        (automation / "automation.toml").write_text('version = 1\nid = "brief"\nkind = "cron"\nstatus = "PAUSED"\nprompt = "x"\n')
        (self.home / ".codex" / "config.toml").write_text('[[skills.config]]\npath = "/x/pet/SKILL.md"\nenabled = false\n')

        out = self.kitchen("inventory").stdout

        self.assertIn("1 total, 1 paused", out)
        self.assertIn("disabled in Codex config: /x/pet/SKILL.md", out)


class RetroTests(ProjectFixture):
    """Fixtures follow the real transcript formats: Claude Code project JSONL and Codex rollout JSONL."""

    def claude_event(self, text, ts="2099-01-01T10:00:00Z", **extra):
        event = {"type": "user", "timestamp": ts, "cwd": "/work/shop", "entrypoint": "claude-desktop",
                 "promptSource": "sdk", "origin": {"kind": "human"}, "message": {"content": text}}
        event.update(extra)
        return event

    def write_claude(self, events, session="s1", folder="-work-shop"):
        path = self.home / ".claude" / "projects" / folder
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{session}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))

    def write_codex(self, name, source, texts, **meta):
        folder = self.home / ".codex" / "sessions" / "2099" / "01" / "01"
        folder.mkdir(parents=True, exist_ok=True)
        payload = {"id": name, "cwd": "/work/api", "originator": "Codex Desktop", "source": source, "thread_source": "user", **meta}
        lines = [{"type": "session_meta", "timestamp": "2099-01-01T09:00:00Z", "payload": payload}]
        for entry in texts:
            text, client = (entry, True) if isinstance(entry, str) else entry
            item = {"type": "UserMessage", "id": f"u-{len(lines)}", "content": [{"type": "text", "text": text}]}
            if client:
                item["client_id"] = f"c-{len(lines)}"
            lines.append({"timestamp": "2099-01-01T10:00:00Z", "type": "event_msg", "payload": {"type": "item_completed", "thread_id": name, "item": item}})
        (folder / f"rollout-{name}.jsonl").write_text("".join(json.dumps(line, separators=(",", ":")) + "\n" for line in lines))

    def retro(self, *args):
        return self.kitchen("retro", "--since", "1d", "--json", *args, cwd=self.home)

    def texts(self, *args):
        return [p["text"] for p in json.loads(self.retro(*args).stdout)]

    def test_claude_keeps_human_prompts_and_drops_injected_turns(self):
        self.write_claude([
            self.claude_event("no, eso está mal otra vez"),
            self.claude_event([{"type": "tool_result", "content": "output"}]),
            self.claude_event("<system-reminder>context</system-reminder>"),
            self.claude_event("Context handoff (manual_context): moved"),
            self.claude_event("Act as the research sub-agent for this task. Do X"),
            self.claude_event("old prompt", ts="2000-01-01T00:00:00Z"),
        ])

        self.assertEqual(self.texts("--tool", "claude"), ["no, eso está mal otra vez"])

    def test_claude_excludes_by_provenance_not_wording(self):
        launched = "Without using any tools, answer in one line: which language do you reply in?"
        self.write_claude([
            self.claude_event("dale, sigue"),
            self.claude_event("Background task finished", origin={"kind": "task-notification"}, promptSource="system"),
            self.claude_event("You are the weekly gardener. Run unattended.", entrypoint="sdk-cli", origin=None),
            self.claude_event("Delegated task node:delegated-task:abc reached a terminal state. Use task_status."),
            self.claude_event("replayed prompt", uuid="u-replay"),
            {"type": "assistant", "uuid": "a-replay", "parentUuid": "u-replay", "requestId": "req_syn_0001", "message": {"content": []}},
        ])
        self.write_claude([
            {"type": "queue-operation", "operation": "enqueue", "timestamp": "2099-01-01T10:00:00Z", "content": launched},
            self.claude_event(launched, entrypoint="sdk-ts", origin=None, cwd="/tmp"),
        ], session="probe", folder="-tmp")
        self.write_claude([
            {"type": "assistant", "timestamp": "2099-01-01T09:59:00Z", "message": {"content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": f"cd /tmp && claude -p '{launched}' --model x"}}]}},
        ], session="parent", folder="-work-lead")

        result = self.kitchen("retro", "--since", "1d", "--tool", "claude", cwd=self.home)

        self.assertEqual(self.texts("--tool", "claude"), ["dale, sigue"])
        self.assertEqual(result.stdout.splitlines()[-1],
                         "1 prompts included · 5 excluded (notification 2, agent-launched 1, non-interactive 1, replayed 1) · 0 unknown provenance")

    def test_codex_unwraps_requests_and_drops_delegated_and_guardian_sessions(self):
        self.write_codex("human", "vscode", ["## Context:\nfiles\n## My request for Codex:\nsube a dev", "Act as the review sub-agent for this task. Review it"])
        self.write_codex("guardian", {"subagent": {"other": "guardian"}}, ["approve this command?"], thread_source="guardian_review")

        self.assertEqual(self.texts("--tool", "codex"), ["sube a dev"])

    def test_codex_excludes_heartbeats_exec_runs_and_subagent_threads(self):
        heartbeat = "<heartbeat>\n  <automation_id>phone-progress</automation_id>\n  <instructions>check it</instructions>\n</heartbeat>"
        self.write_codex("thread", "vscode", ["pon un monitor cada 5 min", (heartbeat, False), "ya le di a restore"])
        self.write_codex("probe", "exec", ["Without using any tools, say hi"], originator="codex_exec")
        self.write_codex("child", "vscode", ["explore the repo"], thread_source="subagent")

        result = self.kitchen("retro", "--since", "1d", "--tool", "codex", cwd=self.home)

        self.assertEqual(self.texts("--tool", "codex"), ["pon un monitor cada 5 min", "ya le di a restore"])
        self.assertTrue(result.stdout.endswith("2 prompts included · 3 excluded (subagent 1, automation 1, non-interactive 1) · 0 unknown provenance\n"), result.stdout)

    def test_include_automated_shows_excluded_messages_with_their_reason(self):
        heartbeat = "<heartbeat>\n  <automation_id>phone-progress</automation_id>\n</heartbeat>"
        self.write_codex("thread", "vscode", ["listo", (heartbeat, False)])

        prompts = json.loads(self.retro("--include-automated").stdout)

        self.assertEqual([(p["text"][:11], p["excluded"]) for p in prompts], [("listo", None), ("<heartbeat>", "automation")])

    def test_json_output_keeps_coverage_off_stdout(self):
        self.write_claude([self.claude_event("dale")])

        result = self.retro()

        self.assertEqual(json.loads(result.stdout)[0]["text"], "dale")
        self.assertIn("1 prompts included · 0 excluded (none) · 0 unknown provenance", result.stderr)

    def test_secrets_are_redacted(self):
        self.write_claude([self.claude_event("use token=abc123 please")])

        self.assertEqual(self.texts(), ["use [REDACTED] please"])

    def test_match_filters_prompts(self):
        self.write_claude([self.claude_event("dale"), self.claude_event("te dije que no")])

        self.assertEqual(self.texts("--match", "te dije"), ["te dije que no"])


if __name__ == "__main__":
    unittest.main()
