import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

KITCHEN = Path(__file__).resolve().parent.parent / "bin" / "kitchen"

VALID_SKILL = textwrap.dedent("""\
    ---
    name: {name}
    description: "Do one thing well. Use when the fixture needs a valid skill."
    ---

    # {name}

    See [the reference](reference.md).
    """)


class KitchenFixture(unittest.TestCase):
    """A throwaway repo and HOME, so tests never touch the real setup."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo = root / "repo"
        self.home = root / "home"
        (self.repo / "skills").mkdir(parents=True)
        (self.repo / "bin").mkdir()
        shutil.copy(KITCHEN, self.repo / "bin" / "kitchen")
        shutil.copytree(KITCHEN.parent.parent / "lib", self.repo / "lib", ignore=shutil.ignore_patterns("__pycache__"))
        self.home.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    extra_env = {}

    def tearDown(self):
        self.tmp.cleanup()

    def add_skill(self, name, text=None, files=("reference.md",)):
        skill = self.repo / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(text if text is not None else VALID_SKILL.format(name=name))
        for file in files:
            (skill / file).write_text("detail\n")
        return skill

    def add_global_rules(self):
        (self.repo / "global").mkdir(exist_ok=True)
        rules = self.repo / "global" / "AGENTS.md"
        rules.write_text("# Rules\n")
        return rules

    def kitchen(self, *args, denylist=None, cwd=None):
        env = {**os.environ, "HOME": str(self.home), "KITCHEN_REPO": str(self.repo)}
        env["KITCHEN_DENYLIST"] = str(denylist or self.home / "no-denylist.txt")
        env["KITCHEN_STATE"] = str(self.home / "state")
        env["KITCHEN_CONFIG"] = str(self.home / "config")
        env.update(self.extra_env)
        return subprocess.run([sys.executable, str(KITCHEN), *args], env=env, capture_output=True, text=True, cwd=cwd)


class InstallTests(KitchenFixture):
    def test_install_links_each_skill_into_claude_and_codex(self):
        skill = self.add_skill("alpha")

        result = self.kitchen("install")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for target in (self.home / ".claude" / "skills" / "alpha", self.home / ".agents" / "skills" / "alpha"):
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.resolve(), skill.resolve())

    def test_install_links_global_rules_for_both_tools(self):
        rules = self.add_global_rules()

        self.kitchen("install")

        self.assertEqual((self.home / ".claude" / "CLAUDE.md").resolve(), rules.resolve())
        self.assertEqual((self.home / ".codex" / "AGENTS.md").resolve(), rules.resolve())

    def test_install_refuses_unmanaged_paths_and_changes_nothing(self):
        self.add_skill("alpha")
        self.add_global_rules()
        existing = self.home / ".codex" / "AGENTS.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("my current rules\n")

        result = self.kitchen("install")

        self.assertEqual(result.returncode, 1)
        self.assertIn(str(existing), result.stdout)
        self.assertEqual(existing.read_text(), "my current rules\n")
        self.assertFalse((self.home / ".claude" / "skills" / "alpha").exists())

    def test_install_backup_moves_unmanaged_paths_before_linking(self):
        rules = self.add_global_rules()
        existing = self.home / ".codex" / "AGENTS.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("my current rules\n")

        result = self.kitchen("install", "--backup")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(existing.resolve(), rules.resolve())
        backups = list((self.home / ".kitchen-backups").rglob("AGENTS.md"))
        self.assertEqual([b.read_text() for b in backups], ["my current rules\n"])

    def test_install_removes_links_of_deleted_skills_but_keeps_foreign_skills(self):
        self.add_skill("alpha")
        self.kitchen("install")
        foreign = self.home / ".claude" / "skills" / "mine"
        foreign.mkdir()
        (self.repo / "skills" / "alpha" / "SKILL.md").unlink()

        result = self.kitchen("install")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.home / ".claude" / "skills" / "alpha").is_symlink())
        self.assertTrue(foreign.is_dir())

    def test_install_puts_the_cli_on_the_user_bin(self):
        result = self.kitchen("install")

        link = self.home / ".local" / "bin" / "kitchen"
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), (self.repo / "bin" / "kitchen").resolve())

    def test_install_is_idempotent(self):
        self.add_skill("alpha")
        self.kitchen("install")

        second = self.kitchen("install")

        self.assertEqual(second.returncode, 0)
        self.assertNotIn("linked", second.stdout)


class DoctorTests(KitchenFixture):
    def test_doctor_fails_until_install_then_passes(self):
        self.add_skill("alpha")
        self.add_global_rules()

        before = self.kitchen("doctor")
        self.kitchen("install")
        after = self.kitchen("doctor")

        self.assertEqual(before.returncode, 1)
        self.assertIn("missing link", before.stdout)
        self.assertEqual(after.returncode, 0, after.stdout)

    def test_doctor_reports_a_link_whose_skill_lost_its_manifest(self):
        skill = self.add_skill("alpha")
        self.kitchen("install")
        (skill / "SKILL.md").rename(skill / "MOVED.md")

        result = self.kitchen("doctor")

        self.assertEqual(result.returncode, 1)
        self.assertIn("stale link", result.stdout)

    def test_doctor_reports_a_link_whose_source_was_deleted(self):
        skill = self.add_skill("alpha")
        self.kitchen("install")
        for file in skill.iterdir():
            file.unlink()
        skill.rmdir()

        result = self.kitchen("doctor")

        self.assertEqual(result.returncode, 1)
        self.assertIn("dangling link", result.stdout)

    def test_doctor_warns_when_there_are_no_global_rules(self):
        self.kitchen("install")

        result = self.kitchen("doctor")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("WARN  global/AGENTS.md is not in the repo yet", result.stdout)

    def test_doctor_lists_unmanaged_skills(self):
        self.kitchen("install")
        (self.home / ".agents" / "skills" / "mine").mkdir(parents=True)

        result = self.kitchen("doctor")

        self.assertIn("INFO  not managed by kitchen", result.stdout)


class LintTests(KitchenFixture):
    def lint(self):
        return self.kitchen("check", "--lint-only")

    def test_valid_skill_passes(self):
        self.add_skill("alpha")

        result = self.lint()

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_name_must_match_directory(self):
        self.add_skill("alpha", VALID_SKILL.format(name="beta"))

        self.assertIn("must equal the directory name", self.lint().stdout)

    def test_description_is_required(self):
        self.add_skill("alpha", "---\nname: alpha\n---\n\n# alpha\n")

        self.assertIn("description is required", self.lint().stdout)

    def test_block_scalar_description_is_rejected(self):
        self.add_skill("alpha", "---\nname: alpha\ndescription: >\n  folded\n---\n")

        self.assertIn("block scalar", self.lint().stdout)

    def test_skill_over_the_line_cap_fails(self):
        self.add_skill("alpha", VALID_SKILL.format(name="alpha") + "line\n" * 200)

        self.assertIn("lines (max 150)", self.lint().stdout)

    def test_broken_relative_link_fails(self):
        self.add_skill("alpha", files=())

        self.assertIn("broken link reference.md", self.lint().stdout)


class InvocationParityTests(KitchenFixture):
    MANUAL = VALID_SKILL.replace('description:', 'disable-model-invocation: true\ndescription:')

    def add_codex_policy(self, skill, allow):
        (skill / "agents").mkdir()
        (skill / "agents" / "openai.yaml").write_text(f"policy:\n  allow_implicit_invocation: {allow}\n")

    def test_manual_in_both_tools_passes(self):
        skill = self.add_skill("alpha", self.MANUAL.format(name="alpha"))
        self.add_codex_policy(skill, "false")

        result = self.kitchen("check", "--lint-only")

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_manual_only_in_claude_fails(self):
        self.add_skill("alpha", self.MANUAL.format(name="alpha"))

        self.assertIn("manual-only for Claude but not for Codex", self.kitchen("check", "--lint-only").stdout)

    def test_manual_only_in_codex_fails(self):
        skill = self.add_skill("alpha")
        self.add_codex_policy(skill, "false")

        self.assertIn("manual-only for Codex but not for Claude", self.kitchen("check", "--lint-only").stdout)


class PublicSafetyTests(KitchenFixture):
    def test_personal_absolute_path_fails(self):
        self.add_skill("alpha")
        (self.repo / "notes.md").write_text("see /" + "Users/someone/project\n")

        result = self.lint()

        self.assertEqual(result.returncode, 1)
        self.assertIn("notes.md:1: personal path", result.stdout)

    def denylisted(self, terms, content):
        denylist = self.home / "denylist.txt"
        denylist.write_text("# clients\n" + "\n".join(terms) + "\n")
        (self.repo / "notes.md").write_text(content)
        return self.kitchen("check", "--lint-only", denylist=denylist)

    def test_lowercase_term_matches_any_case(self):
        result = self.denylisted(["acmecorp"], "built for AcmeCorp\n")

        self.assertEqual(result.returncode, 1)
        self.assertIn("notes.md:1: private term", result.stdout)

    def test_capitalized_term_matches_only_the_exact_name(self):
        flagged = self.denylisted(["Kestrel"], "built for Kestrel\n")
        common_word = self.denylisted(["Kestrel"], "a kestrel flew by\n")

        self.assertEqual(flagged.returncode, 1)
        self.assertEqual(common_word.returncode, 0, common_word.stdout)

    def test_term_inside_a_longer_word_is_not_flagged(self):
        result = self.denylisted(["novus"], "a novusual word\n")

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_denylist_is_reported_not_silently_skipped(self):
        result = self.lint()

        self.assertIn("WARN  private-term scan skipped", result.stdout)

    def lint(self):
        return self.kitchen("check", "--lint-only")


if __name__ == "__main__":
    unittest.main()
