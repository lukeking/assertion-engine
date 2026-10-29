# Data Model: M1 Rule DSL and Parser Tree

Contracts referenced: [grammar.ebnf](contracts/grammar.ebnf), [syntax-tree.md](contracts/syntax-tree.md),
[ruleset.md](contracts/ruleset.md), [cli.md](contracts/cli.md).

## Entities

### Span

`start_line`, `start_column`, `end_line`, `end_column`: 1-based integers within one expression string;
`end_column` is exclusive. Invariant: start ≤ end in (line, column) order.

### Token

`kind` (number, name, keyword, reserved word, operator, punctuation, end of input), `text`, `span`.
The lexer emits tokens left to right; whitespace produces no token. A lexical error stops the lexer.

### Syntax node

One of the 15 kinds in syntax-tree.md; frozen; children are nodes or tuples of nodes; every node carries a span.
Nodes compare by value, so two parses of the same text are equal.

### Dimension and type

- **Dimension**: integer exponents `(length, time, battery)`.
- **Type**: `bool`, `scalar[dimension]`, `vector[dimension]`, or the zero-literal scalar whose dimension is
  taken from its partner (ruleset.md "Type and dimension rules").

### Vocabulary

The built-in, read-only name table: 5 fields, 2 functions (`norm`, `hnorm`) and 4 built-in derived quantities,
each with its type. Temporal keywords are not vocabulary entries: the parser recognizes them and the checker
knows their signatures.

### Parameter declaration

`name`, `unit`. No value in M1.

### Derived declaration

`name`, `unit`, `expression` text, parsed `tree`. Built-in derived declarations come from the vocabulary;
rule-set derived declarations come from `[derived]`. Both kinds are parsed and checked identically.

### Rule

`short_name`, `category` (`threshold` | `logic` | `temporal` | `trend`), `expression` text, parsed `tree`.

### Rule set

`schema_version`, ordered `parameters`, `derived`, `rules` (file order). A checked rule set additionally maps
every node of every tree to its type, and every `Name` node to what it resolved to: field, derived quantity or
parameter.

### Diagnostic

`code` (closed list below), `message`, and a location: expression location (`rule` or `derived` name, `line`,
`column`, `end_column`, `fragment`) or file location (`file_line`, `file_column`).

## Loading pipeline (fail-closed, first error wins)

1. Read bytes; decode TOML → `invalid_ruleset` with file location on failure.
2. Validate shape (ruleset.md "File shape") → `invalid_ruleset`.
3. Validate parameter and derived names → `name_conflict`; units → `unknown_unit`.
4. Parse built-in derived definitions (a failure here is a vocabulary bug; a unit test guards it).
5. Parse rule-set derived expressions in file order.
6. Check all derived quantities: names, types, dimensions, declared units, cycles.
7. Parse rules in file order.
8. Check rules; the root of each rule must be `bool`.
9. Return the checked rule set.

## Pratt binding powers

One row per grammar precedence level, in grammar order (research.md Decision 3). A contract test compares the
level sequence of this table, as implemented in `parser.py`, with the level list in grammar.ebnf.

| level | production | tokens | role | binding power | associativity |
|---|---|---|---|---:|---|
| 1 | `conditional` | `if` (… `then` … `else` …) | prefix | 10 | branches extend right |
| 2 | `implication` | `implies` | infix | 20 | right |
| 3 | `conjunction` | `and` | infix | 30 | left |
| 4 | `comparison` | `< <= > >= == !=` | infix | 40 | none (second one is `chained_comparison`) |
| 5 | `additive` | `+ -` | infix | 50 | left |
| 6 | `multiplicative` | `* /` | infix | 60 | left |
| 7 | `unary` | `-` | prefix | 70 | — |
| 8 | `postfix` | `.` | infix | 80 | left |

`then`, `else`, `,`, `)` and end of input have binding power 0: they end the current operand.

**Parse depth limit**: the parser counts nested operand parses — every operand below the rule body opens one
level: a parenthesized group, a prefix operand, a call or temporal argument, a conditional's branch and an infix
operator's right operand — and rejects depth 101 with `nesting_too_deep` before Python's recursion limit can be
reached. So 100 parentheses around `a` are accepted and 100 around `a < b` are not. E1 (2026-10-29, CPython
3.14.4): counting only groups, prefix operands and arguments does not keep that promise — an `implies` chain of
600 operands raises `RecursionError` with no counted level, and so do 100 groups each holding
`a and b < c + d * (…)` even when `implies` levels are counted too. E1: `sys.getrecursionlimit()` is 1000.
E3: 100 levels is far above the corpus (its deepest rule nests a handful of levels).

## Production coverage

The parser takes an optional collector and records a grammar production name each time it builds that
production's construct (including `grouping`, which builds no node). Parsing the 4 built-in derived
definitions, the corpus's derived definitions and its 17 rules must record exactly the 17 productions that carry
a `used by:` annotation in grammar.ebnf (SC-006); the 8 structural productions are not counted.

## Diagnostic codes (closed list)

| stage | code | example |
|---|---|---|
| lexer | `invalid_character` | `battery_percent ≥ 20` |
| lexer | `invalid_number` | `1e3`, `2.` |
| parser | `empty_expression` | expression is only whitespace |
| parser | `unexpected_token` | `battery_percent >= >= x`; a conditional unparenthesized inside a comparison |
| parser | `unexpected_end` | `battery_percent >=` |
| parser | `unclosed_parenthesis` | `(a + b` |
| parser | `trailing_input` | `a < b c` |
| parser | `chained_comparison` | `0 < battery_percent < x` |
| parser | `reserved_word` | `a < b or c < d`; a parameter named `not` |
| parser | `invalid_axis` | `position_ned_m.x` |
| parser | `nesting_too_deep` | 101 nested `(`; 101 consecutive unary `-` |
| rule set | `invalid_ruleset` | TOML syntax error, unknown key, missing `expression`, wrong `schema_version` |
| rule set | `unknown_unit` | `unit = "km"` |
| rule set | `name_conflict` | a parameter named `altitude_m`; the same name in `parameters` and `derived` |
| checker | `unknown_name` | `batery_percent >= x` |
| checker | `arity_mismatch` | `norm(a, b)`, `slope(x)` |
| checker | `type_mismatch` | `battery_percent and x`; `norm(battery_percent)`; comparing two vectors |
| checker | `dimension_mismatch` | `battery_percent > home_distance_m`; `mission_time_s + altitude_m` |
| checker | `not_boolean_rule` | a rule whose expression is `battery_percent` |
| checker | `nonpositive_duration` | `held_for(c, 0)` |
| checker | `derived_unit_mismatch` | derived declared `s` whose expression is in `m` |
| checker | `derived_cycle` | `a := b + 1`, `b := a + 1` |

The invalid-rule fixture holds at least 2 cases per code (SC-005), each with expected code and location.

## Regression suite files

- `rules/corpus.toml`: the corpus rule set (17 rules, 1 derived, 27 parameters).
- `tests/fixtures/rule_trees/<short-name>.json`: golden canonical tree per rule.
- `tests/fixtures/invalid_rules.toml`: `[[case]]` tables with `code`, either `expression` (embedded by the
  test into a minimal valid rule set) or a whole `ruleset`, and the expected `line`/`column` or
  `file_line`/`file_column`.
- A contract test asserts that the short names in `rules/corpus.toml` and `rule-corpus.md` are the same set.
