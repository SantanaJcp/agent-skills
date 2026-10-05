"""The repo promises Python 3.11+ for the CLI, lib and tests, and 3.9+ for hooks (AGENTS.md). A newer
interpreter accepts syntax those versions reject, so a guard reads the source instead of trusting the local one."""
import io
import sys
import tokenize
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def python_sources():
    for folder in ("bin", "lib", "tests", "hooks", "automation", "skills"):
        for path in sorted((ROOT / folder).rglob("*")):
            if "node_modules" in path.parts or not path.is_file():
                continue
            if path.suffix == ".py" or (path.suffix == "" and path.read_bytes()[:40].startswith(b"#!") and b"python" in path.read_bytes()[:40]):
                yield path


def same_quote_inside_fstring(source: str) -> list[int]:
    """Lines where an f-string's replacement field holds a string with the f-string's own quote: legal only
    since Python 3.12 (PEP 701), a SyntaxError on 3.11."""
    lines, quotes = [], []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.FSTRING_START:
            quotes.append(token.string.lstrip("rRbBfF"))
        elif token.type == tokenize.FSTRING_END and quotes:
            quotes.pop()
        elif token.type == tokenize.STRING and quotes:
            body, outer = token.string.lstrip("rRbBuUfF"), quotes[-1]
            # a single-quoted f-string ends at its quote character; a triple-quoted one only at the triple
            if body.startswith(outer if len(outer) == 3 else outer[0]):
                lines.append(token.start[0])
    return lines


@unittest.skipUnless(sys.version_info >= (3, 12), "the tokenizer exposes f-string parts only from Python 3.12")
class SourceCompatibilityTests(unittest.TestCase):
    def test_the_guard_finds_a_same_quote_string_inside_an_fstring(self):
        self.assertEqual(same_quote_inside_fstring("x = {'a': 1}\ny = f'{x['a']}'\n"), [2])
        self.assertEqual(same_quote_inside_fstring("x = {'a': 1}\ny = f'{x[\"a\"]}'\n"), [])
        self.assertEqual(same_quote_inside_fstring('y = f"""{print("a")}"""\n'), [])  # legal on 3.11

    def test_no_source_uses_fstring_quotes_newer_than_the_promised_python(self):
        found = {str(path.relative_to(ROOT)): lines for path in python_sources()
                 if (lines := same_quote_inside_fstring(path.read_text(encoding="utf-8")))}
        self.assertEqual(found, {}, "these need Python 3.12; use the other quote inside the replacement field")


if __name__ == "__main__":
    unittest.main()
