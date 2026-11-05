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

A temporal keyword is shaped like a call but takes a fixed number of
arguments (grammar `temporal`): its node runs from the keyword to its ")",
and a missing or extra argument is a syntax error, not an arity_mismatch.

The first syntax error stops the parse and points at one token: the
unexpected or reserved token (for a temporal keyword, the token where its
next "," or its ")" was due), a chain's second comparison operator, the "("
left unclosed, or the token that opens nesting level DEPTH_LIMIT + 1. Every
operand parse but the rule body's own opens one level, so the limit bounds
the recursion whatever nests (data-model.md "Parse depth limit"). At the end
of input, and for an empty expression at column 1, the location is one column
wide with an empty fragment.
"""

from types import MappingProxyType

from assertion_engine.dsl.errors import Diagnostic, ExpressionLocation, RuleSetError
from assertion_engine.dsl.lexer import Token, tokenize
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
# keyword: (grammar production, node kind, argument count)
_TEMPORAL = {
    "prev": ("previous", Previous, 1),
    "ago": ("ago", Ago, 2),
    "held_for": ("held_for", HeldFor, 2),
    "within": ("within", Within, 2),
    "slope": ("slope", Slope, 2),
}
AXES = frozenset({"n", "e", "d"})
DEPTH_LIMIT = 100

type Position = tuple[int, int]


def parse(text: str, *, binding_powers=BINDING_POWERS, collector=None) -> Node:
    """Parse one expression string into its syntax tree.

    collector, when given, receives append(<grammar production name>) each
    time the parser builds that production's construct, grouping included.
    """
    parser = _Parser(tokenize(text), binding_powers, collector)
    if parser.peek().kind == "end_of_input":
        location = ExpressionLocation(1, 1, 2, "")
        message = "the expression is empty"
        raise RuleSetError(Diagnostic("empty_expression", message, location))
    node, _, _ = parser.operand(0)
    token = parser.peek()
    if token.kind == "reserved_word":
        raise _unexpected(token)
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
        self.depth = -1  # the rule body's own operand opens no level

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

    def close(self, opening: Token, text: str = ")") -> Token:
        """The ")" for opening, or the "," before its next argument.

        Input that ends first leaves opening unclosed.
        """
        token = self.advance()
        if token.kind == "end_of_input":
            raise _error("unclosed_parenthesis", opening, "'(' is never closed")
        if token.text != text:
            raise _unexpected(token)
        return token

    def record(self, production: str):
        if self.collector is not None:
            self.collector.append(production)

    def operand(self, minimum: int) -> tuple[Node, Position, Position]:
        """Parse one operand and every infix operator binding tighter than minimum.

        The token just consumed (a "(", prefix operator, separator or infix
        operator) opens this operand's nesting level.
        """
        self.depth += 1
        if self.depth > DEPTH_LIMIT:
            message = f"nesting is deeper than {DEPTH_LIMIT} levels"
            raise _error("nesting_too_deep", self.tokens[self.index - 1], message)
        node, start, end = self.prefix(self.advance(), minimum)
        compared = False
        while True:
            operator = self.peek()
            level = _INFIX_LEVELS.get(operator.text)
            if level is None or self.powers[level] <= minimum:
                self.depth -= 1
                return node, start, end
            if compared and level == "comparison":
                message = "comparisons do not chain; join them with 'and'"
                raise _error("chained_comparison", operator, message)
            compared = level == "comparison"
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
        if token.text in _TEMPORAL:
            return self.temporal(token)
        if token.text == "(":
            node, _, _ = self.operand(0)
            end = _end(self.close(token))
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
        opening = self.expect("(")
        arguments = [self.operand(0)[0]]
        while self.peek().text == ",":
            self.advance()
            arguments.append(self.operand(0)[0])
        start, end = _start(function), _end(self.close(opening))
        self.record("call")
        return Call(function.text, tuple(arguments), Span(*start, *end)), start, end

    def temporal(self, keyword: Token) -> tuple[Node, Position, Position]:
        production, kind, count = _TEMPORAL[keyword.text]
        opening = self.expect("(")
        arguments = [self.operand(0)[0]]
        for _ in range(count - 1):
            self.close(opening, ",")
            arguments.append(self.operand(0)[0])
        start, end = _start(keyword), _end(self.close(opening))
        self.record(production)
        return kind(*arguments, Span(*start, *end)), start, end

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
    """A diagnostic at token; end of input is the one column past the text."""
    span = token.span
    end_column = span.end_column
    if token.kind == "end_of_input":
        end_column = span.start_column + 1
    location = ExpressionLocation(
        span.start_line, span.start_column, end_column, token.text
    )
    return RuleSetError(Diagnostic(code, message, location))


def _unexpected(token: Token) -> RuleSetError:
    if token.kind == "end_of_input":
        return _error("unexpected_end", token, "expression ends too early")
    if token.kind == "reserved_word":
        message = f"{token.text!r} is reserved and not part of the M1 grammar"
        return _error("reserved_word", token, message)
    return _error("unexpected_token", token, f"unexpected {token.text!r}")
