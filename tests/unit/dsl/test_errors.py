"""FR-011: the closed diagnostic vocabulary and the single-error rule-set failure."""

from dataclasses import FrozenInstanceError

import pytest

from assertion_engine.dsl.errors import (
    CODES,
    Diagnostic,
    ExpressionLocation,
    FileLocation,
    RuleSetError,
)

# data-model.md "Diagnostic codes (closed list)", copied literally.
DATA_MODEL_CODES = {
    "invalid_character",
    "invalid_number",
    "empty_expression",
    "unexpected_token",
    "unexpected_end",
    "unclosed_parenthesis",
    "trailing_input",
    "chained_comparison",
    "reserved_word",
    "invalid_axis",
    "nesting_too_deep",
    "invalid_ruleset",
    "unknown_unit",
    "name_conflict",
    "unknown_name",
    "arity_mismatch",
    "type_mismatch",
    "dimension_mismatch",
    "not_boolean_rule",
    "nonpositive_duration",
    "derived_unit_mismatch",
    "derived_cycle",
}


def test_FR011_codes_equal_the_22_data_model_codes():
    assert len(DATA_MODEL_CODES) == 22
    assert len(CODES) == 22
    assert set(CODES) == DATA_MODEL_CODES


def test_FR011_diagnostic_with_rule_expression_location():
    location = ExpressionLocation(
        line=1, column=17, end_column=19, fragment=">=", rule="battery-floor"
    )
    diagnostic = Diagnostic("unexpected_token", "expected an operand", location)
    assert (diagnostic.code, diagnostic.message) == (
        "unexpected_token",
        "expected an operand",
    )
    assert diagnostic.location is location
    assert (
        location.rule,
        location.derived,
        location.line,
        location.column,
        location.end_column,
        location.fragment,
    ) == ("battery-floor", None, 1, 17, 19, ">=")


def test_FR011_diagnostic_with_derived_expression_location():
    location = ExpressionLocation(
        line=2, column=3, end_column=13, fragment="altitude_m", derived="return_time_s"
    )
    diagnostic = Diagnostic("derived_unit_mismatch", "declared s, got m", location)
    assert (location.rule, location.derived) == (None, "return_time_s")
    assert (location.line, location.column, location.end_column) == (2, 3, 13)
    assert diagnostic.location.fragment == "altitude_m"


def test_FR011_diagnostic_with_file_location():
    location = FileLocation(file_line=4, file_column=12)
    diagnostic = Diagnostic("invalid_ruleset", "invalid TOML", location)
    assert (diagnostic.code, diagnostic.message) == ("invalid_ruleset", "invalid TOML")
    assert (diagnostic.location.file_line, diagnostic.location.file_column) == (4, 12)


@pytest.mark.parametrize(
    "owners",
    [{}, {"rule": "battery-floor", "derived": "return_time_s"}],
    ids=["neither", "both"],
)
def test_FR011_expression_location_names_exactly_one_owner(owners):
    with pytest.raises(ValueError, match="rule or derived"):
        ExpressionLocation(line=1, column=1, end_column=2, fragment="a", **owners)


def test_FR011_diagnostic_code_outside_closed_list_is_rejected():
    with pytest.raises(ValueError, match="syntax_error"):
        Diagnostic("syntax_error", "x", FileLocation(file_line=1, file_column=1))


def test_FR011_diagnostic_and_locations_are_frozen():
    location = FileLocation(file_line=1, file_column=1)
    diagnostic = Diagnostic("invalid_ruleset", "x", location)
    with pytest.raises(FrozenInstanceError):
        diagnostic.code = "unknown_unit"
    with pytest.raises(FrozenInstanceError):
        location.file_line = 2


def test_FR011_rule_set_error_carries_exactly_one_diagnostic():
    diagnostic = Diagnostic(
        "unknown_unit", "unit km", FileLocation(file_line=3, file_column=8)
    )
    with pytest.raises(RuleSetError) as raised:
        raise RuleSetError(diagnostic)
    assert raised.value.diagnostic is diagnostic
    assert raised.value.args == (diagnostic,)
    with pytest.raises(TypeError):
        RuleSetError()
    with pytest.raises(TypeError):
        RuleSetError(diagnostic, diagnostic)
    with pytest.raises(TypeError):
        RuleSetError("unknown_unit: unit km")
