"""FR-009/FR-010/FR-011: the fail-closed rule-set loading pipeline.

Rule sets are written line by line so the expected file locations can be
counted by hand; expected expression locations are counted in the expression
string. None is produced by the loader. TOML syntax-error positions are
tomllib's own (research.md Decision 7).
"""

from types import MappingProxyType

import pytest

from assertion_engine.dsl import (
    Diagnostic,
    RuleSetError,
    load_ruleset,
    parse_expression,
)
from assertion_engine.dsl import ruleset as ruleset_module
from assertion_engine.dsl.errors import ExpressionLocation, FileLocation
from assertion_engine.dsl.parser import parse

SCHEMA = 'schema_version = "1.0.0"'
RULE = (
    "[rules.r]",
    'category = "threshold"',
    'expression = "battery_percent >= 0"',
)
BUILT_IN_NAMES = [
    "altitude_m",
    "descent_speed_mps",
    "horizontal_speed_mps",
    "home_distance_m",
]

RETURN_TIME = "home_distance_m / cruise_speed_mps + altitude_m / descent_rate_mps"
QUICK_RETURN = "return_time_s < return_limit_s and altitude_m > 0"
BATTERY_FLOOR = "battery_percent >= battery_floor_percent"
# Declarations deliberately out of alphabetical order: mappings keep file order.
VALID = (
    SCHEMA,
    "",
    "[parameters.return_limit_s]",
    'unit = "s"',
    "[parameters.battery_floor_percent]",
    'unit = "%"',
    "[parameters.descent_rate_mps]",
    'unit = "m/s"',
    "[parameters.cruise_speed_mps]",
    'unit = "m/s"',
    "",
    "[derived.return_time_s]",
    'unit = "s"',
    f'expression = "{RETURN_TIME}"',
    "",
    "[rules.quick-return]",
    'category = "logic"',
    f'expression = "{QUICK_RETURN}"',
    "",
    "[rules.battery-floor]",
    'category = "threshold"',
    f'expression = "{BATTERY_FLOOR}"',
)


def document(*lines):
    return "\n".join(lines) + "\n"


def load(lines):
    return load_ruleset(document(*lines).encode("utf-8"))


def rejection(data):
    """The diagnostic load_ruleset raises for data (bytes or a line tuple)."""
    if isinstance(data, tuple):
        data = document(*data).encode("utf-8")
    with pytest.raises(RuleSetError) as caught:
        load_ruleset(data)
    return caught.value.diagnostic


def at(column, fragment, line=1, **owner):
    """An expression location; a past-the-end one has fragment "" and width 1."""
    end = column + max(len(fragment), 1)
    return ExpressionLocation(line, column, end, fragment, **owner)


# A valid rule set (spec US2: valid rules still load).


def test_FR011_valid_non_temporal_rule_set_loads_in_file_order():
    ruleset = load(VALID)
    assert ruleset.schema_version == "1.0.0"
    assert list(ruleset.parameters.items()) == [
        ("return_limit_s", "s"),
        ("battery_floor_percent", "%"),
        ("descent_rate_mps", "m/s"),
        ("cruise_speed_mps", "m/s"),
    ]
    assert list(ruleset.derived) == ["return_time_s"]
    return_time = ruleset.derived["return_time_s"]
    assert (return_time.unit, return_time.expression) == ("s", RETURN_TIME)
    tree = return_time.annotations.tree
    assert tree == parse_expression(RETURN_TIME)
    assert str(return_time.annotations.type_of(tree)) == "scalar[s]"
    assert list(ruleset.rules) == ["quick-return", "battery-floor"]
    for short_name, category, expression in (
        ("quick-return", "logic", QUICK_RETURN),
        ("battery-floor", "threshold", BATTERY_FLOOR),
    ):
        rule = ruleset.rules[short_name]
        assert (rule.category, rule.expression) == (category, expression)
        assert rule.annotations.tree == parse_expression(expression)
        assert str(rule.annotations.type_of(rule.annotations.tree)) == "bool"
    assert list(ruleset.scope.derived) == [*BUILT_IN_NAMES, "return_time_s"]
    assert ruleset.scope.derived["return_time_s"] is return_time.annotations


