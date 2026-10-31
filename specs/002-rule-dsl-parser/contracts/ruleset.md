# Contract: rule set file, vocabulary and checks

A rule set is one UTF-8 TOML file (research.md Decision 1). The corpus is `rules/corpus.toml`.
Loading is fail-closed: the first error stops loading and no partial rule set is returned (FR-011).

## File shape

```toml
schema_version = "1.0.0"

[parameters.battery_floor_percent]
unit = "%"

[derived.return_time_s]
unit = "s"
expression = "home_distance_m / cruise_speed_mps + altitude_m / descent_rate_mps"

[rules.battery-floor]
category = "threshold"
expression = "battery_percent >= battery_floor_percent"
```

| Key | Rule |
|---|---|
| `schema_version` | required; exactly `"1.0.0"` |
| `parameters.<name>` | table with exactly `unit`; M1 accepts no value (FR-009) |
| `derived.<name>` | table with exactly `unit` and `expression` |
| `rules.<short-name>` | table with exactly `category` and `expression` |
| `category` | one of `threshold`, `logic`, `temporal`, `trend` (the corpus's four classes) |
| `<name>` (parameter, derived) | `[a-z][a-z0-9_]*`; not a keyword, reserved word, field, function or built-in derived name; unique across parameters and derived |
| `<short-name>` (rule) | `[a-z0-9]+(-[a-z0-9]+)*` |
| `unit` | one of `1`, `%`, `m`, `s`, `m/s`, `%/s` |

Any other top-level key, table key or value type is error `invalid_ruleset`. At least one rule is required.

## Units and dimensions

A dimension is three integer exponents over the base quantities length (m), time (s) and battery
percentage (%). `%` is a project base quantity, not SI's dimensionless ratio (research.md Decision 4).

| unit | (m, s, %) |
|---|---|
| `1` | (0, 0, 0) |
| `%` | (0, 0, 1) |
| `m` | (1, 0, 0) |
| `s` | (0, 1, 0) |
| `m/s` | (1, -1, 0) |
| `%/s` | (0, -1, 1) |

Inferred dimensions may be any exponent triple; only declarations are limited to this table.

## Built-in vocabulary

Fields (from the M0 telemetry snapshot; `vehicle_id` is not exposed):

| name | type |
|---|---|
| `sequence_number` | scalar `1` |
| `mission_time_s` | scalar `s` |
| `position_ned_m` | vector `m` |
| `velocity_ned_mps` | vector `m/s` |
| `battery_percent` | scalar `%` |

Functions: `norm(vector[D]) → scalar[D]` (3-D length), `hnorm(vector[D]) → scalar[D]` (√(n² + e²)).

Built-in derived quantities, defined in DSL and parsed by the same parser at load:

| name | unit | definition |
|---|---|---|
| `altitude_m` | `m` | `-position_ned_m.d` |
| `descent_speed_mps` | `m/s` | `velocity_ned_mps.d` |
| `horizontal_speed_mps` | `m/s` | `hnorm(velocity_ned_mps)` |
| `home_distance_m` | `m` | `hnorm(position_ned_m)` (home is the NED origin) |

Temporal keywords (syntax only in M1; meaning is M2/M3's):

| form | operand types | result |
|---|---|---|
| `prev(x)` | any | type of `x` |
| `ago(x, d)` | any; `d` scalar `s` | type of `x` |
| `held_for(c, d)` | `c` bool; `d` scalar `s` | bool |
| `within(c, d)` | `c` bool; `d` scalar `s` | bool |
| `slope(x, w)` | `x` scalar `D`; `w` scalar `s` | scalar `D/s` |

## Type and dimension rules

- `+`, `-`: both scalars or both vectors, same dimension; result keeps it.
- `*`: scalar × scalar, vector × scalar, scalar × vector; dimensions add.
- `/`: scalar ÷ scalar, vector ÷ scalar; dimensions subtract.
- Unary `-`: scalar or vector; unchanged.
- `.n`, `.e`, `.d`: vector `D` → scalar `D`.
- Comparisons: two scalars of the same dimension → bool. Vectors cannot be compared.
- `and`, `implies`: bool operands → bool.
- `if c then a else b`: `c` bool; `a` and `b` same type and dimension → that type.
- A rule's expression must be bool (`not_boolean_rule`).
- Literals are dimensionless scalars, except literal `0`, which takes the dimension of the other operand of
  `+`, `-` or a comparison, and of the duration position in a temporal keyword.
- A literal duration (second argument of `ago`, `held_for`, `within`, `slope`) must be positive
  (`nonpositive_duration`). Parameter values are bound in M2 and checked there.
- A derived quantity's inferred type must be a scalar or vector of its declared unit
  (`derived_unit_mismatch`); derived quantities may reference each other but not in a cycle (`derived_cycle`).

## Diagnostics

Fields: `code`, `message`, `location`. `location` is either
`{"rule": <short-name> | "derived": <name>, "line", "column", "end_column", "fragment"}` for expression
errors (positions within that expression string) or `{"file_line", "file_column"}` for errors in the file
itself: a TOML syntax error at the decoder's position (TOML nested too deep to decode at 1:1); a shape, name or
unit error (data-model.md loading steps 2–3) at the first non-blank character of the line that defines the
offending key — a missing key at its table's line, a missing top-level key at 1:1.
The closed list of codes is in data-model.md.
