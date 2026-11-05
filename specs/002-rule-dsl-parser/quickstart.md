# Quickstart: M1 Rule DSL

All commands run from the repository root after `uv sync --locked`. Output files go to a fresh temporary
directory, never into the working tree.

## Check the corpus

```bash
uv run assertion-rules check --ruleset rules/corpus.toml
# ok: 17 rules, 1 derived, 27 parameters
```

## Read one rule's syntax tree

```bash
uv run assertion-rules dump --ruleset rules/corpus.toml --rule battery-floor
```

The bytes equal `tests/fixtures/rule_trees/battery-floor.json`.

## Render a tree image

```bash
out="$(mktemp -d)"
uv run assertion-rules tree --ruleset rules/corpus.toml --rule battery-runout-forecast \
  --output "$out/battery-runout-forecast.png"
```

Each node shows its kind, its source fragment and its checked type, for example `scalar[s]`.

## See a rejection

```bash
tmp="$(mktemp -d)"
cat > "$tmp/bad.toml" <<'EOF'
schema_version = "1.0.0"

[parameters.battery_floor_percent]
unit = "%"

[rules.typo]
category = "threshold"
expression = "batery_percent >= battery_floor_percent"
EOF
uv run assertion-rules check --ruleset "$tmp/bad.toml"   # exit 1
# <tmp>/bad.toml: rule typo: 1:1: unknown_name: batery_percent is not declared
#     batery_percent >= battery_floor_percent
#     ^^^^^^^^^^^^^^
```

## Run the gate

```bash
MPLBACKEND=Agg uv run pytest
uv run ruff check .
uv run ruff format --check .
```
