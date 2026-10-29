"""FR-002/FR-003/FR-004/FR-006: Pratt parsing of the non-temporal constructs.

Expected trees are written by hand from contracts/grammar.ebnf and
contracts/syntax-tree.md, spans included; none is produced by the parser.
"""

from collections import Counter

import pytest

from assertion_engine.dsl.errors import ExpressionLocation, RuleSetError
from assertion_engine.dsl.parser import BINDING_POWERS, parse
from assertion_engine.dsl.syntax import (
    And,
    Arithmetic,
    Call,
    Compare,
    Component,
    Conditional,
    Implies,
    Name,
    Negate,
    Number,
    Span,
)


def name(text, column):
    """A one-line Name starting at column."""
    return Name(text, Span(1, column, 1, column + len(text)))


def span(start, end):
    """A one-line span."""
    return Span(1, start, 1, end)


# Associativity (contracts/syntax-tree.md "Node kinds").


def test_FR004_subtraction_is_left_associative():
    assert parse("a - b - c") == Arithmetic(
        "-",
        Arithmetic("-", name("a", 1), name("b", 5), span(1, 6)),
        name("c", 9),
        span(1, 10),
    )


def test_FR004_implies_is_right_associative():
    assert parse("a implies b implies c") == Implies(
        name("a", 1),
        Implies(name("b", 11), name("c", 21), span(11, 22)),
        span(1, 22),
    )


def test_FR004_and_is_left_associative():
    assert parse("a and b and c") == And(
        And(name("a", 1), name("b", 7), span(1, 8)),
        name("c", 13),
        span(1, 14),
    )


# One case per adjacent pair of the 8 grammar levels; swapping the pair's
# binding powers changes each tree (SC-007 bite check).


def test_FR006_else_branch_swallows_implies():
    # conditional / implication
    assert parse("if c then a else b implies d") == Conditional(
        name("c", 4),
        name("a", 11),
        Implies(name("b", 18), name("d", 28), span(18, 29)),
        span(1, 29),
    )


def test_FR004_and_binds_before_implies():
    # implication / conjunction and conjunction / comparison (spec US1 scenario 2)
    assert parse("a < b and c < d implies e < f") == Implies(
        And(
            Compare("<", name("a", 1), name("b", 5), span(1, 6)),
            Compare("<", name("c", 11), name("d", 15), span(11, 16)),
            span(1, 16),
        ),
        Compare("<", name("e", 25), name("f", 29), span(25, 30)),
        span(1, 30),
    )


def test_FR004_addition_binds_before_comparison():
    # comparison / additive
    assert parse("a < b + c") == Compare(
        "<",
        name("a", 1),
        Arithmetic("+", name("b", 5), name("c", 9), span(5, 10)),
        span(1, 10),
    )


def test_FR004_multiplication_binds_before_addition():
    # additive / multiplicative
    assert parse("a + b * c") == Arithmetic(
        "+",
        name("a", 1),
        Arithmetic("*", name("b", 5), name("c", 9), span(5, 10)),
        span(1, 10),
    )


def test_FR004_negate_wraps_only_its_operand():
    # multiplicative / unary
    assert parse("-a * b") == Arithmetic(
        "*",
        Negate(name("a", 2), span(1, 3)),
        name("b", 6),
        span(1, 7),
    )


def test_FR004_negate_wraps_the_component():
    # unary / postfix
    assert parse("-x.d") == Negate(
        Component(name("x", 2), "d", span(2, 5)),
        span(1, 5),
    )


# Parentheses change the tree but build no node.


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "(a + b) * c",
            Arithmetic(
                "*",
                Arithmetic("+", name("a", 2), name("b", 6), span(2, 7)),
                name("c", 11),
                span(1, 12),
            ),
        ),
        (
            "a - (b - c)",
            Arithmetic(
                "-",
                name("a", 1),
                Arithmetic("-", name("b", 6), name("c", 10), span(6, 11)),
                span(1, 12),
            ),
        ),
        (
            "a < b and (c < d implies e < f)",
            And(
                Compare("<", name("a", 1), name("b", 5), span(1, 6)),
                Implies(
                    Compare("<", name("c", 12), name("d", 16), span(12, 17)),
                    Compare("<", name("e", 26), name("f", 30), span(26, 31)),
                    span(12, 31),
                ),
                span(1, 32),
            ),
        ),
        (
            "(if c then a else b) implies d",
            Implies(
                Conditional(name("c", 5), name("a", 12), name("b", 19), span(2, 20)),
                name("d", 30),
                span(1, 31),
            ),
        ),
        (
            "(-x).d",
            Component(Negate(name("x", 3), span(2, 4)), "d", span(1, 7)),
        ),
    ],
    ids=["additive", "subtraction", "implication", "conditional", "postfix"],
)
def test_FR004_parentheses_regroup(text, expected):
    # Without its parentheses each text is a case above with a different tree.
    assert parse(text) == expected