def test_FR011_loaded_rule_set_is_read_only():
    ruleset = load(VALID)
    for mapping in (ruleset.parameters, ruleset.derived, ruleset.rules):
        with pytest.raises(TypeError):
            mapping["x"] = None


def test_FR009_rule_set_needs_no_parameters_or_derived_tables():
    ruleset = load((SCHEMA, *RULE))
    assert (dict(ruleset.parameters), dict(ruleset.derived)) == ({}, {})
    assert list(ruleset.rules) == ["r"]


def test_FR005_loader_parses_the_built_in_derived_definitions():
    ruleset = load((SCHEMA, *RULE))
    altitude = ruleset.scope.derived["altitude_m"]
    assert altitude.tree == parse("-position_ned_m.d")
    assert str(altitude.type_of(altitude.tree)) == "scalar[m]"


# Step 1: bytes and TOML.


@pytest.mark.parametrize(
    ("text", "location"),
    [
        # research.md Decision 7 E1 shape: "x = " fails where the value is missing.
        (f"{SCHEMA}\nx = \n", FileLocation(2, 5)),
        (f"{SCHEMA}\n[rules.r\n", FileLocation(2, 9)),
    ],
    ids=["missing-value", "unclosed-header"],
)
def test_FR011_toml_syntax_error_reports_its_file_line_and_column(text, location):
    diagnostic = rejection(text.encode("utf-8"))
    assert diagnostic.code == "invalid_ruleset"
    assert diagnostic.location == location


def test_FR011_duplicate_table_is_a_toml_syntax_error():
    diagnostic = rejection((SCHEMA, *RULE, *RULE))
    assert diagnostic.code == "invalid_ruleset"
    assert diagnostic.location.file_line == 5


def test_FR011_toml_too_deep_for_tomllib_is_invalid_ruleset():
    # tomllib recurses per nested array and raises RecursionError, not a
    # TOMLDecodeError; step 1 must still fail with a diagnostic.
    diagnostic = rejection(b"x = " + b"[" * 2000 + b"]" * 2000)
    assert diagnostic.code == "invalid_ruleset"
    assert diagnostic.location == FileLocation(1, 1)


@pytest.mark.parametrize(
    ("data", "location"),
    [
        (b'schema_version = "1.0.0"\n# caf\xe9\n', FileLocation(2, 6)),
        # Columns count characters: two 2-byte characters precede the bad byte.
        (b"# \xc3\xa9t\xc3\xa9 \xff\n", FileLocation(1, 7)),
    ],
    ids=["latin-1-byte", "after-multibyte-characters"],
)
def test_FR011_non_utf8_bytes_are_invalid_ruleset_at_the_first_bad_byte(data, location):
    diagnostic = rejection(data)
    assert diagnostic.code == "invalid_ruleset"
    assert diagnostic.location == location


# Step 2: file shape (contracts/ruleset.md "File shape"). A file location is
# the start of the line that defines the offending key, or of the table that
# lacks one; a missing top-level key points at the start of the file.


