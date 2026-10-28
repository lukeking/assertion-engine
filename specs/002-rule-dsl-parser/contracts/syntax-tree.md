# Contract: syntax tree and canonical serialization

The parser output for one rule expression. Golden files in `tests/fixtures/rule_trees/<short-name>.json`
hold the expected canonical bytes for every corpus rule (spec FR-001, FR-012, SC-001–SC-003, SC-008).

## Canonical bytes

- Produced by `assertion_engine.artifacts.canonical_bytes` applied to the node document below:
  sorted keys, compact separators, UTF-8, one trailing LF.
- Number literals are stored as their source text string, never as JSON numbers, so the serializer's
  quantization cannot alter them.
- A golden file is `{"rule": "<short-name>", "tree": <node>}`.
- Determinism: the same expression text yields byte-identical output on every run (SC-008).

## Span

Every node has `"span": [start_line, start_column, end_line, end_column]`, 1-based, positions within the
rule's expression string. `end_column` is one past the node's last character. A node's span covers its
own source fragment; parentheses that wrap it are not included, because parentheses belong to no node
(grammar `grouping`).

## Node kinds

| kind | fields (besides `kind`, `span`) | grammar production |
|---|---|---|
| `Number` | `text`: source digits, e.g. `"1"`, `"0.5"` | `number` |
| `Name` | `name` | `name` |
| `Component` | `target`: node, `axis`: `"n"` \| `"e"` \| `"d"` | `postfix` |
| `Negate` | `operand`: node | `unary` |
| `Arithmetic` | `op`: `"+"` \| `"-"` \| `"*"` \| `"/"`, `left`, `right` | `additive`, `multiplicative` |
| `Compare` | `op`: `"<"` \| `"<="` \| `">"` \| `">="` \| `"=="` \| `"!="`, `left`, `right` | `comparison` |
| `And` | `left`, `right` | `conjunction` |
| `Implies` | `antecedent`, `consequent` | `implication` |
| `Conditional` | `condition`, `then`, `else` | `conditional` |
| `Call` | `function`: name string, `arguments`: list of nodes | `call` |
| `Previous` | `value` | `previous` |
| `Ago` | `value`, `duration` | `ago` |
| `HeldFor` | `condition`, `duration` | `held_for` |
| `Within` | `condition`, `duration` | `within` |
| `Slope` | `value`, `window` | `slope` |

Associativity is visible in the tree: `a - b - c` is `Arithmetic(-, Arithmetic(-, a, b), c)`;
`a implies b implies c` is `Implies(a, Implies(b, c))`; `a and b and c` is `And(And(a, b), c)`.

## Example

`battery_percent >= battery_floor_percent` →

```json
{"rule":"battery-floor","tree":{"kind":"Compare","left":{"kind":"Name","name":"battery_percent","span":[1,1,1,16]},"op":">=","right":{"kind":"Name","name":"battery_floor_percent","span":[1,20,1,41]},"span":[1,1,1,41]}}
```

## Checker annotations (not part of the golden tree)

The checker (contracts/ruleset.md, data-model.md) returns each node's type — `bool`, `scalar[<unit>]` or
`vector[<unit>]` — keyed by node identity, and for each `Name` node what it resolved to (`field`, `derived`,
`parameter`). Tree images (FR-014) show both; golden trees do not, so a checker change cannot silently rewrite
the syntax regression suite.
