/* Deterministic build-time syntax highlighting for Acta v2 code islands.
 *
 * Runs only in Node while materializing instruments — the browser never
 * re-tokenizes anything, so this adds no runtime dependency and no markup
 * sink: every token is escaped through the caller-supplied esc() before it
 * is wrapped in a class-only <span>. Coverage is deliberately small (the
 * JavaScript subset that appears in instrument snippets); anything the
 * scanner does not recognize passes through as escaped plain text.
 */

const KEYWORDS = new Set([
  "async", "await", "break", "case", "catch", "class", "const", "continue",
  "default", "delete", "else", "export", "extends", "false", "finally",
  "for", "from", "function", "get", "if", "import", "in", "instanceof",
  "let", "new", "null", "of", "return", "set", "static", "switch", "this",
  "throw", "true", "try", "typeof", "undefined", "var", "void", "while",
  "yield",
]);

const IDENT_START = /[A-Za-z_$#]/;
const IDENT_PART = /[A-Za-z0-9_$#]/;
const PLAIN_STOP = /[A-Za-z0-9_$#"'`/=]/;

/**
 * @param {string} code raw source text (unescaped)
 * @param {(value: unknown) => string} esc HTML escaper (assemble.esc)
 * @returns {string} escaped HTML with token spans
 */
export function highlightJs(code, esc) {
  let out = "";
  let i = 0;
  const n = code.length;
  /** @param {string | null} cls @param {string} text */
  const push = (cls, text) => {
    if (!text) return;
    out += cls ? `<span class="${cls}">${esc(text)}</span>` : esc(text);
  };

  while (i < n) {
    const ch = code[i];
    const two = code.slice(i, i + 2);

    if (two === "//") {
      let j = code.indexOf("\n", i);
      if (j === -1) j = n;
      push("tok-com", code.slice(i, j));
      i = j;
      continue;
    }
    if (two === "/*") {
      let j = code.indexOf("*/", i + 2);
      j = j === -1 ? n : j + 2;
      push("tok-com", code.slice(i, j));
      i = j;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === "`") {
      let j = i + 1;
      while (j < n && code[j] !== ch) {
        if (code[j] === "\\") j += 1;
        j += 1;
      }
      j = Math.min(j + 1, n);
      push("tok-str", code.slice(i, j));
      i = j;
      continue;
    }
    if (ch >= "0" && ch <= "9") {
      let j = i;
      while (j < n && /[0-9A-Fa-f_.xXoObBn]/.test(code[j])) j += 1;
      push("tok-num", code.slice(i, j));
      i = j;
      continue;
    }
    if (IDENT_START.test(ch)) {
      let j = i;
      while (j < n && IDENT_PART.test(code[j])) j += 1;
      const word = code.slice(i, j);
      let k = j;
      while (k < n && code[k] === " ") k += 1;
      if (KEYWORDS.has(word)) push("tok-kw", word);
      else if (code[k] === "(") push("tok-fn", word);
      else push(null, word);
      i = j;
      continue;
    }
    if (two === "=>") {
      push("tok-kw", "=>");
      i += 2;
      continue;
    }
    // Plain run: whitespace, punctuation, operators — stop before anything
    // that may start a recognized token so the scanner sees it next turn.
    {
      let j = i;
      while (j < n && !PLAIN_STOP.test(code[j])) j += 1;
      if (j === i) {
        push(null, code[i]);
        i += 1;
      } else {
        push(null, code.slice(i, j));
        i = j;
      }
    }
  }
  return out;
}
