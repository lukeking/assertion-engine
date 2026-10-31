"""ASCII scanner for one rule expression: tokens with 1-based spans.

Follows contracts/grammar.ebnf "Lexical notes". Whitespace (space, tab,
newline) separates tokens and produces none; every other character is one
column, and a newline starts the next line at column 1. The last token is
always end_of_input, an empty span where the text ends.

A number directly followed by a letter, "_" or "." is invalid_number, located
over the whole run of name and number characters it starts (1e3, 2., 2.5.1).
"""

import re
from dataclasses import dataclass

from assertion_engine.dsl.errors import Diagnostic, ExpressionLocation, RuleSetError
from assertion_engine.dsl.syntax import Span

KEYWORDS = frozenset(
    {
        "if",
        "then",
        "else",
        "implies",
        "and",
        "prev",
        "ago",
        "held_for",
        "within",
        "slope",
    }
)
RESERVED_WORDS = frozenset({"or", "not"})

# Two-character operators come first so the longest operator wins.
_TOKEN = re.compile(
    r"""
    (?P<whitespace>[ \t\n]+)
    | (?P<number>[0-9]+(?:\.[0-9]+)?)
    | (?P<word>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<operator><=|>=|==|!=|[-+*/.<>])
    | (?P<punctuation>[(),])
    """,
    re.VERBOSE,
)
# What a well-formed number may not run into.
_NUMBER_TAIL = re.compile(r"[A-Za-z0-9_.]+")


@dataclass(frozen=True)
class Token:
    # number, name, keyword, reserved_word, operator, punctuation or end_of_input
    kind: str
    text: str
    span: Span


def tokenize(text: str) -> tuple[Token, ...]:
    """Scan text left to right; the first character no token accepts is an error."""
    tokens = []
    index, line, column = 0, 1, 1
    while index < len(text):
        match = _TOKEN.match(text, index)
        if match is None:
            location = ExpressionLocation(line, column, column + 1, text[index])
            message = f"character {text[index]!r} is not part of the rule language"
            raise RuleSetError(Diagnostic("invalid_character", message, location))
        lexeme, group = match.group(), match.lastgroup
        index = match.end()
        if group == "number" and (tail := _NUMBER_TAIL.match(text, index)):
            lexeme += tail.group()
            location = ExpressionLocation(line, column, column + len(lexeme), lexeme)
            message = f"{lexeme!r} is not a number: no exponent, digits around '.'"
            raise RuleSetError(Diagnostic("invalid_number", message, location))
        if group == "whitespace":
            if "\n" in lexeme:
                line += lexeme.count("\n")
                column = len(lexeme) - lexeme.rfind("\n")
            else:
                column += len(lexeme)
            continue
        span = Span(line, column, line, column + len(lexeme))
        tokens.append(Token(_kind(group, lexeme), lexeme, span))
        column += len(lexeme)
    tokens.append(Token("end_of_input", "", Span(line, column, line, column)))
    return tuple(tokens)


def _kind(group: str, lexeme: str) -> str:
    if group != "word":
        return group
    if lexeme in KEYWORDS:
        return "keyword"
    if lexeme in RESERVED_WORDS:
        return "reserved_word"
    return "name"
