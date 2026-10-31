"""SC-001–SC-003/SC-008: corpus trees match hand-written shapes and golden bytes."""

import tomllib
from pathlib import Path

import pytest

from assertion_engine.artifacts import canonical_bytes
from assertion_engine.dsl.parser import parse
from assertion_engine.dsl.syntax import (
    Ago,
    And,
    Arithmetic,
    Call,
    Compare,
    Component,
    Conditional,
    HeldFor,
    Implies,
    Name,
    Negate,
    Number,
    Previous,
    Slope,
    Within,
    to_document,
)
from tests.contract.rule_shapes import DERIVED_SHAPES, RULE_SHAPES

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "rules" / "corpus.toml"
GOLDEN_DIR = REPO_ROOT / "tests" / "fixtures" / "rule_trees"

# Gate 「基本規則」 (spec SC-001): the threshold and logic corpus rules.
BASIC_RULES = (
    "battery-floor",
    "altitude-ceiling",
    "horizontal-speed-limit",
    "return-reserve",
    "geofence-cylinder",
    "low-battery-stay-close",
    "descent-speed-near-ground",
)
# Tier 「時序規則」 (spec SC-002): the basic rules and the temporal corpus rules.
TEMPORAL_TIER = BASIC_RULES + (
    "telemetry-heartbeat",
    "monotonic-sequence",
    "battery-tier-low",
    "battery-tier-critical",
    "battery-tier-emergency",
    "no-sudden-jump",
)
# Tier 「全語料」 (spec SC-003): every corpus rule, the trend rules included.
FULL_CORPUS_TIER = TEMPORAL_TIER + (
    "battery-drain-rate",
    "battery-runout-forecast",
    "altitude-trend-ceiling",
    "geofence-forecast",
)
# The highest tier reached: exactly its rules have golden files. 「全語料」 is
# the top tier, and M1 is complete only there (spec SC-004).
REACHED_TIER = FULL_CORPUS_TIER

# contracts/ruleset.md "Built-in vocabulary", built-in derived quantities table,
# copied literally and kept independent of vocabulary.py: expected inputs here
# do not come from the implementation (test_checker.py pins vocabulary.py to it).
BUILT_IN_DEFINITIONS = {
    "altitude_m": "-position_ned_m.d",
    "descent_speed_mps": "velocity_ned_mps.d",
    "horizontal_speed_mps": "hnorm(velocity_ned_mps)",
    "home_distance_m": "hnorm(position_ned_m)",
}

ARITHMETIC_OPS = ("+", "-", "*", "/")
COMPARE_OPS = ("<", "<=", ">", ">=", "==", "!=")


def shape(node):
    """Rewrite a tree in the rule_shapes.py notation, dropping spans."""
    match node:
        case Name(name=text):
            return text
        case Number(text=text):
            return ("number", text)
        case Arithmetic(op=op, left=left, right=right) if op in ARITHMETIC_OPS:
            return (op, shape(left), shape(right))
        case Compare(op=op, left=left, right=right) if op in COMPARE_OPS:
            return (op, shape(left), shape(right))
        case And(left=left, right=right):
            return ("and", shape(left), shape(right))
        case Implies(antecedent=antecedent, consequent=consequent):
            return ("implies", shape(antecedent), shape(consequent))
        case Conditional(condition=condition, then=then, else_=else_):
            return ("if", shape(condition), shape(then), shape(else_))
        case Negate(operand=operand):
            return ("neg", shape(operand))
        case Component(target=target, axis=axis):
            return (".", shape(target), axis)
        case Call(function=function, arguments=arguments):
            return ("call", function, *(shape(argument) for argument in arguments))
        case Previous(value=value):
            return ("prev", shape(value))
        case Ago(value=value, duration=duration):
            return ("ago", shape(value), shape(duration))
        case HeldFor(condition=condition, duration=duration):
            return ("held_for", shape(condition), shape(duration))
        case Within(condition=condition, duration=duration):
            return ("within", shape(condition), shape(duration))
        case Slope(value=value, window=window):
            return ("slope", shape(value), shape(window))
    raise TypeError(f"no shape notation for {node!r}")


def load_corpus() -> dict:
    return tomllib.loads(CORPUS.read_text(encoding="utf-8"))


