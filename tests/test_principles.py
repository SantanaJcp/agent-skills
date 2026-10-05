"""Every control names the principle it enforces, and every name is a principle in PRINCIPLES.md.

A control is a guard, a scheduled job, a CLI module, a must-have of `kitchen init`, or a skill. They are found by
globbing, so a new one is held to this suite the moment it lands; a helper that enforces nothing is excused by name
in NOT_CONTROLS, with the reason.
"""
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "lib"))

from kitchen import repocheck, rules  # noqa: E402

NOT_CONTROLS = {
    "hooks/shellparse.py": "the parser the guards share",
    "automation/bin/install-schedule": "writes launchd and systemd units; the jobs it schedules are the controls",
    "lib/kitchen/__init__.py": "package marker",
    "lib/kitchen/checkplan.py": "picks which test modules a commit runs",
    "lib/kitchen/common.py": "paths and git helpers",
    "lib/kitchen/environment.py": "tool and schedule probes that doctor prints",
    "lib/kitchen/inventory.py": "lists what the agents can see",
    "lib/kitchen/notify.py": "sends a local notification for the controls that decide to",
}
CANDIDATES = [*REPO.glob("hooks/*"), *REPO.glob("skills/*/SKILL.md"), *REPO.glob("automation/bin/*"), *REPO.glob("lib/kitchen/*.py")]
CONTROLS = sorted(p for p in CANDIDATES if p.is_file() and p.name != "README.md" and str(p.relative_to(REPO)) not in NOT_CONTROLS)
DECLARATION = re.compile(r"Principles(?: \([^)]*\))?:\s*(.+)")
NAME = re.compile(r"`([a-z][a-z-]*)`")


def declared(path: Path) -> list[str]:
    match = DECLARATION.search(path.read_text(encoding="utf-8"))
    return NAME.findall(match.group(1)) if match else []


class Principles(unittest.TestCase):
    def setUp(self):
        self.ids = [pid for pid, _, _ in rules.principles(REPO)]

    def test_principles_parse_with_unique_ids(self):
        self.assertGreaterEqual(len(self.ids), 13, "PRINCIPLES.md headings must read `## N. Title (`id`)`")
        self.assertEqual(len(self.ids), len(set(self.ids)))

    def test_every_control_names_known_principles(self):
        for path in CONTROLS:
            with self.subTest(control=str(path.relative_to(REPO))):
                self.assertTrue(path.is_file(), "a listed control is missing")
                names = declared(path)
                self.assertTrue(names, "no `Principles:` line naming at least one principle")
                self.assertEqual([n for n in names if n not in self.ids], [], "names a principle PRINCIPLES.md does not define")

    def test_every_excused_helper_still_exists(self):
        self.assertEqual([p for p in NOT_CONTROLS if not (REPO / p).is_file()], [], "drop a gone helper from NOT_CONTROLS")

    def test_every_must_have_names_a_known_principle(self):
        for key, _, principle in repocheck.MUST_HAVES:
            with self.subTest(must_have=key):
                self.assertIn(principle, self.ids)

    def test_every_principle_is_enforced_or_says_rule_only(self):
        text = (REPO / "PRINCIPLES.md").read_text(encoding="utf-8")
        sections = dict(zip(self.ids, re.split(r"^## \d+\. ", text, flags=re.MULTILINE)[1:]))
        cited = {n for path in CONTROLS for n in declared(path)} | {p for _, _, p in repocheck.MUST_HAVES}
        for pid in self.ids:
            with self.subTest(principle=pid):
                enforced = re.search(r"^- \*\*Enforced by:\*\* (.+)$", sections[pid], re.MULTILINE)
                self.assertTrue(enforced, "no `Enforced by:` line")
                self.assertTrue(pid in cited or enforced.group(1).startswith("rule only"),
                                "no control names this principle, and its `Enforced by:` does not start with `rule only`")


if __name__ == "__main__":
    unittest.main()