@pytest.mark.parametrize(
    ("lines", "location"),
    [
        ((SCHEMA, 'owner = "luke"', *RULE), FileLocation(2, 1)),
        ((SCHEMA, *RULE, 'severity = "high"'), FileLocation(5, 1)),
        (
            (SCHEMA, "[parameters.limit_m]", 'unit = "m"', "value = 120", *RULE),
            FileLocation(4, 1),
        ),
        ((SCHEMA, "[rules.r]", 'category = "threshold"'), FileLocation(2, 1)),
        (
            (SCHEMA, "[rules.r]", 'expression = "battery_percent >= 0"'),
            FileLocation(2, 1),
        ),
        (
            (SCHEMA, "[derived.x]", 'expression = "altitude_m"', *RULE),
            FileLocation(2, 1),
        ),
        ((SCHEMA, "[parameters.limit_m]", *RULE), FileLocation(2, 1)),
        (RULE, FileLocation(1, 1)),
        (("# draft", 'schema_version = "1.1.0"', *RULE), FileLocation(2, 1)),
        (("", "schema_version = 1.0", *RULE), FileLocation(2, 1)),
        ((SCHEMA, "", "[rules]"), FileLocation(3, 1)),
        ((SCHEMA, "[parameters.limit_m]", 'unit = "m"'), FileLocation(1, 1)),
        (
            (
                SCHEMA,
                "[rules.r]",
                'category = "safety"',
                'expression = "battery_percent >= 0"',
            ),
            FileLocation(3, 1),
        ),
        (
            (SCHEMA, "[rules.r]", "category = 1", 'expression = "x"'),
            FileLocation(3, 1),
        ),
        (
            (
                SCHEMA,
                "[rules.r]",
                'category = "threshold"',
                'expression = ["battery_percent >= 0"]',
            ),
            FileLocation(4, 1),
        ),
        ((SCHEMA, "[parameters.limit_m]", "unit = 1", *RULE), FileLocation(3, 1)),
        (
            (SCHEMA, "[[rules]]", 'category = "threshold"', 'expression = "x"'),
            FileLocation(2, 1),
        ),
        ((SCHEMA, 'rules.r = "battery_percent >= 0"'), FileLocation(2, 1)),
        ((SCHEMA, "parameters = 3", *RULE), FileLocation(2, 1)),
    ],
    ids=[
        "unknown-top-level-key",
        "unknown-rule-key",
        "parameter-value",
        "missing-expression",
        "missing-category",
        "missing-derived-unit",
        "missing-parameter-unit",
        "missing-schema-version",
        "wrong-schema-version",
        "schema-version-not-a-string",
        "zero-rules-empty-table",
        "zero-rules-absent",
        "unknown-category",
        "category-not-a-string",
        "expression-not-a-string",
        "unit-not-a-string",
        "rules-array-of-tables",
        "rule-not-a-table",
        "parameters-not-a-table",
    ],
)
def test_FR011_shape_error_is_invalid_ruleset_at_the_offending_key(lines, location):
    diagnostic = rejection(lines)
    assert diagnostic.code == "invalid_ruleset"
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("section", "key"),
    [
        ("parameters", "Limit_m"),
        ("parameters", "_limit"),
        ("parameters", "2x"),
        ("parameters", '"limit m"'),
        ("derived", "limit-m"),
        ("rules", "Battery-floor"),
        ("rules", "battery_floor"),
        ("rules", "battery--floor"),
        ("rules", "-battery"),
        ("rules", "battery-"),
    ],
)
def test_FR011_name_outside_its_pattern_is_invalid_ruleset(section, key):
    declarations = {
        "parameters": (f"[parameters.{key}]", 'unit = "m"', *RULE),
        "derived": (
            f"[derived.{key}]",
            'unit = "m"',
            'expression = "altitude_m"',
            *RULE,
        ),
        "rules": (
            f"[rules.{key}]",
            'category = "threshold"',
            'expression = "battery_percent >= 0"',
        ),
    }
    diagnostic = rejection((SCHEMA, *declarations[section]))
    assert diagnostic.code == "invalid_ruleset"
    assert diagnostic.location == FileLocation(2, 1)


@pytest.mark.parametrize(
    ("lines", "location"),
    [
        (
            (SCHEMA, "[rules.r]", '  category = "safety"', '  expression = "x"'),
            FileLocation(3, 3),
        ),
        ((SCHEMA, *RULE, 'notes = """', "first", '"""'), FileLocation(5, 1)),
        (
            (
                SCHEMA,
                "[rules.r]",
                'category = "threshold"',
                'expression = """battery_percent',
                '>= 0"""',
                'severity = "high"',
            ),
            FileLocation(6, 1),
        ),
        (
            (
                SCHEMA,
                'rules = { r = { category = "safety", expression = "x" } }',
            ),
            FileLocation(2, 1),
        ),
        (
            (
                SCHEMA,
                "[rules]",
                'r.category = "threshold"',
                'r.expression = "battery_percent >= 0"',
                'r.severity = "high"',
            ),
            FileLocation(5, 1),
        ),
    ],
    ids=[
        "indented-key",
        "multi-line-value",
        "after-a-multi-line-value",
        "inline-table",
        "dotted-keys",
    ],
)
def test_FR011_file_location_finds_keys_in_any_toml_spelling(lines, location):
    assert rejection(lines).location == location


# Step 3: names and units.


