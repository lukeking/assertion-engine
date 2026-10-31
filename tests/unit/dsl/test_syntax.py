"""FR-003/FR-012: immutable syntax nodes and their syntax-tree.md documents."""

import typing
from dataclasses import FrozenInstanceError, fields

import pytest

from assertion_engine.artifacts import canonical_bytes
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
    Node,
    Number,
    Previous,
    Slope,
    Span,
    Within,
    to_document,
)

KINDS = {
    "Number",
    "Name",
    "Component",
    "Negate",
    "Arithmetic",
    "Compare",
    "And",
    "Implies",
    "Conditional",
    "Call",
    "Previous",
    "Ago",
    "HeldFor",
    "Within",
    "Slope",
}

# Leaves and their documents are written out by hand, never produced by to_document.
A = Name("a", Span(1, 1, 1, 2))
B = Name("b", Span(1, 5, 1, 6))
C = Name("c", Span(1, 9, 1, 10))
A_DOC = {"kind": "Name", "name": "a", "span": [1, 1, 1, 2]}
B_DOC = {"kind": "Name", "name": "b", "span": [1, 5, 1, 6]}
C_DOC = {"kind": "Name", "name": "c", "span": [1, 9, 1, 10]}
WHOLE = Span(1, 1, 1, 10)
WHOLE_DOC = [1, 1, 1, 10]

CASES = [
    (
        Number("0.5", Span(1, 1, 1, 4)),
        {"kind": "Number", "span": [1, 1, 1, 4], "text": "0.5"},
    ),
    (A, A_DOC),
    (
        Component(A, "d", Span(1, 1, 1, 4)),
        {"kind": "Component", "span": [1, 1, 1, 4], "target": A_DOC, "axis": "d"},
    ),
    (Negate(B, WHOLE), {"kind": "Negate", "span": WHOLE_DOC, "operand": B_DOC}),
    (
        Arithmetic("-", A, B, WHOLE),
        {
            "kind": "Arithmetic",
            "span": WHOLE_DOC,
            "op": "-",
            "left": A_DOC,
            "right": B_DOC,
        },
    ),
    (
        Compare("<=", A, B, WHOLE),
        {
            "kind": "Compare",
            "span": WHOLE_DOC,
            "op": "<=",
            "left": A_DOC,
            "right": B_DOC,
        },
    ),
    (
        And(A, B, WHOLE),
        {"kind": "And", "span": WHOLE_DOC, "left": A_DOC, "right": B_DOC},
    ),
    (
        Implies(A, B, WHOLE),
        {
            "kind": "Implies",
            "span": WHOLE_DOC,
            "antecedent": A_DOC,
            "consequent": B_DOC,
        },
    ),
    (
        Conditional(A, B, C, WHOLE),
        {
            "kind": "Conditional",
            "span": WHOLE_DOC,
            "condition": A_DOC,
            "then": B_DOC,
            "else": C_DOC,
        },
    ),
    (
        Call("norm", (A, B), WHOLE),
        {
            "kind": "Call",
            "span": WHOLE_DOC,
            "function": "norm",
            "arguments": [A_DOC, B_DOC],
        },
    ),
    (Previous(A, WHOLE), {"kind": "Previous", "span": WHOLE_DOC, "value": A_DOC}),
    (
        Ago(A, B, WHOLE),
        {"kind": "Ago", "span": WHOLE_DOC, "value": A_DOC, "duration": B_DOC},
    ),
    (
        HeldFor(A, B, WHOLE),
        {"kind": "HeldFor", "span": WHOLE_DOC, "condition": A_DOC, "duration": B_DOC},
    ),
    (
        Within(A, B, WHOLE),
        {"kind": "Within", "span": WHOLE_DOC, "condition": A_DOC, "duration": B_DOC},
    ),
    (
        Slope(A, B, WHOLE),
        {"kind": "Slope", "span": WHOLE_DOC, "value": A_DOC, "window": B_DOC},
    ),
]
CASE_IDS = [document["kind"] for _, document in CASES]


