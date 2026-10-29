"""Immutable syntax-tree nodes and their contracts/syntax-tree.md documents.

A node's kind is its class name. to_document builds the plain contract document;
assertion_engine.artifacts.canonical_bytes turns that document into golden bytes.
"""

from dataclasses import dataclass, fields

type Node = (
    Number
    | Name
    | Component
    | Negate
    | Arithmetic
    | Compare
    | And
    | Implies
    | Conditional
    | Call
    | Previous
    | Ago
    | HeldFor
    | Within
    | Slope
)


@dataclass(frozen=True)
class Span:
    """1-based positions within one expression string; end_column is exclusive."""

    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def __post_init__(self):
        if (self.start_line, self.start_column) > (self.end_line, self.end_column):
            raise ValueError("span start must not follow its end")


@dataclass(frozen=True)
class Number:
    # Source text, not a number: canonical_bytes rounds JSON numbers to 6 places.
    text: str
    span: Span


@dataclass(frozen=True)
class Name:
    name: str
    span: Span


@dataclass(frozen=True)
class Component:
    target: Node
    axis: str
    span: Span


@dataclass(frozen=True)
class Negate:
    operand: Node
    span: Span


@dataclass(frozen=True)
class Arithmetic:
    op: str
    left: Node
    right: Node
    span: Span


@dataclass(frozen=True)
class Compare:
    op: str
    left: Node
    right: Node
    span: Span


@dataclass(frozen=True)
class And:
    left: Node
    right: Node
    span: Span


@dataclass(frozen=True)
class Implies:
    antecedent: Node
    consequent: Node
    span: Span


@dataclass(frozen=True)
class Conditional:
    condition: Node
    then: Node
    else_: Node  # document key "else"; else is a Python keyword
    span: Span


@dataclass(frozen=True)
class Call:
    function: str
    arguments: tuple[Node, ...]
    span: Span

    def __post_init__(self):
        object.__setattr__(self, "arguments", tuple(self.arguments))


@dataclass(frozen=True)
class Previous:
    value: Node
    span: Span


@dataclass(frozen=True)
class Ago:
    value: Node
    duration: Node
    span: Span


@dataclass(frozen=True)
class HeldFor:
    condition: Node
    duration: Node
    span: Span


@dataclass(frozen=True)
class Within:
    condition: Node
    duration: Node
    span: Span


@dataclass(frozen=True)
class Slope:
    value: Node
    window: Node
    span: Span


_DOCUMENT_KEYS = {"else_": "else"}


def _document_value(value):
    if isinstance(value, Span):
        return [value.start_line, value.start_column, value.end_line, value.end_column]
    if isinstance(value, tuple):
        return [to_document(item) for item in value]
    if isinstance(value, str):
        return value
    return to_document(value)


def to_document(node: Node) -> dict:
    """Return the node's contract document: kind, span and its fields, recursively."""
    document = {"kind": type(node).__name__}
    for field in fields(node):
        key = _DOCUMENT_KEYS.get(field.name, field.name)
        document[key] = _document_value(getattr(node, field.name))
    return document