@pytest.mark.parametrize("section", ["parameters", "derived"])
@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("altitude_m", "name_conflict"),  # built-in derived quantity
        ("battery_percent", "name_conflict"),  # field
        ("norm", "name_conflict"),  # function
        ("hnorm", "name_conflict"),
        ("if", "name_conflict"),  # keyword
        ("held_for", "name_conflict"),  # temporal keyword
        ("or", "reserved_word"),
        ("not", "reserved_word"),
    ],
)
def test_FR004_FR010_declared_name_must_not_be_a_vocabulary_or_language_word(
    section, name, code
):
    declaration = {
        "parameters": (f"[parameters.{name}]", 'unit = "m"'),
        "derived": (f"[derived.{name}]", 'unit = "m"', 'expression = "altitude_m"'),
    }[section]
    diagnostic = rejection((SCHEMA, *declaration, *RULE))
    assert diagnostic.code == code
    assert diagnostic.location == FileLocation(2, 1)


PARAMETER_LIMIT_M = ("[parameters.limit_m]", 'unit = "m"')
DERIVED_LIMIT_M = ("[derived.limit_m]", 'unit = "m"', 'expression = "altitude_m"')


@pytest.mark.parametrize(
    ("lines", "location"),
    [
        ((SCHEMA, *PARAMETER_LIMIT_M, *DERIVED_LIMIT_M, *RULE), FileLocation(4, 1)),
        ((SCHEMA, *DERIVED_LIMIT_M, *PARAMETER_LIMIT_M, *RULE), FileLocation(2, 1)),
    ],
    ids=["parameter-first", "derived-first"],
)
def test_FR010_same_name_as_parameter_and_derived_conflicts_at_the_derived(
    lines, location
):
    diagnostic = rejection(lines)
    assert diagnostic.code == "name_conflict"
    assert diagnostic.location == location


@pytest.mark.parametrize("unit", ["km", "M", "", "m/s^2", "s/m", " m"])
def test_FR013_parameter_unit_outside_the_table_is_unknown_unit(unit):
    diagnostic = rejection((SCHEMA, "[parameters.x]", f'unit = "{unit}"', *RULE))
    assert diagnostic.code == "unknown_unit"
    assert diagnostic.location == FileLocation(3, 1)


def test_FR013_derived_unit_outside_the_table_is_unknown_unit():
    lines = (SCHEMA, "[derived.x]", 'expression = "altitude_m"', '  unit = "km"')
    diagnostic = rejection((*lines, *RULE))
    assert diagnostic.code == "unknown_unit"
    assert diagnostic.location == FileLocation(4, 3)


# Steps 4-8: parse errors name the rule or derived quantity being parsed.


def test_FR011_rule_parse_error_names_the_rule():
    lines = (
        SCHEMA,
        "[rules.battery-floor]",
        'category = "threshold"',
        'expression = "battery_percent >= >= 0"',
    )
    diagnostic = rejection(lines)
    assert diagnostic.code == "unexpected_token"
    assert diagnostic.location == at(20, ">=", rule="battery-floor")


def test_FR011_derived_parse_error_names_the_derived_quantity():
    lines = (SCHEMA, "[derived.x]", 'unit = "m"', 'expression = "(altitude_m"')
    diagnostic = rejection((*lines, *RULE))
    assert diagnostic.code == "unclosed_parenthesis"
    assert diagnostic.location == at(1, "(", derived="x")


def test_FR005_built_in_parse_error_names_the_built_in_before_rule_set_derived(
    monkeypatch,
):
    # A vocabulary bug: step 4 parses the built-ins before step 5's own.
    broken = MappingProxyType({"altitude_m": ("m", "-position_ned_m.")})
    monkeypatch.setattr(ruleset_module, "BUILT_IN_DERIVED", broken)
    lines = (SCHEMA, "[derived.x]", 'unit = "m"', 'expression = "altitude_m +"')
    diagnostic = rejection((*lines, *RULE))
    assert diagnostic.code == "unexpected_end"
    assert diagnostic.location == at(17, "", derived="altitude_m")


def test_FR011_parse_expression_names_no_owner():
    assert parse_expression("a < b") == parse("a < b")
    with pytest.raises(RuleSetError) as caught:
        parse_expression("battery_percent >= >= 0")
    assert isinstance(caught.value.diagnostic, Diagnostic)
    assert caught.value.diagnostic.location == at(20, ">=")


