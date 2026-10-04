"""Every detector against its attack corpus in tests/corpus/<detector>/cases.json.

A corpus holds positive, negative and bypass cases. A miss found in review becomes a bypass entry, so the guarantee
is tested as a property over known attacks, not as one fixed example. Detection and redaction read the same cases.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.test_kitchen import KITCHEN, KitchenFixture

CORPUS = Path(__file__).resolve().parent / "corpus"


def load(detector):
    return json.loads((CORPUS / detector / "cases.json").read_text(encoding="utf-8"))


def joined(value):
    return "".join(value) if isinstance(value, list) else value


def scrub(text):
    sys.path.insert(0, str(KITCHEN.parent.parent / "lib"))
    try:
        from kitchen.transcripts import scrub as kitchen_scrub
    finally:
        sys.path.pop(0)
    return kitchen_scrub(text)


class PublicSafetyCorpus(KitchenFixture):
    """`kitchen check` must report exactly the expected labels for each case file, working tree or index."""

    def run_corpus(self, detector):
        corpus = load(detector)
        denylist = None
        if "denylist" in corpus:
            denylist = self.home / "denylist.txt"
            denylist.write_text("\n".join(corpus["denylist"]) + "\n")
        for case in corpus["cases"]:
            path = self.repo / "cases" / f"{case['id']}.txt"
            path.parent.mkdir(exist_ok=True)
            path.write_text(joined(case["text"]) + "\n")
            if case.get("where") == "staged-only":
                subprocess.run(["git", "-C", str(self.repo), "add", "--", str(path)], check=True)
                path.write_text("clean\n")
        output = self.kitchen("check", "--lint-only", denylist=denylist).stdout
        for case in corpus["cases"]:
            prefix = f"cases/{case['id']}.txt" + (" (staged)" if case.get("where") == "staged-only" else "") + ":"
            reported = {line.split(": ", 1)[1].removesuffix(" in a public repo")
                        for line in output.splitlines() if line.startswith(f"FAIL  {prefix}")}
            with self.subTest(case["id"], kind=case["kind"]):
                self.assertEqual(reported, set(case["check"]), output)

    def test_credentials_corpus_detection(self):
        self.run_corpus("credentials")

    def test_private_terms_corpus_detection(self):
        self.run_corpus("private-terms")


class RedactionCorpus(KitchenFixture):
    def test_credentials_corpus_redaction(self):
        for case in load("credentials")["cases"]:
            if "redact" not in case:
                continue
            text = joined(case["text"])
            with self.subTest(case["id"], kind=case["kind"]):
                scrubbed = scrub(text)
                if case["redact"] == "keeps":
                    self.assertEqual(scrubbed, text)
                else:
                    for secret in case["secret"]:
                        self.assertNotIn(secret, scrubbed)


class ProvenanceCorpus(KitchenFixture):
    """`kitchen retro` classifies each corpus transcript exactly as expected."""

    def write_case(self, home, case):
        for relative, events in case["transcripts"].items():
            base = home / ".claude" / "projects" if case["tool"] == "claude" else home / ".codex" / "sessions" / "2099" / "01" / "01"
            path = base / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(e, separators=(",", ":")) + "\n" for e in events))
        for automation in case.get("automations", []):
            folder = home / ".codex" / "automations" / automation["id"]
            folder.mkdir(parents=True)
            (folder / "automation.toml").write_text(
                f'version = 1\nid = "{automation["id"]}\"\nkind = "{automation["kind"]}"\nprompt = {json.dumps(automation["prompt"])}\n')

    def test_provenance_corpus(self):
        for case in load("provenance")["cases"]:
            home = self.home / "cases" / case["id"]
            home.mkdir(parents=True)
            self.write_case(home, case)
            env = {**os.environ, "HOME": str(home), "KITCHEN_REPO": str(self.repo), "KITCHEN_STATE": str(home / "state"),
                   "KITCHEN_CONFIG": str(home / "config"), "KITCHEN_DENYLIST": str(home / "none")}
            result = subprocess.run([sys.executable, str(KITCHEN), "retro", "--since", "1d", "--json", "--include-automated", "--tool", case["tool"]],
                                    env=env, capture_output=True, text=True, cwd=home)
            with self.subTest(case["id"], kind=case["kind"]):
                self.assertEqual(result.returncode, 0, result.stderr)
                got = [[p["text"], p["excluded"]] for p in json.loads(result.stdout)]
                self.assertEqual(got, case["expect"])
