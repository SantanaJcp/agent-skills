"""Credential shapes shared by `kitchen check` (refuse to publish) and `kitchen retro` (redact)."""
from __future__ import annotations

import re

# Tokens with a recognizable vendor shape. Tests build their samples at runtime so this repo never holds one.
TOKENS = [
    ("GitHub token", r"\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}"),
    ("Slack token", r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    ("AWS access key", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("API key", r"\bsk-[A-Za-z0-9_-]{16,}"),  # OpenAI and Anthropic style
    ("JWT", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("private key", r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
]

_NAME = r"(?:password|passwd|secret|client[_-]?secret|api[_-]?key|access[_-]?token|auth[_-]?token)"

# A password, secret, API key or token assigned a literal value: quoted, or a bare run of 8+ token characters.
# Variables, placeholders (<...>, ${...}) and lookups (os.environ[...], get_key()) are not literals.
ASSIGNMENT = re.compile(
    rf"(?i)\b{_NAME}\b\s*[=:]\s*(?:([\"'])[^\"'\s$<{{]{{6,}}\1|(?![\"'$<{{(\[])[A-Za-z0-9_+/.=-]{{8,}}(?![\w(\[]))"
)

CREDENTIALS = [(label, re.compile(pattern)) for label, pattern in TOKENS] + [("credential assignment", ASSIGNMENT)]

# Redaction is broader than the publish check: in a transcript any `token: value` is worth hiding.
REDACT = re.compile(
    "|".join(pattern for _, pattern in TOKENS)
    + r"|(?i:(?:password|passwd|token|secret|api[_-]?key)\s*[=:]\s*)\S+"
)


def find(line: str) -> list[str]:
    """Labels of every credential shape present in one line."""
    return [label for label, pattern in CREDENTIALS if pattern.search(line)]


def redact(text: str) -> str:
    return REDACT.sub("[REDACTED]", text)
