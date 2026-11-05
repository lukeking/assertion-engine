"""FR-015: docs/glossary.md has an entry for every node kind and name origin,
and its field table, derived table and unit list match the code.

An entry is a ### heading that names its code identifiers in inline code, as in
### 蘊涵（`Implies`）. The node kinds come from syntax.Node and the origins from
what the checker resolves the corpus's names to, so a kind or origin added
later fails here until the glossary has an entry for it.
"""

import re
from dataclasses import fields
from pathlib import Path
from typing import get_args

from assertion_engine.dsl.ruleset import load_ruleset
from assertion_engine.dsl.syntax import Name, Node, Span
from assertion_engine.dsl.units import UNITS
from assertion_engine.dsl.vocabulary import BUILT_IN_DERIVED, FIELDS

REPO_ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = REPO_ROOT / "docs" / "glossary.md"
CORPUS = REPO_ROOT / "rules" / "corpus.toml"


def glossary_identifiers() -> set[str]:
    """Every inline-code identifier in the glossary's ### headings."""
    identifiers = set()
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if heading := re.fullmatch(r"### (.+)", line):
            identifiers.update(re.findall(r"`([^`]+)`", heading.group(1)))
    return identifiers


def walk(node):
    """Every node of a tree, parents before children."""
    yield node
    for field in fields(node):
        value = getattr(node, field.name)
        for child in value if isinstance(value, tuple) else (value,):
            if not isinstance(child, (str, Span)):
                yield from walk(child)


def corpus_origins() -> set[str]:
    """What the checker resolved each Name of the corpus's trees to."""
    ruleset = load_ruleset(CORPUS.read_bytes())
    checked = [rule.annotations for rule in ruleset.rules.values()]
    checked += ruleset.scope.derived.values()  # built-in and the corpus's own
    return {
        annotations.resolution_of(node)
        for annotations in checked
        for node in walk(annotations.tree)
        if isinstance(node, Name)
    }


def test_FR015_corpus_names_resolve_to_the_three_origins():
    # Guards the next test: an empty derivation would pass it vacuously.
    assert corpus_origins() == {"field", "parameter", "derived"}


def test_FR015_every_node_kind_has_a_glossary_entry():
    kinds = {kind.__name__ for kind in get_args(Node.__value__)}
    assert sorted(kinds - glossary_identifiers()) == []


def test_FR015_every_name_origin_has_a_glossary_entry():
    assert sorted(corpus_origins() - glossary_identifiers()) == []


def table_rows(heading: str) -> list[list[str]]:
    """The cells of the table rows under one ### heading, backticks stripped.

    A row counts when its first cell is inline code, so the header and the
    |---| line are skipped; a renamed heading yields no rows and fails below.
    """
    rows, inside = [], False
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            inside = line == heading
        elif inside and line.startswith("| `"):
            rows.append(
                [cell.strip().strip("`") for cell in line.strip("|").split("|")]
            )
    return rows


def test_FR015_field_table_matches_the_vocabulary():
    rows = table_rows("### 欄位（`field`）")
    assert {row[0]: row[1] for row in rows} == {
        name: f"{kind}[{unit}]" for name, (kind, unit) in FIELDS.items()
    }


def test_FR015_derived_table_matches_the_vocabulary():
    rows = table_rows("### 衍生量（`derived`）")
    assert {row[0]: (row[1], row[2]) for row in rows} == dict(BUILT_IN_DERIVED)


def test_FR015_unit_list_matches_the_declarable_units():
    lines = [
        line
        for line in GLOSSARY.read_text(encoding="utf-8").splitlines()
        if line.startswith("- 本專案的單位只有這些：")
    ]
    assert len(lines) == 1
    assert set(re.findall(r"`([^`]+)`", lines[0])) == set(UNITS)
