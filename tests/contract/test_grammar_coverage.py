"""SC-006/FR-002: the parser exercises exactly the grammar's annotated productions.

Expected values are read from contracts/grammar.ebnf, never from parser.py:
the productions whose annotation carries `used by:`, the header's structural
productions and its precedence levels. Only what the parser records or holds
is compared with them.
"""

import re
import tomllib
from pathlib import Path

from assertion_engine.dsl.parser import BINDING_POWERS, parse

REPO_ROOT = Path(__file__).resolve().parents[2]
GRAMMAR = REPO_ROOT / "specs" / "002-rule-dsl-parser" / "contracts" / "grammar.ebnf"
CORPUS = REPO_ROOT / "rules" / "corpus.toml"

# contracts/ruleset.md "Built-in vocabulary", built-in derived quantities table,
# copied literally as in test_rule_trees.py (test_checker.py pins vocabulary.py
# to it).
BUILT_IN_DEFINITIONS = {
    "altitude_m": "-position_ned_m.d",
    "descent_speed_mps": "velocity_ned_mps.d",
    "horizontal_speed_mps": "hnorm(velocity_ned_mps)",
    "home_distance_m": "hnorm(position_ned_m)",
}

# The `used by:` entry that stands for all 17 corpus rules.
EVERY_CORPUS_RULE = "every corpus rule"

_SPACE = re.compile(r"\s*")
_PRODUCTION = re.compile(r'([a-z_]+)\s*=(?:"[^"]*"|[^";])*;')


def grammar_items() -> list[tuple[str, str]]:
    """grammar.ebnf's top-level items in file order.

    An item is ("comment", body) or ("production", name). A comment body keeps
    the file's columns: the text before "(*" on its line becomes spaces.
    """
    text = GRAMMAR.read_text(encoding="utf-8")
    items, position = [], 0
    while (position := _SPACE.match(text, position).end()) < len(text):
        if text.startswith("(*", position):
            end = text.index("*)", position)
            line_start = text.rfind("\n", 0, position) + 1
            body = " " * (position + 2 - line_start) + text[position + 2 : end]
            items.append(("comment", body))
            position = end + 2
            continue
        match = _PRODUCTION.match(text, position)
        assert match, f"grammar.ebnf: no production at {text[position:][:40]!r}"
        items.append(("production", match.group(1)))
        position = match.end()
    return items


def annotations() -> dict[str, str | None]:
    """Each production's annotation block, None when it has none.

    The block is the comment right after the production that starts with
    `builds:`; a "(* level N *)" heading or an axis note is no annotation.
    """
    items = grammar_items()
    blocks = {}
    for (kind, value), following in zip(items, [*items[1:], ("end", "")]):
        if kind != "production":
            continue
        comment = following[1] if following[0] == "comment" else ""
        blocks[value] = comment if comment.lstrip().startswith("builds:") else None
    return blocks


def used_by(block: str | None) -> list[str] | None:
    """The `used by:` entries of one annotation block, None without the field.

    The list runs on while the following lines are indented past the label,
    so a wrapped list continues and the block's prose after it does not. A
    parenthesized note after an entry ("no-sudden-jump (norm)") is dropped.
    """
    if block is None:
        return None
    lines = block.splitlines()
    for index, line in enumerate(lines):
        column = line.find("used by:")
        if column < 0:
            continue
        text = [line[column + len("used by:") :]]
        for following in lines[index + 1 :]:
            if len(following) - len(following.lstrip()) <= column:
                break
            text.append(following)
        return [
            re.sub(r"\s*\(.*\)$", "", entry.strip())
            for entry in " ".join(text).split(",")
        ]
    return None


def annotated_productions() -> dict[str, list[str]]:
    return {
        production: entries
        for production, block in annotations().items()
        if (entries := used_by(block)) is not None
    }


def header() -> str:
    kind, body = grammar_items()[0]
    assert kind == "comment", "grammar.ebnf must open with its header comment"
    return body


def structural_productions() -> list[str]:
    # "The other 8 (rule_body, expression, ...) are structural"
    match = re.search(r"The other (\d+) \(([^)]*)\)", header())
    assert match, "grammar.ebnf header names no structural productions"
    names = [name.strip() for name in match.group(2).split(",")]
    assert len(names) == int(match.group(1))
    return names


def grammar_levels() -> list[str]:
    # "Precedence levels, loosest first ... 1 conditional   2 implication ..."
    listing = header().split("Precedence levels", 1)[1]
    numbered = re.findall(r"(\d+) ([a-z_]+)", listing)
    assert [int(number) for number, _ in numbered] == list(
        range(1, len(numbered) + 1)
    ), f"grammar.ebnf levels are not numbered 1..n: {numbered}"
    return [level for _, level in numbered]


def load_corpus() -> dict:
    return tomllib.loads(CORPUS.read_text(encoding="utf-8"))


def test_SC006_grammar_annotates_seventeen_productions_and_eight_structural():
    # Header: exactly 17 productions carry `used by:`; the other 8 are named.
    annotated = annotated_productions()
    assert len(annotated) == 17, f"annotated: {sorted(annotated)}"
    assert sorted(set(annotations()) - set(annotated)) == sorted(
        structural_productions()
    )


def test_SC006_parsing_the_corpus_records_exactly_the_annotated_productions():
    corpus = load_corpus()
    derived = {name: entry["expression"] for name, entry in corpus["derived"].items()}
    rules = {name: entry["expression"] for name, entry in corpus["rules"].items()}
    # The 4 built-in derived definitions, return_time_s and the 17 rules.
    assert (len(BUILT_IN_DEFINITIONS), list(derived), len(rules)) == (
        4,
        ["return_time_s"],
        17,
    )
    collector = []
    for text in [*BUILT_IN_DEFINITIONS.values(), *derived.values(), *rules.values()]:
        parse(text, collector=collector)
    recorded, annotated = set(collector), set(annotated_productions())
    assert recorded == annotated, (
        f"recorded but not annotated: {sorted(recorded - annotated)}; "
        f"annotated but not recorded: {sorted(annotated - recorded)}"
    )


def test_FR002_binding_powers_list_the_grammar_levels_in_order():
    # One table row per grammar level, in the header's order, loosest first:
    # the powers rise strictly down the table.
    levels = grammar_levels()
    assert len(levels) == 8, levels
    assert list(BINDING_POWERS) == levels
    powers = list(BINDING_POWERS.values())
    assert all(low < high for low, high in zip(powers, powers[1:])), (
        f"binding powers do not rise down the table: {dict(BINDING_POWERS)}"
    )


def test_FR002_used_by_names_are_corpus_rules_or_derived_quantities():
    corpus = load_corpus()
    known = {
        EVERY_CORPUS_RULE,
        *corpus["rules"],
        *corpus["derived"],
        *BUILT_IN_DEFINITIONS,
    }
    unknown = {
        production: [name for name in entries if name not in known]
        for production, entries in annotated_productions().items()
    }
    assert {production: names for production, names in unknown.items() if names} == {}
