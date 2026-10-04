#!/usr/bin/env python3
"""Refuses a diff whose added lines look like a credential. Reads `git diff -U0` on stdin.

  git diff -U0 --no-color <base> <tree-ish> | scan_diff.py

A layer independent of the sandbox: whatever the agent managed to read, a secret must not reach a PR.
Three checks on every added line:
- the kitchen's own redaction patterns (lib/kitchen, the same ones `kitchen retro` uses);
- known token shapes, kept here so this check does not depend on the kitchen's list;
- long high-entropy runs (random-looking keys with no known prefix).
Prints one line per finding (file, line, kind; never the value) and exits 1 when anything matched.
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from kitchen.transcripts import scrub  # noqa: E402

KNOWN = [
    ("GitHub token", r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    ("Anthropic or OpenAI key", r"\bsk-[A-Za-z0-9_-]{16,}"),
    ("AWS access key", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("Slack token", r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    ("Google API key", r"\bAIza[0-9A-Za-z_-]{35}"),
    ("Stripe key", r"\b[rs]k_live_[0-9A-Za-z]{16,}"),
    ("npm token", r"\bnpm_[A-Za-z0-9]{36}"),
    ("JWT", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("private key", r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
    ("bearer token", r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{20,}"),
]
KNOWN = [(label, re.compile(pattern)) for label, pattern in KNOWN]
CANDIDATE = re.compile(r"[A-Za-z0-9+/_=-]{32,}")
MIN_ENTROPY = 4.0  # bits per character; hex (git SHAs, hashes) stays below it
MIN_SWITCHES = 0.45  # share of neighbouring characters that change class (lower, upper, digit, other):
# random keys switch about 6 times in 10 (98% of random 32-40 char keys pass 0.45), camelCase identifiers and
# paths only at word boundaries (contrived ones measured 0.32-0.38)


def entropy(text: str) -> float:
    counts = Counter(text)
    return -sum(n / len(text) * math.log2(n / len(text)) for n in counts.values())


def char_class(char: str) -> str:
    return "l" if char.islower() else "u" if char.isupper() else "d" if char.isdigit() else "o"


def switches(text: str) -> float:
    return sum(char_class(a) != char_class(b) for a, b in zip(text, text[1:])) / (len(text) - 1)


def high_entropy(line: str) -> bool:
    for run in CANDIDATE.findall(line):
        mixed = re.search(r"[a-z]", run) and re.search(r"[A-Z]", run) and re.search(r"[0-9]", run)
        if mixed and entropy(run) >= MIN_ENTROPY and switches(run) >= MIN_SWITCHES:
            return True
    return False


def findings(diff: str) -> list[str]:
    found, path, line_no = [], "?", 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            line_no = int(match.group(1)) if match else 0
        elif line.startswith("+"):
            added = line[1:]
            kinds = [label for label, pattern in KNOWN if pattern.search(added)]
            if scrub(added) != added:
                kinds.append("redaction pattern")
            if not kinds and high_entropy(added):
                kinds.append("high-entropy string")
            if kinds:
                found.append(f"{path}:{line_no}: {', '.join(dict.fromkeys(kinds))}")
            line_no += 1
    return found


def main() -> int:
    found = findings(sys.stdin.read())
    for finding in found:
        print(finding)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
