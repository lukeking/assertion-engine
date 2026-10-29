"""Pratt parser for one rule expression (contracts/grammar.ebnf).

A token at the start of an operand runs its prefix handler; an operator after
an operand runs its infix handler while its binding power exceeds the caller's
minimum. BINDING_POWERS has one row per grammar precedence level, loosest
first (data-model.md "Pratt binding powers"); parse accepts a replacement
table. Tokens that are no infix operator (then, else, ",", ")", end of input)
have binding power 0 and end the operand.

Every parse also returns the operand's extent, which includes the parentheses
around a grouped operand: a parent node's span covers them, the grouped
node's own span does not (contracts/syntax-tree.md "Span").
"""

from types import MappingProxyType

from assertion_engine.dsl.errors import Diagnostic, ExpressionLocation, RuleSetError
from assertion_engine.dsl.lexer import Token, tokenize
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
    Node,
    Number,
    Span,
)

BINDING_POWERS = MappingProxyType(
    {
        "conditional": 10,  # prefix "if"; the else branch extends right
        "implication": 20,  # infix, right-associative
        "conjunction": 30,  # infix, left-associative
        "comparison": 40,  # infix, non-associative
        "additive": 50,  # infix, left-associative
        "multiplicative": 60,  # infix, left-associative
        "unary": 70,  # prefix "-"
        "postfix": 80,  # infix ".", left-associative
    }
)

_INFIX_LEVELS = {
    "implies": "implication",
    "and": "conjunction",
    **dict.fromkeys(("<", "<=", ">", ">=", "==", "!="), "comparison"),
    **dict.fromkeys(("+", "-"), "additive"),
    **dict.fromkeys(("*", "/"), "multiplicative"),
    ".": "postfix",
}
_RIGHT_ASSOCIATIVE = frozenset({"implication"})
AXES = frozenset({"n", "e", "d"})

type Position = tuple[int, int]


def parse(text: str, *, binding_powers=BINDING_POWERS, collector=None) -> Node:
    """Parse one expression string into its syntax tree.

    collector, when given, receives append(<grammar production name>) each
    time the parser builds that production's construct, grouping included.
    """
    parser = _Parser(tokenize(text), binding_powers, collector)
    node, _, _ = parser.operand(0)
    token = parser.peek()
    if token.kind != "end_of_input":
        message = f"unexpected {token.text!r} after a complete expression"
        raise _error("trailing_input", token, message)
    return node


class _Parser:
    def __init__(self, tokens: tuple[Token, ...], powers, collector):
        self.tokens = tokens
        self.index = 0
        self.powers = powers
        self.collector = collector

    def peek(self) -> Token:
        return self.tokens[self.index]

    def advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def expect(self, text: str) -> Token:
        token = self.advance()
        if token.text != text:
            raise _unexpected(token)
        return token

    def record(self, production: str):
        if self.collector is not None:
            self.collector.append(production)

    def operand(self, minimum: int) -> tuple[Node, Position, Position]:
        """Parse one operand and every infix operator binding tighter than minimum."""
        node, start, end = self.prefix(self.advance(), minimum)
        while True:
            level = _INFIX_LEVELS.get(self.peek().text)
            if level is None or self.powers[level] <= minimum:
                return node, start, end
            node, end = self.infix(self.advance(), level, node, start)

    def prefix(self, token: Token, minimum: int) -> tuple[Node, Position, Position]:
        start, end = _start(token), _end(token)
        if token.kind == "number":
            self.record("number")
            return Number(token.text, token.span), start, end
        if token.kind == "name":
            if self.peek().text == "(":
                return self.call(token)
            self.record("name")
            return Name(token.text, token.span), start, end
        if token.text == "(":
            node, _, _ = self.operand(0)
            end = _end(self.expect(")"))
            self.record("grouping")
            return node, start, end
        if token.text == "-":
            operand, _, end = self.operand(self.powers["unary"])
            self.record("unary")
            return Negate(operand, Span(*start, *end)), start, end
        # A conditional only starts an expression: the caller's minimum must be
        # below its power, true at the rule body, a group, a call argument or a
        # conditional branch, false inside any operator's operand.
        if token.text == "if" and self.powers["conditional"] > minimum:
            condition, _, _ = self.operand(0)
            self.expect("then")
            then, _, _ = self.operand(0)
            self.expect("else")
            else_, _, end = self.operand(self.powers["conditional"] - 1)
            self.record("conditional")
            return Conditional(condition, then, else_, Span(*start, *end)), start, end
        raise _unexpected(token)

    def call(self, function: Token) -> tuple[Node, Position, Position]:
        self.expect("(")
        arguments = [self.operand(0)[0]]
        while self.peek().text == ",":
            self.advance()
            arguments.append(self.operand(0)[0])
        start, end = _start(function), _end(self.expect(")"))
        self.record("call")
        return Call(function.text, tuple(arguments), Span(*start, *end)), start, end

    def infix(
        self, operator: Token, level: str, left: Node, start: Position
    ) -> tuple[Node, Position]:
        if level == "postfix":
            axis = self.advance()
            if axis.kind != "name":
                raise _unexpected(axis)
            if axis.text not in AXES:
                raise _error("invalid_axis", axis, f"{axis.text!r} is not n, e or d")
            end = _end(axis)
            self.record("postfix")
            return Component(left, axis.text, Span(*start, *end)), end
        power = self.powers[level]
        minimum = power - 1 if level in _RIGHT_ASSOCIATIVE else power
        right, _, end = self.operand(minimum)
        span = Span(*start, *end)
        self.record(level)
        if level == "implication":
            return Implies(left, right, span), end
        if level == "conjunction":
            return And(left, right, span), end
        if level == "comparison":
            return Compare(operator.text, left, right, span), end
        return Arithmetic(operator.text, left, right, span), end


def _start(token: Token) -> Position:
    return token.span.start_line, token.span.start_column


def _end(token: Token) -> Position:
    return token.span.end_line, token.span.end_column


def _error(code: str, token: Token, message: str) -> RuleSetError:
    span = token.span
    location = ExpressionLocation(
        span.start_line, span.start_column, span.end_column, token.text
    )
    return RuleSetError(Diagnostic(code, message, location))


def _unexpected(token: Token) -> RuleSetError:
    if token.kind == "end_of_input":
        return _error("unexpected_end", token, "expression ends too early")
    return _error("unexpected_token", token, f"unexpected {token.text!r}")
