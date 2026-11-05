# Contract: `assertion-rules` CLI

Entry point `assertion-rules = "assertion_engine.dsl.cli:main"`. Every command loads the whole rule set
first (contracts/ruleset.md); a rule set with any error is rejected before a command does anything else.

## Commands

### `assertion-rules check --ruleset PATH`

Loads and checks the rule set.

- Success: stdout `ok: <R> rules, <D> derived, <P> parameters`; exit 0. `<D>` counts the rule set's own
  `[derived]` entries; the 4 built-in derived quantities are not counted.
- Invalid rule set: stderr one diagnostic (format below); exit 1; nothing on stdout.

### `assertion-rules dump --ruleset PATH --rule SHORT-NAME`

Writes the rule's canonical syntax tree bytes (contracts/syntax-tree.md) to stdout; exit 0.
Unknown `SHORT-NAME`: stderr `unknown rule: <name>`; exit 2.

### `assertion-rules tree --ruleset PATH --rule SHORT-NAME --output PATH.png`

Renders the rule's syntax tree with checker types to a PNG (FR-014); exit 0.

- `--output` must name a new file whose parent directory exists. An existing file is never overwritten:
  stderr `output exists: <path>`; exit 2.
- The image is written to a temporary file in the same directory and renamed into place, so a failure
  leaves no partial PNG.
- Rendering uses Matplotlib's Agg backend; no display is needed.

## Diagnostic format

```text
<ruleset path>: rule <short-name>: <line>:<column>: <code>: <message>
    <expression line>
    <caret under column … end_column - 1>
```

For a derived quantity, `rule <short-name>` is `derived <name>`. For TOML syntax errors the line is
`<ruleset path>:<file_line>:<file_column>: invalid_ruleset: <message>` with no caret block.

## Exit codes

| code | meaning |
|---|---|
| 0 | success |
| 1 | the rule set was read and is invalid |
| 2 | usage error: bad arguments, unreadable file, unknown rule, output exists |
