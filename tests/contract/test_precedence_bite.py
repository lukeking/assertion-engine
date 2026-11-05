"""SC-007: swapping two adjacent precedence levels, or one wrong power, is caught.

A swap must reshape at least one corpus, derived or T010 tree; a wrong power
must fail at least one rule golden or one derived definition's hand-written
shape (tests/contract/rule_shapes.py). The level order is read from
contracts/grammar.ebnf's header, not from parser.py; each altered
binding-power table is injected through parse(binding_powers=...).
"""

import re
import tomllib
from pathlib import Path

import pytest

from assertion_engine.artifacts import canonical_bytes
from assertion_engine.dsl.errors import RuleSetError
from assertion_engine.dsl.parser import BINDING_POWERS, parse
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
from tests.contract.rule_shapes import DERIVED_SHAPES

REPO_ROOT = Path(__file__).resolve().parents[2]
GRAMMAR = REPO_ROOT / "specs" / "002-rule-dsl-parser" / "contracts" / "grammar.ebnf"
CORPUS = REPO_ROOT / "rules" / "corpus.toml"
GOLDEN_DIR = REPO_ROOT / "tests" / "fixtures" / "rule_trees"

# contracts/ruleset.md "Built-in vocabulary", built-in derived quantities table,
# copied literally as in test_rule_trees.py (test_checker.py pins vocabulary.py
# to it).
BUILT_IN_DEFINITIONS = {
    "altitude_m": "-position_ned_m.d",
    "descent_speed_mps": "velocity_ned_mps.d",
    "horizontal_speed_mps": "hnorm(velocity_ned_mps)",
    "home_distance_m": "hnorm(position_ned_m)",
}

# T010's associativity, adjacent-pair, parentheses and conditional cases
# (tests/unit/dsl/test_parser.py), copied as input strings.
T010_CASES = (
    "a - b - c",
    "a implies b implies c",
    "a and b and c",
    "if c then a else b implies d",
    "a < b and c < d implies e < f",
    "a < b + c",
    "a + b * c",
    "-a * b",
    "-x.d",
    "(a + b) * c",
    "a - (b - c)",
    "a < b and (c < d implies e < f)",
    "(if c then a else b) implies d",
    "(-x).d",
    "a <= (if c then x else y)",
    "f(if c then x else y)",
    "if a then b else if c then d else e",
    "if a then if b then c else d else e",
)

# One wrong binding power per level, each checked below to be out of the
# grammar's order (or no tighter than ")"). Where a nearer wrong value leaves
# every rule golden and derived shape unchanged, the value moves further:
WRONG_POWERS = {
    # Every positive value is invisible: the corpus's only conditional sits
    # alone in parentheses. 0 makes "if" unable to start it (unexpected_token).
    "conditional": 0,
    # Past comparison; swapped with conjunction only, nothing fails.
    "implication": 45,
    # Past comparison: comparisons do not chain, so the rule is rejected
    # (chained_comparison) instead of regrouped.
    "conjunction": 45,
    "comparison": 55,  # past additive
    "additive": 65,  # past multiplicative
    "multiplicative": 45,  # below additive
    # Below comparison; past multiplicative or additive, nothing fails.
    "unary": 35,
    # Below unary. No corpus rule has a ".", so no rule golden can fail;
    # altitude_m's shape does: "-position_ned_m.d" negates before the ".".
    "postfix": 65,
}

ARITHMETIC_OPS = ("+", "-", "*", "/")
COMPARE_OPS = ("<", "<=", ">", ">=", "==", "!=")


def grammar_levels() -> list[str]:
    # grammar.ebnf header: "Precedence levels, loosest first ... 1 conditional ..."
    text = GRAMMAR.read_text(encoding="utf-8")
    header = text[text.index("(*") : text.index("*)")]
    numbered = re.findall(r"(\d+) ([a-z_]+)", header.split("Precedence levels", 1)[1])
    assert [int(number) for number, _ in numbered] == list(
        range(1, len(numbered) + 1)
    ), f"grammar.ebnf levels are not numbered 1..n: {numbered}"
    return [level for _, level in numbered]


