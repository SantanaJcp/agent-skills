"""The verify-kitchen-skills feature map covers every `kitchen` command: a new command without a feature file fails here."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FEATURES = REPO / ".agents" / "skills" / "verify-kitchen-skills" / "features"
COMMAND = re.compile(r'\bsub\.add_parser\("([a-z-]+)"')


class FeatureMap(unittest.TestCase):
    def test_every_command_has_a_feature_file_listed_in_the_readme(self):
        commands = COMMAND.findall((REPO / "bin" / "kitchen").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(commands), 10, "the command pattern stopped matching bin/kitchen")
        readme = (FEATURES / "README.md").read_text(encoding="utf-8")
        for name in commands:
            with self.subTest(command=name):
                self.assertTrue((FEATURES / f"{name}.md").is_file(), f"add features/{name}.md")
                self.assertIn(f"({name}.md)", readme, f"list {name} in features/README.md")


if __name__ == "__main__":
    unittest.main()
