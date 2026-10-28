# 003: Rule DSL syntax, rule-set container and Pratt parser

**Status:** Accepted

**Date:** 2026-10-28

## Context

The DSL grammar is the project's hardest decision to reverse: M2's Evaluator, M3's windows and M4's Fuzzer
are all built on it (constitution principle III). Principle III requires the grammar to be derived from a
corpus of at least 10 real rules. The M1 corpus ([rule-corpus.md](../../specs/002-rule-dsl-parser/rule-corpus.md))
has 17 rules across threshold, logic, temporal and trend classes, reviewed rule by rule by the user on
2026-10-28; numbers are named thresholds whose values are not yet chosen.

ADR 002 already chose a handwritten recursive-descent/Pratt parser in Python with an EBNF-like grammar.

## Decision

- **Container**: a rule set is a TOML file declaring parameter units, derived quantities and rules; the DSL
  is a single-expression language. Weighted score 4.15 vs 3.50 for a full DSL file.
- **Syntax**: symbols for arithmetic and comparison; `and`, `implies`, `if … then … else …` for logic;
  `.n`/`.e`/`.d` vector components; the temporal keywords `prev`, `ago`, `held_for`, `within`, `slope`,
  call-shaped with the duration last. Weighted score 4.55 vs 3.60 for infix temporal syntax.
- **`or` and `not`**: no corpus rule needs them, so they are reserved words without productions (user ruling).
- **Units**: declared on vocabulary entries and parameters; the checker infers dimensions over (m, s, %) and
  rejects mismatches. Rule text carries no units (user ruling).
- **Parser**: Pratt with one binding-power row per grammar level, checked against the EBNF by a contract test.
  Weighted score 4.25 vs 4.00 for one-function-per-level recursive descent.
- **Parse vs check**: the parser builds trees only; a separate checker resolves names, arity, types and
  dimensions.

The scoring tables, evidence tiers and sources are in
[research.md](../../specs/002-rule-dsl-parser/research.md).

## Consequences

- Every grammar production is justified by a corpus rule, and a coverage test keeps it that way.
- The temporal keywords are distinct tree nodes, so M2/M3 can see which rules need history or must wait.
- Units catch formula errors at load time; the cost is a type checker in M1 and `%` treated as its own base
  quantity rather than SI's dimensionless ratio.
- Rule text lives in TOML strings; expression positions are relative to each string.

## Revisit when

- a real rule needs `or`/`not` and cannot be written clearly with `implies`;
- rules need structure TOML strings cannot hold (cross-rule references, local bindings);
- a rule needs unit-bearing literals, a fourth base quantity, or `%` mixed with dimensionless values;
- the binding-power table can no longer be kept in one-to-one correspondence with the grammar levels.