def test_FR006_conditional_compared_on_the_right_is_parenthesized():
    # A conditional is no comparison operand; descent-speed-near-ground groups it.
    assert parse("a <= (if c then x else y)") == Compare(
        "<=",
        name("a", 1),
        Conditional(name("c", 10), name("x", 17), name("y", 24), span(7, 25)),
        span(1, 26),
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "f(if c then x else y)",
            Call(
                "f",
                (Conditional(name("c", 6), name("x", 13), name("y", 20), span(3, 21)),),
                span(1, 22),
            ),
        ),
        (
            "if a then b else if c then d else e",
            Conditional(
                name("a", 4),
                name("b", 11),
                Conditional(name("c", 21), name("d", 28), name("e", 35), span(18, 36)),
                span(1, 36),
            ),
        ),
        (
            "if a then if b then c else d else e",
            Conditional(
                name("a", 4),
                Conditional(name("b", 14), name("c", 21), name("d", 28), span(11, 29)),
                name("e", 35),
                span(1, 36),
            ),
        ),
    ],
    ids=["call-argument", "else-branch", "then-branch"],
)
def test_FR006_conditional_starts_any_expression(text, expected):
    assert parse(text) == expected


def test_FR004_calls_nest_and_take_any_expression():
    assert parse("f(a + b, g(c))") == Call(
        "f",
        (
            Arithmetic("+", name("a", 3), name("b", 7), span(3, 8)),
            Call("g", (name("c", 12),), span(10, 14)),
        ),
        span(1, 15),
    )


# Spans, written out in full; parentheses that wrap a node are not in its span.


def test_FR003_compare_span():
    assert parse("battery_percent >= battery_floor_percent") == Compare(
        ">=",
        Name("battery_percent", Span(1, 1, 1, 16)),
        Name("battery_floor_percent", Span(1, 20, 1, 41)),
        Span(1, 1, 1, 41),
    )


def test_FR003_arithmetic_and_number_spans():
    assert parse("x.d * 0.5") == Arithmetic(
        "*",
        Component(Name("x", Span(1, 1, 1, 2)), "d", Span(1, 1, 1, 4)),
        Number("0.5", Span(1, 7, 1, 10)),
        Span(1, 1, 1, 10),
    )


def test_FR003_parenthesized_operand_span_excludes_its_parentheses():
    tree = parse("(a + b) * c")
    assert tree.left.span == Span(1, 2, 1, 7)
    # The parentheses belong to the product's own fragment.
    assert tree.span == Span(1, 1, 1, 12)


def test_FR003_negate_span():
    assert parse("-(a)") == Negate(Name("a", Span(1, 3, 1, 4)), Span(1, 1, 1, 5))
    assert parse("- x") == Negate(Name("x", Span(1, 3, 1, 4)), Span(1, 1, 1, 4))


def test_FR003_component_span():
    assert parse("(p).d") == Component(
        Name("p", Span(1, 2, 1, 3)), "d", Span(1, 1, 1, 6)
    )


def test_FR003_call_span():
    assert parse("hnorm( (p) )") == Call(
        "hnorm", (Name("p", Span(1, 9, 1, 10)),), Span(1, 1, 1, 13)
    )


def test_FR003_multiline_spans():
    assert parse("a\n  <= (b\n + c)") == Compare(
        "<=",
        Name("a", Span(1, 1, 1, 2)),
        Arithmetic(
            "+",
            Name("b", Span(2, 7, 2, 8)),
            Name("c", Span(3, 4, 3, 5)),
            Span(2, 7, 3, 5),
        ),
        Span(1, 1, 3, 6),
    )


# Binding-power table and production coverage.


