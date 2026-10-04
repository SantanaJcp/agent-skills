import json
import subprocess
import unittest
from pathlib import Path

from tests.test_kitchen import KitchenFixture


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class ProjectFixture(KitchenFixture):
    extra_env = {"KITCHEN_AGENT": "claude", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

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
        (project / "decisions.md").write_text("- [x] 2026-10-01 use uuids later\n- [ ] keep the old route?\n- [ ] drop the table?\n")
        self.list_projects(project)

        out = self.kitchen("status").stdout

        self.assertIn("2 entries, 1 blocked", out)
        self.assertLess(out.index("needs the prod password"), out.index("step one done"))
        self.assertIn("2 owed by you", out)

    def test_status_reports_nightly_green_streak_and_failed_step(self):
        project = self.make_project("shop")
        nightly = self.home / "state" / "nightly"
        nightly.mkdir(parents=True)
        runs = [{"ts": "t1", "sha": "a", "status": "red", "failed_step": "tests"}, {"ts": "t2", "sha": "b", "status": "green"}, {"ts": "t3", "sha": "c", "status": "green"}]
        (nightly / "shop.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))

        out = self.kitchen("status", str(project)).stdout

        self.assertIn("✓ green at t3 on c", out)
        self.assertIn("green streak 2", out)

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
            self.claude_event(launched, entrypoint="sdk-ts", origin=None),
        ], session="probe", folder="-tmp")
        self.write_claude([
            {"type": "assistant", "timestamp": "2099-01-01T09:59:00Z", "message": {"content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": f"cd /tmp && claude -p '{launched}' --model x"}}]}},
        ], session="parent", folder="-work-lead")

        result = self.kitchen("retro", "--since", "1d", "--tool", "claude", cwd=self.home)

        self.assertEqual(self.texts("--tool", "claude"), ["dale, sigue"])
        self.assertEqual(result.stdout.splitlines()[-1],
                         "1 prompts included · 5 excluded (notification 2, agent-launched 1, non-interactive 1, replayed 1)")

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
        self.assertTrue(result.stdout.endswith("2 prompts included · 3 excluded (subagent 1, automation 1, non-interactive 1)\n"), result.stdout)

    def test_include_automated_shows_excluded_messages_with_their_reason(self):
        heartbeat = "<heartbeat>\n  <automation_id>phone-progress</automation_id>\n</heartbeat>"
        self.write_codex("thread", "vscode", ["listo", (heartbeat, False)])

        prompts = json.loads(self.retro("--include-automated").stdout)

        self.assertEqual([(p["text"][:11], p["excluded"]) for p in prompts], [("listo", None), ("<heartbeat>", "automation")])

    def test_json_output_keeps_coverage_off_stdout(self):
        self.write_claude([self.claude_event("dale")])

        result = self.retro()

        self.assertEqual(json.loads(result.stdout)[0]["text"], "dale")
        self.assertIn("1 prompts included · 0 excluded (none)", result.stderr)

    def test_secrets_are_redacted(self):
        self.write_claude([self.claude_event("use token=abc123 please")])

        self.assertEqual(self.texts(), ["use [REDACTED] please"])

    def test_match_filters_prompts(self):
        self.write_claude([self.claude_event("dale"), self.claude_event("te dije que no")])

        self.assertEqual(self.texts("--match", "te dije"), ["te dije que no"])


if __name__ == "__main__":
    unittest.main()