def test_FR003_cases_cover_exactly_the_15_contract_kinds():
    assert len(CASES) == 15
    assert set(CASE_IDS) == KINDS
    assert {cls.__name__ for cls in typing.get_args(Node.__value__)} == KINDS


@pytest.mark.parametrize(("node", "expected"), CASES, ids=CASE_IDS)
def test_FR012_to_document_emits_contract_fields(node, expected):
    assert to_document(node) == expected


@pytest.mark.parametrize(("node", "expected"), CASES, ids=CASE_IDS)
def test_FR003_nodes_are_frozen_and_hashable(node, expected):
    for field in fields(node):
        with pytest.raises(FrozenInstanceError):
            setattr(node, field.name, None)
    # Hashing walks every child, so a mutable child container fails here.
    hash(node)


def test_FR003_call_arguments_become_an_immutable_tuple():
    arguments = [A, B]
    call = Call("norm", arguments, WHOLE)
    arguments.append(C)
    assert call.arguments == (A, B)
    hash(call)


def test_FR012_nodes_compare_by_value():
    def tree():
        # a < 1 implies held_for(c, 2)
        return Implies(
            Compare(
                "<",
                Name("a", Span(1, 1, 1, 2)),
                Number("1", Span(1, 5, 1, 6)),
                Span(1, 1, 1, 6),
            ),
            HeldFor(
                Name("c", Span(1, 24, 1, 25)),
                Number("2", Span(1, 27, 1, 28)),
                Span(1, 15, 1, 29),
            ),
            Span(1, 1, 1, 29),
        )

    first, second = tree(), tree()
    assert first is not second
    assert first == second
    assert hash(first) == hash(second)
    assert Name("a", Span(1, 1, 1, 2)) != Name("a", Span(1, 2, 1, 3))
    # Same field names and values, different kind.
    assert HeldFor(A, B, WHOLE) != Within(A, B, WHOLE)


@pytest.mark.parametrize(
    "positions",
    [(1, 1, 1, 1), (1, 3, 1, 8), (1, 9, 2, 1), (2, 4, 3, 2)],
    ids=["empty", "one-line", "later-line-smaller-column", "multi-line"],
)
def test_FR003_span_start_not_after_end_in_line_column_order(positions):
    span = Span(*positions)
    assert (
        span.start_line,
        span.start_column,
        span.end_line,
        span.end_column,
    ) == positions


@pytest.mark.parametrize(
    "positions",
    [(1, 5, 1, 4), (2, 1, 1, 9)],
    ids=["end-column-before-start", "end-line-before-start"],
)
def test_FR003_span_rejects_end_before_start(positions):
    with pytest.raises(ValueError, match="span"):
        Span(*positions)


def test_FR012_contract_example_canonical_bytes():
    # contracts/syntax-tree.md "Example": battery_percent >= battery_floor_percent
    tree = Compare(
        ">=",
        Name("battery_percent", Span(1, 1, 1, 16)),
        Name("battery_floor_percent", Span(1, 20, 1, 41)),
        Span(1, 1, 1, 41),
    )
    assert canonical_bytes({"rule": "battery-floor", "tree": to_document(tree)}) == (
        b'{"rule":"battery-floor","tree":{"kind":"Compare","left":{"kind":"Name",'
        b'"name":"battery_percent","span":[1,1,1,16]},"op":">=","right":{"kind":"Name",'
        b'"name":"battery_floor_percent","span":[1,20,1,41]},"span":[1,1,1,41]}}\n'
    )


def test_FR012_number_text_is_not_quantized():
    # canonical_bytes rounds JSON numbers to 6 places; 0.0000005 would become 0.
    number = Number("0.0000005", Span(1, 1, 1, 10))
    assert canonical_bytes(to_document(number)) == (
        b'{"kind":"Number","span":[1,1,1,10],"text":"0.0000005"}\n'
    )
