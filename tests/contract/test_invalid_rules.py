"""SC-005: every invalid rule set is rejected at its recorded code and location.

tests/fixtures/invalid_rules.toml holds the cases (data-model.md "Regression
suite files"); their expected locations are counted by hand there. An
`expression` case becomes rule `case` of MINIMAL_RULE_SET, a `ruleset` case is
loaded as written. Every case must raise: nothing is returned, so no rule set
and no tree is produced.
"""

import tomllib
from collections import Counter
from pathlib import Path

import pytest

from assertion_engine.dsl import RuleSetError, load_ruleset
from assertion_engine.dsl.errors import CODES, ExpressionLocation, FileLocation

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "invalid_rules.toml"
CASES = tomllib.loads(FIXTURE.read_text(encoding="utf-8"))["case"]

# One parameter per unit the expression cases need; the rule is named `case`.
MINIMAL_RULE_SET = """\
schema_version = "1.0.0"

[parameters.count]
unit = "1"

[parameters.limit_percent]
unit = "%"

[parameters.limit_m]
unit = "m"

[parameters.limit_s]
unit = "s"

[parameters.limit_mps]
unit = "m/s"

[rules.case]
category = "logic"
expression = {expression}
"""
EXPRESSION_LOCATION = {"line", "column", "end_column", "fragment"}
FILE_LOCATION = {"file_line", "file_column"}


def toml_string(text):
    """text as a TOML basic string: quotes, backslashes and controls escaped."""
    escaped = []
    for character in text:
        if character in '"\\':
            escaped.append("\\" + character)
        elif ord(character) < 0x20 or character == "\x7f":
            escaped.append(f"\\u{ord(character):04x}")
        else:
            escaped.append(character)
    return '"' + "".join(escaped) + '"'


def embedded(expression):
    return MINIMAL_RULE_SET.format(expression=toml_string(expression))


def rule_set_text(case):
    if "expression" in case:
        return embedded(case["expression"])
    return case["ruleset"]


def expected_location(case):
    if "file_line" in case:
        return FileLocation(case["file_line"], case["file_column"])
    if "expression" in case:
        owner = {"rule": "case"}
    else:
        owner = {key: case[key] for key in ("rule", "derived") if key in case}
    return ExpressionLocation(
        case["line"], case["column"], case["end_column"], case["fragment"], **owner
    )


def case_ids():
    """Parameter IDs are the code, numbered within it: unexpected_end-2."""
    seen = Counter()
    for case in CASES:
        seen[case["code"]] += 1
        yield f"{case['code']}-{seen[case['code']]}"


CASE_IDS = list(case_ids())
EXPRESSION_CASES = [
    pytest.param(case, id=case_id)
    for case, case_id in zip(CASES, CASE_IDS)
    if "expression" in case
]


def test_SC005_fixture_has_two_cases_for_every_code_but_nonpositive_duration():
    counts = Counter(case["code"] for case in CASES)
    assert set(counts) == set(CODES) - {"nonpositive_duration"}
    assert min(counts.values()) >= 2


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_SC005_fixture_case_has_one_source_and_one_location_kind(case):
    keys = set(case) - {"code"}
    assert len(keys & {"expression", "ruleset"}) == 1
    location = keys - {"expression", "ruleset"}
    owner = location & {"rule", "derived"}
    if location - owner == FILE_LOCATION:
        assert not owner
    else:
        assert location - owner == EXPRESSION_LOCATION
        # A ruleset case names its owner; an expression case is rule `case`.
        assert len(owner) == ("ruleset" in case)


@pytest.mark.parametrize("case", EXPRESSION_CASES)
def test_SC005_embedding_keeps_the_expression_text(case):
    document = tomllib.loads(embedded(case["expression"]))
    assert document["rules"]["case"]["expression"] == case["expression"]


def test_SC005_minimal_rule_set_loads_with_a_valid_expression():
    expression = (
        "battery_percent >= limit_percent and altitude_m < limit_m"
        " and mission_time_s < limit_s and descent_speed_mps < limit_mps"
        " and sequence_number > count"
    )
    ruleset = load_ruleset(embedded(expression).encode("utf-8"))
    assert list(ruleset.rules) == ["case"]
    assert ruleset.rules["case"].expression == expression


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_SC005_invalid_case_is_rejected_at_its_code_and_location(case):
    with pytest.raises(RuleSetError) as caught:
        load_ruleset(rule_set_text(case).encode("utf-8"))
    diagnostic = caught.value.diagnostic
    assert diagnostic.code == case["code"]
    assert diagnostic.location == expected_location(case)