def test_FR002_binding_powers_follow_the_data_model_table():
    # data-model.md "Pratt binding powers", one row per grammar level, loosest first.
    assert list(BINDING_POWERS.items()) == [
        ("conditional", 10),
        ("implication", 20),
        ("conjunction", 30),
        ("comparison", 40),
        ("additive", 50),
        ("multiplicative", 60),
        ("unary", 70),
        ("postfix", 80),
    ]


def test_SC007_injected_binding_powers_reshape_the_tree():
    swapped = {**BINDING_POWERS, "additive": 60, "multiplicative": 50}
    assert parse("a + b * c", binding_powers=swapped) == Arithmetic(
        "*",
        Arithmetic("+", name("a", 1), name("b", 5), span(1, 6)),
        name("c", 9),
        span(1, 10),
    )
    assert parse("a + b * c") == Arithmetic(
        "+",
        name("a", 1),
        Arithmetic("*", name("b", 5), name("c", 9), span(5, 10)),
        span(1, 10),
    )


def test_SC006_collector_records_grouping_and_built_productions():
    collector = []
    parse("(a + b) * c", collector=collector)
    assert Counter(collector) == {
        "grouping": 1,
        "additive": 1,
        "multiplicative": 1,
        "name": 3,
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1", {"number": 1}),
        ("a", {"name": 1}),
        ("f(a, b)", {"call": 1, "name": 2}),
        ("(a)", {"grouping": 1, "name": 1}),
        ("a.d", {"postfix": 1, "name": 1}),
        ("-a", {"unary": 1, "name": 1}),
        ("a / b", {"multiplicative": 1, "name": 2}),
        ("a - b", {"additive": 1, "name": 2}),
        ("a != b", {"comparison": 1, "name": 2}),
        ("a and b", {"conjunction": 1, "name": 2}),
        ("a implies b", {"implication": 1, "name": 2}),
        ("if a then b else c", {"conditional": 1, "name": 3}),
    ],
)
def test_SC006_collector_names_each_production_once_per_construct(text, expected):
    collector = []
    parse(text, collector=collector)
    assert Counter(collector) == expected


# Parse depth limit (data-model.md): every operand parse but the rule body's
# own opens one level, whatever opens it; level 101 is nesting_too_deep at the
# token that opens it, before Python's recursion limit (1000) is near.

DEPTH_LIMIT = 100


def at(column, fragment):
    return ExpressionLocation(1, column, column + len(fragment), fragment)


def depth_error(text):
    with pytest.raises(RuleSetError) as caught:
        parse(text)
    assert caught.value.diagnostic.code == "nesting_too_deep"
    return caught.value.diagnostic.location


def groups(depth):
    return "(" * depth + "a" + ")" * depth


def negations(depth):
    return "-" * depth + "a"


def calls(depth):
    return "f(" * depth + "a" + ")" * depth


def implications(depth):
    # Right-associative: each right operand nests inside the previous one.
    return " implies ".join(["a"] * (depth + 1))


def conditionals(depth):
    # Each else branch holds the next conditional; its condition is one deeper.
    return "if a then b else " * depth + "c"


NESTINGS = pytest.mark.parametrize(
    ("nest", "opener"),
    [
        (groups, at(101, "(")),
        (negations, at(101, "-")),
        (calls, at(202, "(")),
        (implications, at(1003, "implies")),
        (conditionals, at(1701, "if")),
    ],
    ids=["groups", "negations", "calls", "implications", "conditionals"],
)


@NESTINGS
def test_FR003_depth_100_parses_and_depth_101_is_nesting_too_deep(nest, opener):
    parse(nest(DEPTH_LIMIT))
    assert depth_error(nest(DEPTH_LIMIT + 1)) == opener


@NESTINGS
def test_FR003_nesting_far_past_the_limit_stops_at_level_101(nest, opener):
    assert depth_error(nest(5000)) == opener


def test_FR003_every_opener_shares_one_depth_counter():
    parse("-(" * 50 + "a" + ")" * 50)
    assert depth_error("-(" * 50 + "-a" + ")" * 50) == at(101, "-")


def test_FR003_an_infix_operand_opens_a_level_too():
    parse("(" * 99 + "a < b" + ")" * 99)
    assert depth_error("(" * 100 + "a < b" + ")" * 100) == at(103, "<")


def test_FR003_sibling_operands_do_not_add_up():
    parse("f(" + groups(99) + ", " + groups(99) + ")")
    parse(groups(99) + " and " + groups(98))
