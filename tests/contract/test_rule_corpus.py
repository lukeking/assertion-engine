"""FR-001: the corpus rule set names the same rules as the plain-language corpus."""

import re
import tomllib
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "rules" / "corpus.toml"
PLAIN_CORPUS = REPO_ROOT / "specs" / "002-rule-dsl-parser" / "rule-corpus.md"
SECTION_CATEGORIES = {
    "門檻比較": "threshold",
    "邏輯組合": "logic",
    "時序約束": "temporal",
    "趨勢外推": "trend",
}


def load_corpus() -> dict:
    assert CORPUS.is_file(), f"missing {CORPUS.relative_to(REPO_ROOT)}"
    return tomllib.loads(CORPUS.read_text(encoding="utf-8"))


def plain_corpus_categories() -> dict[str, str]:
    """Map each ### `short-name` heading to the category of its ## section."""
    categories = {}
    category = None
    for line in PLAIN_CORPUS.read_text(encoding="utf-8").splitlines():
        if section := re.fullmatch(r"## (.+)（\d+）", line):
            category = SECTION_CATEGORIES[section.group(1)]
        elif heading := re.fullmatch(r"### `([^`]+)`", line):
            categories[heading.group(1)] = category
    return categories


def test_FR001_corpus_short_names_match_plain_corpus():
    assert set(load_corpus()["rules"]) == set(plain_corpus_categories())


def test_FR001_corpus_category_counts():
    rules = load_corpus()["rules"]
    assert Counter(rule["category"] for rule in rules.values()) == {
        "threshold": 4,
        "logic": 3,
        "temporal": 6,
        "trend": 4,
    }


def test_FR001_corpus_categories_follow_plain_corpus_sections():
    rules = load_corpus()["rules"]
    assert {
        name: rule["category"] for name, rule in rules.items()
    } == plain_corpus_categories()


def test_FR001_corpus_declares_one_derived_and_27_parameters():
    corpus = load_corpus()
    assert list(corpus["derived"]) == ["return_time_s"]
    assert len(corpus["parameters"]) == 27