# First error wins: two errors at once report the earlier pipeline step,
# and inside one step the earlier one in file order.


@pytest.mark.parametrize(
    ("lines", "code", "location"),
    [
        (
            (
                SCHEMA,
                "[parameters.altitude_m]",
                'unit = "m"',
                "[rules.r]",
                'category = "safety"',
                'expression = "battery_percent >= 0"',
            ),
            "invalid_ruleset",
            FileLocation(5, 1),
        ),
        (
            (
                SCHEMA,
                "[parameters.limit_m]",
                'unit = "km"',
                "[derived.norm]",
                'unit = "m"',
                'expression = "altitude_m"',
                *RULE,
            ),
            "name_conflict",
            FileLocation(4, 1),
        ),
        (
            (
                SCHEMA,
                "[rules.r]",
                'category = "threshold"',
                'expression = "battery_percent >="',
                "[parameters.limit_m]",
                'unit = "km"',
            ),
            "unknown_unit",
            FileLocation(6, 1),
        ),
        (
            (
                SCHEMA,
                "[derived.a]",
                'unit = "s"',
                'expression = "altitude_m"',
                "[derived.b]",
                'unit = "m"',
                'expression = "altitude_m +"',
                *RULE,
            ),
            "unexpected_end",
            at(13, "", derived="b"),
        ),
        (
            (
                SCHEMA,
                "[rules.r]",
                'category = "threshold"',
                'expression = "battery_percent >="',
                "[derived.a]",
                'unit = "s"',
                'expression = "altitude_m"',
            ),
            "derived_unit_mismatch",
            at(1, "altitude_m", derived="a"),
        ),
        (
            (
                SCHEMA,
                "[rules.r]",
                'category = "threshold"',
                'expression = "batery_percent >= 0"',
                "[rules.s]",
                'category = "threshold"',
                'expression = "battery_percent >="',
            ),
            "unexpected_end",
            at(19, "", rule="s"),
        ),
    ],
    ids=[
        "shape-before-names",
        "names-before-units",
        "units-before-parsing",
        "derived-parsing-before-derived-checks",
        "derived-checks-before-rule-parsing",
        "rule-parsing-before-rule-checks",
    ],
)
def test_FR011_two_errors_report_the_earlier_pipeline_step(lines, code, location):
    diagnostic = rejection(lines)
    assert diagnostic.code == code
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("lines", "code", "location"),
    [
        (
            (
                SCHEMA,
                "[rules.s]",
                'category = "threshold"',
                'expression = "battery_percent >= 0"',
                "owner = 1",
                "[rules.r]",
                'category = "safety"',
                'expression = "battery_percent >= 0"',
            ),
            "invalid_ruleset",
            FileLocation(5, 1),
        ),
        (
            (
                SCHEMA,
                "[rules.s]",
                'category = "threshold"',
                'expression = "battery_percent >="',
                "[rules.r]",
                'category = "threshold"',
                'expression = "(battery_percent"',
            ),
            "unexpected_end",
            at(19, "", rule="s"),
        ),
        (
            (
                SCHEMA,
                "[rules.s]",
                'category = "threshold"',
                'expression = "batery_percent >= 0"',
                "[rules.r]",
                'category = "threshold"',
                'expression = "battery_percent"',
            ),
            "unknown_name",
            at(1, "batery_percent", rule="s"),
        ),
    ],
    ids=["shape", "rule-parsing", "rule-checks"],
)
def test_FR011_inside_one_step_the_first_error_in_file_order_wins(
    lines, code, location
):
    diagnostic = rejection(lines)
    assert diagnostic.code == code
    assert diagnostic.location == location


@pytest.mark.parametrize(
    "bad_rule",
    [
        ("[rules.bad]", 'category = "threshold"'),
        ("[rules.bad]", 'category = "threshold"', 'expression = "battery_percent"'),
    ],
    ids=["shape-error", "check-error"],
)
def test_FR011_failure_returns_no_partial_rule_set(bad_rule):
    # The first rule is valid; the rejection still returns nothing.
    lines = (
        SCHEMA,
        "[rules.good]",
        'category = "threshold"',
        'expression = "battery_percent >= 0"',
        *bad_rule,
    )
    with pytest.raises(RuleSetError):
        load(lines)