LEVELS = grammar_levels()
ADJACENT_PAIRS = list(zip(LEVELS, LEVELS[1:]))


def load_corpus() -> dict:
    return tomllib.loads(CORPUS.read_text(encoding="utf-8"))


def rule_expressions() -> dict[str, str]:
    return {name: rule["expression"] for name, rule in load_corpus()["rules"].items()}


def derived_definitions() -> dict[str, str]:
    """The 4 built-in definitions and the corpus's derived definitions."""
    corpus_derived = {
        name: derived["expression"]
        for name, derived in load_corpus()["derived"].items()
    }
    return {**BUILT_IN_DEFINITIONS, **corpus_derived}


def swap_inputs() -> list[str]:
    """The 17 rules, the 4 built-in and the corpus's derived definitions, T010."""
    return [
        *rule_expressions().values(),
        *derived_definitions().values(),
        *T010_CASES,
    ]


def shape(node):
    """Rewrite a tree in the rule_shapes.py notation, dropping spans.

    Mirrors shape() in test_rule_trees.py.
    """
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


def changed_trees(powers) -> list[str]:
    """Inputs whose tree under powers differs from their tree under the real table.

    An input that powers turns into a syntax error has no tree to compare and
    does not count: the swap must reshape a tree, not only reject a text.
    """
    changed = []
    for text in swap_inputs():
        expected = parse(text)
        try:
            tree = parse(text, binding_powers=powers)
        except RuleSetError:
            continue
        if tree != expected:
            changed.append(text)
    return changed


def regression_failures(powers) -> list[str]:
    """Rule goldens and derived shapes that no longer match when parsed with powers.

    Each of the 17 rules is compared with its golden bytes, each derived
    definition with its hand-written shape in DERIVED_SHAPES. A syntax error
    fails the comparison as the regression test would fail: there is no tree
    to match.
    """
    failures = []
    for short_name, expression in rule_expressions().items():
        golden = (GOLDEN_DIR / f"{short_name}.json").read_bytes()
        try:
            tree = parse(expression, binding_powers=powers)
        except RuleSetError as error:
            failures.append(f"rule {short_name}: {error.diagnostic.code}")
            continue
        document = {"rule": short_name, "tree": to_document(tree)}
        if canonical_bytes(document) != golden:
            failures.append(f"rule {short_name}: golden differs")
    for name, expression in derived_definitions().items():
        try:
            tree = parse(expression, binding_powers=powers)
        except RuleSetError as error:
            failures.append(f"derived {name}: {error.diagnostic.code}")
            continue
        if shape(tree) != DERIVED_SHAPES[name]:
            failures.append(f"derived {name}: shape differs")
    return failures


def test_SC007_grammar_has_seven_adjacent_pairs():
    assert len(ADJACENT_PAIRS) == 7, LEVELS


@pytest.mark.parametrize(
    ("first", "second"),
    ADJACENT_PAIRS,
    ids=[f"{first}-{second}" for first, second in ADJACENT_PAIRS],
)
def test_SC007_swapping_adjacent_levels_changes_a_tree(first, second):
    swapped = {
        **BINDING_POWERS,
        first: BINDING_POWERS[second],
        second: BINDING_POWERS[first],
    }
    assert changed_trees(swapped), (
        f"no corpus, derived or T010 tree changes with {first} and {second} swapped"
    )


def test_SC007_real_binding_powers_match_every_golden_and_derived_shape():
    # Control: the comparison below passes for the real table.
    assert regression_failures(BINDING_POWERS) == []


@pytest.mark.parametrize("level", LEVELS)
def test_SC007_a_wrong_binding_power_fails_a_golden_or_derived_shape(level):
    wrong = {**BINDING_POWERS, level: WRONG_POWERS[level]}
    assert sorted(wrong, key=wrong.get) != LEVELS or wrong[level] <= 0, (
        f"{level} = {wrong[level]} keeps the grammar's order"
    )
    assert regression_failures(wrong), (
        f"no rule golden or derived shape fails with {level} = {wrong[level]}"
    )
