"""FR-003/FR-004: ASCII tokens with 1-based spans, per grammar.ebnf "Lexical notes"."""

import pytest

from assertion_engine.dsl.lexer import Token, tokenize
from assertion_engine.dsl.syntax import Span

# grammar.ebnf "Lexical notes", copied literally.
KEYWORDS = (
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
)
RESERVED_WORDS = ("or", "not")
SYMBOLS = [
    ("+", "operator"),
    ("-", "operator"),
    ("*", "operator"),
    ("/", "operator"),
    (".", "operator"),
    ("<", "operator"),
    ("<=", "operator"),
    (">", "operator"),
    (">=", "operator"),
    ("==", "operator"),
    ("!=", "operator"),
    ("(", "punctuation"),
    (")", "punctuation"),
    (",", "punctuation"),
]


def token(kind, text, column):
    """A one-line token whose span starts at column."""
    return Token(kind, text, Span(1, column, 1, column + len(text)))


def end(column, line=1):
    return Token("end_of_input", "", Span(line, column, line, column))


def kinds(text):
    return [token.kind for token in tokenize(text)]


def test_FR003_integer_and_decimal_numbers():
    assert list(tokenize("7 0.5 120.25")) == [
        token("number", "7", 1),
        token("number", "0.5", 3),
        token("number", "120.25", 7),
        end(13),
    ]


def test_FR003_names():
    assert list(tokenize("battery_percent _tmp a1 B2")) == [
        token("name", "battery_percent", 1),
        token("name", "_tmp", 17),
        token("name", "a1", 22),
        token("name", "B2", 25),
        end(27),
    ]


def test_FR003_contract_lists_ten_keywords():
    assert len(KEYWORDS) == 10


@pytest.mark.parametrize("word", KEYWORDS)
def test_FR003_keywords_are_keyword_tokens(word):
    assert list(tokenize(word)) == [token("keyword", word, 1), end(1 + len(word))]


@pytest.mark.parametrize("word", RESERVED_WORDS)
def test_FR004_or_and_not_are_reserved_words(word):
    assert list(tokenize(word)) == [
        token("reserved_word", word, 1),
        end(1 + len(word)),
    ]


def test_FR003_words_that_only_start_with_a_keyword_are_names():
    text = "iffy andy prevalent orbit nothing then_ held_for2 n1 dd"
    assert kinds(text) == ["name"] * 9 + ["end_of_input"]


@pytest.mark.parametrize(("symbol", "kind"), SYMBOLS, ids=[s for s, _ in SYMBOLS])
def test_FR003_operator_and_punctuation_kinds(symbol, kind):
    assert list(tokenize(symbol)) == [token(kind, symbol, 1), end(1 + len(symbol))]


def test_FR003_adjacent_symbols_take_the_longest_operator():
    assert list(tokenize("(a<=b,c>=d)==e!=-f.n*2/3+0.5<g>h")) == [
        token("punctuation", "(", 1),
        token("name", "a", 2),
        token("operator", "<=", 3),
        token("name", "b", 5),
        token("punctuation", ",", 6),
        token("name", "c", 7),
        token("operator", ">=", 8),
        token("name", "d", 10),
        token("punctuation", ")", 11),
        token("operator", "==", 12),
        token("name", "e", 14),
        token("operator", "!=", 15),
        token("operator", "-", 17),
        token("name", "f", 18),
        token("operator", ".", 19),
        token("name", "n", 20),
        token("operator", "*", 21),
        token("number", "2", 22),
        token("operator", "/", 23),
        token("number", "3", 24),
        token("operator", "+", 25),
        token("number", "0.5", 26),
        token("operator", "<", 29),
        token("name", "g", 30),
        token("operator", ">", 31),
        token("name", "h", 32),
        end(33),
    ]


def test_FR003_multiline_expression_lines_and_columns():
    # A tab is one column; a newline starts the next line at column 1.
    assert list(tokenize("a <=\n  (b)\n\tc")) == [
        Token("name", "a", Span(1, 1, 1, 2)),
        Token("operator", "<=", Span(1, 3, 1, 5)),
        Token("punctuation", "(", Span(2, 3, 2, 4)),
        Token("name", "b", Span(2, 4, 2, 5)),
        Token("punctuation", ")", Span(2, 5, 2, 6)),
        Token("name", "c", Span(3, 2, 3, 3)),
        Token("end_of_input", "", Span(3, 3, 3, 3)),
    ]


def test_FR003_axis_letters_are_ordinary_names():
    assert list(tokenize("n e d")) == [
        token("name", "n", 1),
        token("name", "e", 3),
        token("name", "d", 5),
        end(6),
    ]
    assert list(tokenize("position_ned_m.d")) == [
        token("name", "position_ned_m", 1),
        token("operator", ".", 15),
        token("name", "d", 16),
        end(17),
    ]


def test_FR003_whitespace_produces_no_tokens():
    tokens = tokenize(" \t\n  x \n\t ")
    assert [token.kind for token in tokens] == ["name", "end_of_input"]
    assert tokens[0] == Token("name", "x", Span(2, 3, 2, 4))
    assert kinds("") == ["end_of_input"]
    assert kinds(" \n\t") == ["end_of_input"]