def rule_expression(short_name: str) -> str:
    return load_corpus()["rules"][short_name]["expression"]


def derived_definitions() -> dict[str, str]:
    corpus_derived = {
        name: derived["expression"]
        for name, derived in load_corpus()["derived"].items()
    }
    return {**BUILT_IN_DEFINITIONS, **corpus_derived}


def tree_bytes(short_name: str, expression: str) -> bytes:
    return canonical_bytes({"rule": short_name, "tree": to_document(parse(expression))})


def test_SC001_basic_tier_is_the_threshold_and_logic_rules():
    rules = load_corpus()["rules"]
    assert len(BASIC_RULES) == 7
    assert set(BASIC_RULES) == {
        name
        for name, rule in rules.items()
        if rule["category"] in ("threshold", "logic")
    }


@pytest.mark.parametrize("short_name", BASIC_RULES)
def test_SC001_basic_rule_matches_hand_written_shape(short_name):
    assert shape(parse(rule_expression(short_name))) == RULE_SHAPES[short_name]


def test_SC002_temporal_tier_adds_the_temporal_rules():
    rules = load_corpus()["rules"]
    assert len(TEMPORAL_TIER) == 13
    assert set(TEMPORAL_TIER) == {
        name
        for name, rule in rules.items()
        if rule["category"] in ("threshold", "logic", "temporal")
    }


@pytest.mark.parametrize("short_name", TEMPORAL_TIER)
def test_SC002_temporal_tier_rule_matches_hand_written_shape(short_name):
    assert shape(parse(rule_expression(short_name))) == RULE_SHAPES[short_name]


def test_SC003_full_corpus_tier_is_every_corpus_rule():
    assert len(FULL_CORPUS_TIER) == 17
    assert set(FULL_CORPUS_TIER) == set(load_corpus()["rules"])


def test_SC003_rule_shapes_cover_every_corpus_rule():
    assert set(RULE_SHAPES) == set(FULL_CORPUS_TIER)


@pytest.mark.parametrize("short_name", FULL_CORPUS_TIER)
def test_SC003_full_corpus_rule_matches_hand_written_shape(short_name):
    assert shape(parse(rule_expression(short_name))) == RULE_SHAPES[short_name]


def test_SC001_derived_shapes_cover_built_in_and_corpus_definitions():
    assert set(derived_definitions()) == set(DERIVED_SHAPES)


@pytest.mark.parametrize("name", sorted(DERIVED_SHAPES))
def test_SC001_derived_definition_matches_hand_written_shape(name):
    assert shape(parse(derived_definitions()[name])) == DERIVED_SHAPES[name]


def test_SC001_battery_floor_bytes_match_contract_example():
    # contracts/syntax-tree.md "Example", copied literally.
    expected = (
        b'{"rule":"battery-floor","tree":{"kind":"Compare","left":{"kind":"Name",'
        b'"name":"battery_percent","span":[1,1,1,16]},"op":">=","right":'
        b'{"kind":"Name","name":"battery_floor_percent","span":[1,20,1,41]},'
        b'"span":[1,1,1,41]}}\n'
    )
    assert tree_bytes("battery-floor", rule_expression("battery-floor")) == expected


def test_SC001_golden_files_are_exactly_the_reached_tier():
    assert GOLDEN_DIR.is_dir(), f"missing {GOLDEN_DIR.relative_to(REPO_ROOT)}"
    assert sorted(path.name for path in GOLDEN_DIR.iterdir()) == sorted(
        f"{short_name}.json" for short_name in REACHED_TIER
    )


@pytest.mark.parametrize("short_name", REACHED_TIER)
def test_SC001_golden_bytes_match_the_parsed_tree(short_name):
    # A missing golden fails here; comparison is never skipped.
    golden = (GOLDEN_DIR / f"{short_name}.json").read_bytes()
    assert tree_bytes(short_name, rule_expression(short_name)) == golden


@pytest.mark.parametrize("short_name", REACHED_TIER)
def test_SC008_three_parses_are_byte_identical(short_name):
    expression = rule_expression(short_name)
    first, second, third = (tree_bytes(short_name, expression) for _ in range(3))
    assert first == second == third
