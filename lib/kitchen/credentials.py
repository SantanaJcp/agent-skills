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
    # A URL with userinfo (user, a colon, a password, then @host) for postgres, mysql, mongodb+srv, redis, amqp, https...: a literal password, not ${VAR}
    ("URL credentials", r"\b[a-z][a-z0-9+.-]*://[^\s:/@]*:(?![$<{*])[^\s:/@]{3,}@"),
    # Azure storage AccountKey / Service Bus and Event Hub SharedAccessKey (base64), SAS signatures (URL-encoded)
    ("Azure key", r"\b(?i:AccountKey|SharedAccessKey)=[A-Za-z0-9+/]{20,}={0,2}|[?&]sig=[A-Za-z0-9%+/]{20,}"),
]

# Key names that hold a secret, bare or quoted as in JSON and YAML: password, Pwd, client_secret, apiKey,
# api_key, token, github_token, access_token... A prefix is allowed; a suffix is not (password_hash, max_tokens).
_NAME = r"[\w-]*?(?:password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key)"
_KEY = rf"(?:\"{_NAME}\"|'{_NAME}'|\b{_NAME}\b)"

# A secret key assigned a literal value: quoted (6+ chars), or a bare run of 8+ token characters.
# Variables, empty strings, placeholders (<...>, ${...}, {0}, $(...)), paths and lookups (os.environ[...], get_key()) are not literals.
ASSIGNMENT = re.compile(
    rf"(?i){_KEY}\s*[=:]\s*(?:([\"'])[^\"'\s$<{{]{{6,}}\1|(?![\"'$<{{(\[/])[A-Za-z0-9_+/.=-]{{8,}}(?![\w(\[]))"
)

CREDENTIALS = [(label, re.compile(pattern)) for label, pattern in TOKENS] + [("credential assignment", ASSIGNMENT)]

# Redaction is broader than the publish check: any value under a secret key goes, quoted or not,
# and a private key goes from BEGIN to END (or to the end of the text when the block is cut off).
PEM_BLOCK = r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----(?:.*?-----END (?:[A-Z0-9]+ )*PRIVATE KEY-----|.*\Z)"
REDACT = re.compile(
    rf"(?s:{PEM_BLOCK})"
    + "".join(f"|{pattern}" for label, pattern in TOKENS if label != "private key")
    + rf"|(?i:{_KEY}\s*[=:]\s*(?:\"[^\"]*\"|'[^']*'|\S+))"
)


def find(line: str) -> list[str]:
    """Labels of every credential shape present in one line."""
    return [label for label, pattern in CREDENTIALS if pattern.search(line)]


def redact(text: str) -> str:
    return REDACT.sub("[REDACTED]", text)
