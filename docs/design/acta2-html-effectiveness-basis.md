# Acta v2 HTML-effectiveness audit basis

**Audit date:** 2026-07-22  
**Acta source revision:** `a8b083705553550eda289ddf9cf1d028df907682`  
**Upstream comparison revision:** [`1787245d94aa680edf18b52027e3f859032776ba`](https://github.com/ThariqS/html-effectiveness/commit/1787245d94aa680edf18b52027e3f859032776ba)

This is the durable public summary of the audit that motivated the Acta v2
pilot. The complete acceptance rubric is
[Acta effectiveness criteria v2](acta2-effectiveness-criteria-v2.md).

## Finding

Acta 0.1 preserved important technical properties—offline portability, safe
DOM handling, no-JavaScript readability, print, provenance, epistemic labels,
and durable exports—but too often turned the result into a prose record inside
a common HTML shell. The dominant workflow became “write canonical prose,
then render it” rather than “choose a cognitive instrument, manipulate it,
decide, export, and explicitly accept.” Automated QA proved technical
conformance more strongly than human comprehension.

The audit identified three load-bearing failure classes:

1. visible state and exported state could disagree;
2. the common shell and serialized prose displaced the task-specific
   instrument from the first viewport; and
3. different cognitive jobs converged on the same document topology, with no
   human cognitive-effectiveness release gate.

## Design response

The pilot separates two roles:

- an **instrument** is an open, disposable working surface specialized for one
  cognitive action—compare, monitor, or simulate—and exports candidate state;
- a **record** is the durable, print-first view generated only after explicit
  conversational acceptance updates canonical state.

The browser never writes canonical files. Scenario JSON generates the
instrument; accepted canonical JSON generates the record. Technical integrity
and cognitive effectiveness remain separate gate sets and cannot compensate
for one another.

## Public sources

- [The unreasonable effectiveness of HTML](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html)
- [Thariq Shihipar's HTML Effectiveness examples at the audited revision](https://github.com/ThariqS/html-effectiveness/tree/1787245d94aa680edf18b52027e3f859032776ba)
