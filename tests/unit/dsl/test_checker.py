"""FR-005/FR-010/FR-013: name resolution, arity, types and dimensions.

Expected types and locations are written by hand from contracts/ruleset.md
"Type and dimension rules" and "Diagnostics"; none is produced by the checker.
Value-typed expressions are checked as a derived quantity x declared in the
expected unit; rules are checked as rule r.
"""

import tomllib
from dataclasses import fields
from pathlib import Path

import pytest

from assertion_engine.dsl.checker import check_derived, check_rule
from assertion_engine.dsl.errors import ExpressionLocation, RuleSetError
from assertion_engine.dsl.parser import parse
from assertion_engine.dsl.syntax import Name, Span
from assertion_engine.dsl.vocabulary import BUILT_IN_DERIVED, FIELDS, FUNCTIONS

CORPUS = Path(__file__).resolve().parents[3] / "rules" / "corpus.toml"

# contracts/ruleset.md "Built-in vocabulary", copied literally.
CONTRACT_FIELDS = {
    "sequence_number": ("scalar", "1"),
    "mission_time_s": ("scalar", "s"),
    "position_ned_m": ("vector", "m"),
    "velocity_ned_mps": ("vector", "m/s"),
    "battery_percent": ("scalar", "%"),
}
CONTRACT_BUILT_IN_DERIVED = {
    "altitude_m": ("m", "-position_ned_m.d"),
    "descent_speed_mps": ("m/s", "velocity_ned_mps.d"),
    "horizontal_speed_mps": ("m/s", "hnorm(velocity_ned_mps)"),
    "home_distance_m": ("m", "hnorm(position_ned_m)"),
}

# Gate 「基本規則」 (spec SC-001): the corpus rules the parser accepts today.
BASIC_RULES = (
    "battery-floor",
    "altitude-ceiling",
    "horizontal-speed-limit",
    "return-reserve",
    "geofence-cylinder",
    "low-battery-stay-close",
    "descent-speed-near-ground",
)

# One parameter per declarable unit.
PARAMETERS = {
    "count": "1",
    "limit_percent": "%",
    "limit_m": "m",
    "limit_s": "s",
    "limit_mps": "m/s",
    "rate_percent_per_s": "%/s",
}


def built_in():
    """The built-in derived quantities, parsed as loading pipeline step 4 does."""
    return {
        name: (unit, text, parse(text))
        for name, (unit, text) in BUILT_IN_DERIVED.items()
    }


def scope(derived=None, parameters=PARAMETERS):
    """Check derived = {name: (unit, text)} beside the built-in quantities."""
    declarations = {
        name: (unit, text, parse(text))
        for name, (unit, text) in (derived or {}).items()
    }
    return check_derived(built_in(), declarations, parameters)


def check(text, derived=None):
    """Check text as rule r; return its tree and annotations."""
    tree = parse(text)
    return tree, check_rule("r", text, tree, scope(derived))


def value_type(text, unit):
    """Check text as derived quantity x declared in unit; return its type label."""
    annotations = scope({"x": (unit, text)}).derived["x"]
    return str(annotations.type_of(annotations.tree))


def rule_error(text, derived=None):
    with pytest.raises(RuleSetError) as caught:
        check(text, derived)
    return caught.value.diagnostic


def derived_error(derived):
    with pytest.raises(RuleSetError) as caught:
        scope(derived)
    return caught.value.diagnostic


def at(column, fragment, line=1, **owner):
    """The location of fragment from column; owner defaults to rule r."""
    return ExpressionLocation(
        line, column, column + len(fragment), fragment, **(owner or {"rule": "r"})
    )


def walk(node):
    """Every node of a tree, parents before children."""
    yield node
    for field in fields(node):
        value = getattr(node, field.name)
        for child in value if isinstance(value, tuple) else (value,):
            if not isinstance(child, (str, Span)):
                yield from walk(child)


def corpus():
    return tomllib.loads(CORPUS.read_text(encoding="utf-8"))


def corpus_scope():
    document = corpus()
    parameters = {name: table["unit"] for name, table in document["parameters"].items()}
    derived = {
        name: (table["unit"], table["expression"], parse(table["expression"]))
        for name, table in document["derived"].items()
    }
    return check_derived(built_in(), derived, parameters)


# Vocabulary (contracts/ruleset.md "Built-in vocabulary").


def test_FR005_fields_equal_the_contract_table():
    assert dict(FIELDS) == CONTRACT_FIELDS


def test_FR010_functions_take_one_vector_and_return_a_scalar():
    assert dict(FUNCTIONS) == {
        "norm": (("vector",), "scalar"),
        "hnorm": (("vector",), "scalar"),
    }


def test_FR005_built_in_derived_definitions_and_units_equal_the_contract_table():
    assert list(BUILT_IN_DERIVED.items()) == list(CONTRACT_BUILT_IN_DERIVED.items())


def test_FR005_built_in_derived_quantities_check_in_their_declared_units():
    # Every rule set loads them, so a failure here is a vocabulary bug.
    checked = scope().derived
    assert {
        name: str(annotations.type_of(annotations.tree))
        for name, annotations in checked.items()
    } == {
        "altitude_m": "scalar[m]",
        "descent_speed_mps": "scalar[m/s]",
        "horizontal_speed_mps": "scalar[m/s]",
        "home_distance_m": "scalar[m]",
    }
    assert list(checked) == list(CONTRACT_BUILT_IN_DERIVED)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("sequence_number", "scalar[1]"),
        ("mission_time_s", "scalar[s]"),
        ("position_ned_m", "vector[m]"),
        ("velocity_ned_mps", "vector[m/s]"),
        ("battery_percent", "scalar[%]"),
    ],
)
def test_FR005_field_has_its_vocabulary_type(name, expected):
    assert value_type(name, CONTRACT_FIELDS[name][1]) == expected


@pytest.mark.parametrize(("name", "unit"), PARAMETERS.items())
def test_FR009_parameter_is_a_scalar_of_its_declared_unit(name, unit):
    assert value_type(name, unit) == f"scalar[{unit}]"


# Corpus (research.md 量綱驗算).


def test_FR013_return_time_s_is_inferred_in_seconds():
    annotations = corpus_scope().derived["return_time_s"]
    tree = annotations.tree
    assert str(annotations.type_of(tree)) == "scalar[s]"
    assert str(annotations.type_of(tree.left)) == "scalar[s]"
    assert str(annotations.type_of(tree.right)) == "scalar[s]"


@pytest.mark.parametrize("short_name", BASIC_RULES)
def test_FR013_basic_corpus_rule_types_every_node_and_is_bool(short_name):
    text = corpus()["rules"][short_name]["expression"]
    tree = parse(text)
    annotations = check_rule(short_name, text, tree, corpus_scope())
    assert str(annotations.type_of(tree)) == "bool"
    labels = {str(annotations.type_of(node)) for node in walk(tree)}
    assert labels <= {
        "bool",
        "scalar[%]",
        "scalar[%/s]",
        "scalar[m]",
        "scalar[m/s]",
        "scalar[s]",
    }


def test_FR013_return_reserve_right_side_is_in_percent():
    text = corpus()["rules"]["return-reserve"]["expression"]
    tree = parse(text)
    annotations = check_rule("return-reserve", text, tree, corpus_scope())
    # s x %/s + % = %
    assert str(annotations.type_of(tree.right.left)) == "scalar[%]"
    assert str(annotations.type_of(tree.right)) == "scalar[%]"


# Name resolution.


def test_FR010_every_name_resolves_to_field_derived_or_parameter():
    text = (
        "battery_percent > return_time_s * drain_rate_percent_per_s"
        " + return_reserve_percent and altitude_m < fence_radius_m"
    )
    tree = parse(text)
    annotations = check_rule("r", text, tree, corpus_scope())
    resolved = {
        node.name: annotations.resolution_of(node)
        for node in walk(tree)
        if isinstance(node, Name)
    }
    assert resolved == {
        "battery_percent": "field",
        "return_time_s": "derived",
        "drain_rate_percent_per_s": "parameter",
        "return_reserve_percent": "parameter",
        "altitude_m": "derived",
        "fence_radius_m": "parameter",
    }


def test_FR010_names_inside_derived_quantities_are_resolved():
    checked = corpus_scope().derived
    resolved = {}
    for name in ("return_time_s", "altitude_m"):
        annotations = checked[name]
        for node in walk(annotations.tree):
            if isinstance(node, Name):
                resolved[node.name] = annotations.resolution_of(node)
    assert resolved == {
        "home_distance_m": "derived",
        "cruise_speed_mps": "parameter",
        "altitude_m": "derived",
        "descent_rate_mps": "parameter",
        "position_ned_m": "field",
    }


def test_FR010_annotations_are_keyed_by_node_identity():
    text = "altitude_m <= limit_m"
    tree, annotations = check(text)
    assert str(annotations.type_of(tree.left)) == "scalar[m]"
    twin = parse(text)
    assert twin == tree
    with pytest.raises(KeyError):
        annotations.type_of(twin.left)
    with pytest.raises(KeyError):
        annotations.resolution_of(twin.left)


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("batery_percent >= limit_percent", at(1, "batery_percent")),
        ("limit_m > altitud_m", at(11, "altitud_m")),
        ("norm < limit_m", at(1, "norm")),
        ("n > limit_m", at(1, "n")),
    ],
    ids=["field-typo", "derived-typo", "function-as-name", "axis-as-name"],
)
def test_FR010_unknown_name_points_at_the_name(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "unknown_name"
    assert diagnostic.location == location


def test_FR010_unknown_function_points_at_the_call():
    diagnostic = rule_error("limit_m > nrm(position_ned_m)")
    assert diagnostic.code == "unknown_name"
    assert diagnostic.location == at(11, "nrm(position_ned_m)")


@pytest.mark.parametrize(
    ("text", "location"),
    [
        (
            "norm(position_ned_m, velocity_ned_mps) < limit_m",
            at(1, "norm(position_ned_m, velocity_ned_mps)"),
        ),
        (
            "limit_m < hnorm(position_ned_m, 1, 2)",
            at(11, "hnorm(position_ned_m, 1, 2)"),
        ),
    ],
    ids=["norm", "hnorm"],
)
def test_FR010_arity_mismatch_points_at_the_call(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "arity_mismatch"
    assert diagnostic.location == location


# Functions: vector[D] -> scalar[D].


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("norm(velocity_ned_mps)", "m/s", "scalar[m/s]"),
        ("hnorm(position_ned_m)", "m", "scalar[m]"),
        ("norm(position_ned_m - position_ned_m)", "m", "scalar[m]"),
    ],
)
def test_FR013_function_keeps_its_argument_dimension(text, unit, expected):
    assert value_type(text, unit) == expected


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("norm(battery_percent) > limit_percent", at(6, "battery_percent")),
        ("limit_m < hnorm(altitude_m < limit_m)", at(17, "altitude_m < limit_m")),
    ],
    ids=["scalar", "bool"],
)
def test_FR013_function_argument_must_be_a_vector(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == location


# Type and dimension rules (contracts/ruleset.md), at least one positive and one
# negative case each. A type_mismatch points at the first operand, in source
# order, that the construct rejects by its own kind; a mismatch between operands
# that are acceptable one by one points at the construct.


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("altitude_m + limit_m", "m", "scalar[m]"),
        ("limit_s - mission_time_s", "s", "scalar[s]"),
        ("position_ned_m + position_ned_m", "m", "vector[m]"),
        ("velocity_ned_mps - velocity_ned_mps", "m/s", "vector[m/s]"),
    ],
)
def test_FR013_addition_keeps_the_shared_type(text, unit, expected):
    assert value_type(text, unit) == expected


@pytest.mark.parametrize(
    ("text", "code", "location"),
    [
        (
            "mission_time_s + altitude_m",
            "dimension_mismatch",
            at(1, "mission_time_s + altitude_m"),
        ),
        (
            "position_ned_m - velocity_ned_mps",
            "dimension_mismatch",
            at(1, "position_ned_m - velocity_ned_mps"),
        ),
        (
            "battery_percent + position_ned_m",
            "type_mismatch",
            at(1, "battery_percent + position_ned_m"),
        ),
        (
            "position_ned_m - limit_m",
            "type_mismatch",
            at(1, "position_ned_m - limit_m"),
        ),
        (
            "(altitude_m < limit_m) + altitude_m",
            "type_mismatch",
            at(2, "altitude_m < limit_m"),
        ),
        (
            "altitude_m - (altitude_m < limit_m)",
            "type_mismatch",
            at(15, "altitude_m < limit_m"),
        ),
    ],
    ids=[
        "scalar-dimensions",
        "vector-dimensions",
        "scalar-plus-vector",
        "vector-minus-scalar",
        "bool-left",
        "bool-right",
    ],
)
def test_FR013_addition_rejects(text, code, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == code
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("limit_s * rate_percent_per_s", "%", "scalar[%]"),
        ("velocity_ned_mps * limit_s", "m", "vector[m]"),
        ("limit_s * velocity_ned_mps", "m", "vector[m]"),
    ],
    ids=["scalar-scalar", "vector-scalar", "scalar-vector"],
)
def test_FR013_multiplication_adds_dimensions(text, unit, expected):
    assert value_type(text, unit) == expected


@pytest.mark.parametrize(
    ("text", "code", "location"),
    [
        (
            "position_ned_m * velocity_ned_mps",
            "type_mismatch",
            at(1, "position_ned_m * velocity_ned_mps"),
        ),
        (
            "(altitude_m < limit_m) * limit_m",
            "type_mismatch",
            at(2, "altitude_m < limit_m"),
        ),
        (
            "limit_m * (altitude_m < limit_m)",
            "type_mismatch",
            at(12, "altitude_m < limit_m"),
        ),
    ],
    ids=["vector-vector", "bool-left", "bool-right"],
)
def test_FR013_multiplication_rejects(text, code, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == code
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("home_distance_m / limit_mps", "s", "scalar[s]"),
        ("limit_percent / rate_percent_per_s", "s", "scalar[s]"),
        ("position_ned_m / mission_time_s", "m/s", "vector[m/s]"),
    ],
    ids=["scalar-scalar", "percent-rate", "vector-scalar"],
)
def test_FR013_division_subtracts_dimensions(text, unit, expected):
    assert value_type(text, unit) == expected


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("mission_time_s / position_ned_m", at(18, "position_ned_m")),
        ("position_ned_m / position_ned_m", at(18, "position_ned_m")),
        ("(altitude_m < limit_m) / limit_s", at(2, "altitude_m < limit_m")),
    ],
    ids=["scalar-vector", "vector-vector", "bool-left"],
)
def test_FR013_division_rejects(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "left", "right"),
    [
        ("altitude_m * altitude_m > limit_m * limit_m", "scalar[m^2]", "scalar[m^2]"),
        ("count / limit_s < rate_percent_per_s / limit_percent", "scalar[1/s]", None),
        ("limit_mps / limit_s >= limit_mps / limit_s", "scalar[m/s^2]", None),
    ],
)
def test_FR013_products_and_quotients_infer_any_exponents(text, left, right):
    tree, annotations = check(text)
    assert str(annotations.type_of(tree.left)) == left
    assert str(annotations.type_of(tree.right)) == (right or left)


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("-limit_percent", "%", "scalar[%]"),
        ("-position_ned_m", "m", "vector[m]"),
    ],
)
def test_FR013_negation_keeps_the_type(text, unit, expected):
    assert value_type(text, unit) == expected


def test_FR013_negation_rejects_bool():
    diagnostic = rule_error("-(altitude_m < limit_m)")
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == at(3, "altitude_m < limit_m")


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("velocity_ned_mps.n", "m/s", "scalar[m/s]"),
        ("position_ned_m.e", "m", "scalar[m]"),
        ("(position_ned_m / limit_s).d", "m/s", "scalar[m/s]"),
    ],
)
def test_FR013_component_of_a_vector_is_a_scalar(text, unit, expected):
    assert value_type(text, unit) == expected


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("battery_percent.d", at(1, "battery_percent")),
        ("(altitude_m < limit_m).n", at(2, "altitude_m < limit_m")),
    ],
    ids=["scalar", "bool"],
)
def test_FR013_component_rejects_a_non_vector(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == location


@pytest.mark.parametrize("op", ["<", "<=", ">", ">=", "==", "!="])
def test_FR013_comparison_of_same_dimension_scalars_is_bool(op):
    tree, annotations = check(f"altitude_m {op} limit_m")
    assert str(annotations.type_of(tree)) == "bool"


@pytest.mark.parametrize(
    ("text", "code", "location"),
    [
        (
            "battery_percent > home_distance_m",
            "dimension_mismatch",
            at(1, "battery_percent > home_distance_m"),
        ),
        ("position_ned_m == position_ned_m", "type_mismatch", at(1, "position_ned_m")),
        ("limit_m < position_ned_m", "type_mismatch", at(11, "position_ned_m")),
        (
            "(altitude_m < limit_m) == (altitude_m < limit_m)",
            "type_mismatch",
            at(2, "altitude_m < limit_m"),
        ),
    ],
    ids=["dimensions", "vectors", "vector-right", "bools"],
)
def test_FR013_comparison_rejects(text, code, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == code
    assert diagnostic.location == location


@pytest.mark.parametrize(
    "text",
    [
        "altitude_m < limit_m and mission_time_s > limit_s",
        "altitude_m < limit_m implies mission_time_s > limit_s",
    ],
)
def test_FR013_and_implies_of_bools_is_bool(text):
    tree, annotations = check(text)
    assert str(annotations.type_of(tree)) == "bool"


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("battery_percent and altitude_m < limit_m", at(1, "battery_percent")),
        ("altitude_m < limit_m and position_ned_m", at(26, "position_ned_m")),
        ("altitude_m < limit_m implies battery_percent", at(30, "battery_percent")),
        ("count implies altitude_m < limit_m", at(1, "count")),
    ],
    ids=["and-left", "and-right", "implies-right", "implies-left"],
)
def test_FR013_and_implies_reject_a_non_bool(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        (
            "if altitude_m < limit_m then limit_mps else descent_speed_mps",
            "m/s",
            "scalar[m/s]",
        ),
        (
            "if altitude_m < limit_m then position_ned_m else -position_ned_m",
            "m",
            "vector[m]",
        ),
    ],
)
def test_FR006_conditional_takes_its_branch_type(text, unit, expected):
    assert value_type(text, unit) == expected


def test_FR006_conditional_of_bool_branches_is_bool():
    text = "if count < 1 then altitude_m < limit_m else limit_s > mission_time_s"
    tree, annotations = check(text)
    assert str(annotations.type_of(tree)) == "bool"


@pytest.mark.parametrize(
    ("text", "code", "location"),
    [
        (
            "if battery_percent then limit_m else altitude_m",
            "type_mismatch",
            at(4, "battery_percent"),
        ),
        (
            "if count < 1 then limit_m else position_ned_m",
            "type_mismatch",
            at(1, "if count < 1 then limit_m else position_ned_m"),
        ),
        (
            "if count < 1 then altitude_m < limit_m else limit_m",
            "type_mismatch",
            at(1, "if count < 1 then altitude_m < limit_m else limit_m"),
        ),
        (
            "if count < 1 then limit_m else limit_s",
            "dimension_mismatch",
            at(1, "if count < 1 then limit_m else limit_s"),
        ),
    ],
    ids=["condition", "scalar-vector", "bool-scalar", "dimensions"],
)
def test_FR006_conditional_rejects(text, code, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == code
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        ("battery_percent", "battery_percent"),
        ("altitude_m + limit_m", "altitude_m + limit_m"),
        ("position_ned_m", "position_ned_m"),
    ],
)
def test_FR013_rule_that_is_not_bool_is_rejected_at_its_root(text, fragment):
    diagnostic = rule_error(text)
    assert diagnostic.code == "not_boolean_rule"
    assert diagnostic.location == at(1, fragment)


def test_FR011_diagnostic_names_the_rule_being_checked():
    text = "battery_percent"
    with pytest.raises(RuleSetError) as caught:
        check_rule("battery-floor", text, parse(text), scope())
    assert caught.value.diagnostic.location.rule == "battery-floor"
    assert caught.value.diagnostic.location.derived is None


# Literals: dimensionless, except that literal 0 takes its partner's dimension
# in +, - and comparisons.


@pytest.mark.parametrize(
    ("text", "zero", "expected"),
    [
        ("descent_speed_mps > 0", "right", "scalar[m/s]"),
        ("0 <= battery_percent", "left", "scalar[%]"),
        ("0.0 < limit_s", "left", "scalar[s]"),
        ("limit_m - 00 != altitude_m", None, "scalar[m]"),
    ],
    ids=["compare-right", "compare-left", "decimal-zero", "subtract"],
)
def test_FR013_zero_literal_takes_its_partner_dimension(text, zero, expected):
    tree, annotations = check(text)
    node = tree.left.right if zero is None else getattr(tree, zero)
    assert str(annotations.type_of(node)) == expected
    assert str(annotations.type_of(tree)) == "bool"


def test_FR013_zero_literal_in_addition_keeps_the_partner_type():
    assert value_type("0 + altitude_m", "m") == "scalar[m]"
    assert value_type("limit_mps - 0", "m/s") == "scalar[m/s]"


@pytest.mark.parametrize(
    ("text", "expected"),
    [("0 + 0 == 0", "scalar[1]"), ("altitude_m * 0 > limit_m", "scalar[1]")],
    ids=["no-partner", "product"],
)
def test_FR013_zero_literal_without_an_additive_partner_is_dimensionless(
    text, expected
):
    tree, annotations = check(text)
    zero = tree.left.right
    assert str(annotations.type_of(zero)) == expected


def test_FR013_zero_literal_takes_a_dimension_but_not_a_kind():
    diagnostic = rule_error("position_ned_m - 0")
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == at(1, "position_ned_m - 0")


def test_FR013_zero_literal_takes_no_dimension_from_a_conditional_branch():
    diagnostic = rule_error("if count < 1 then 0 else limit_m")
    assert diagnostic.code == "dimension_mismatch"


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("battery_percent > 1", at(1, "battery_percent > 1")),
        ("limit_m + 0.5 < limit_m", at(1, "limit_m + 0.5")),
        ("10 == limit_s", at(1, "10 == limit_s")),
    ],
)
def test_FR013_nonzero_literal_is_dimensionless(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "dimension_mismatch"
    assert diagnostic.location == location


def test_FR013_nonzero_literal_matches_a_dimensionless_partner():
    tree, annotations = check("sequence_number == count + 1")
    assert str(annotations.type_of(tree.right.right)) == "scalar[1]"
    assert value_type("0.5 * altitude_m", "m") == "scalar[m]"


# Derived quantities: declared unit and dependency graph.


def test_FR013_derived_quantity_may_be_a_vector_of_its_unit():
    assert value_type("position_ned_m * 2", "m") == "vector[m]"
    tree, annotations = check(
        "norm(v) < limit_m", derived={"v": ("m", "position_ned_m * 2")}
    )
    assert str(annotations.type_of(tree.left.arguments[0])) == "vector[m]"


def test_FR013_vector_derived_quantity_stays_a_vector_in_rules():
    diagnostic = rule_error("v < limit_m", derived={"v": ("m", "position_ned_m")})
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == at(1, "v")


def test_FR013_derived_quantities_may_refer_forward_and_share_dependencies():
    derived = {
        "a": ("s", "b / limit_mps + c / limit_mps"),
        "b": ("m", "d + limit_m"),
        "c": ("m", "d"),
        "d": ("m", "altitude_m"),
    }
    checked = scope(derived).derived
    assert list(checked) == [*CONTRACT_BUILT_IN_DERIVED, "a", "b", "c", "d"]
    assert str(checked["a"].type_of(checked["a"].tree)) == "scalar[s]"
    tree, annotations = check("a > limit_s", derived)
    assert annotations.resolution_of(tree.left) == "derived"
    assert str(annotations.type_of(tree.left)) == "scalar[s]"


@pytest.mark.parametrize(
    ("derived", "location"),
    [
        ({"t": ("s", "altitude_m")}, at(1, "altitude_m", derived="t")),
        (
            {"t": ("1", "altitude_m < limit_m")},
            at(1, "altitude_m < limit_m", derived="t"),
        ),
        (
            {"t": ("m", "altitude_m * limit_m")},
            at(1, "altitude_m * limit_m", derived="t"),
        ),
    ],
    ids=["other-unit", "bool", "non-table"],
)
def test_FR013_derived_unit_mismatch_points_at_the_expression(derived, location):
    diagnostic = derived_error(derived)
    assert diagnostic.code == "derived_unit_mismatch"
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("derived", "location", "path"),
    [
        (
            {"a": ("1", "b + 1"), "b": ("1", "a + 1")},
            at(1, "a", derived="b"),
            "a -> b -> a",
        ),
        ({"a": ("1", "count + a")}, at(9, "a", derived="a"), "a -> a"),
        (
            {
                "a": ("1", "b"),
                "b": ("1", "c"),
                "c": ("1", "count * a"),
                "d": ("1", "a"),
            },
            at(9, "a", derived="c"),
            "a -> b -> c -> a",
        ),
        (
            {"z": ("1", "count"), "a": ("1", "z + b"), "b": ("1", "a")},
            at(1, "a", derived="b"),
            "a -> b -> a",
        ),
        (
            {"x": ("1", "a"), "a": ("1", "b"), "b": ("1", "a")},
            at(1, "a", derived="b"),
            "a -> b -> a",
        ),
    ],
    ids=["pair", "self", "three", "after-a-checked-one", "behind-a-dependent"],
)
def test_FR013_derived_cycle_points_at_the_reference_that_closes_it(
    derived, location, path
):
    # Depth first in declaration order; the closing reference is in the
    # quantity being checked when its target is already on the path. The
    # message lists the cycle alone, not the dependents that led into it.
    diagnostic = derived_error(derived)
    assert diagnostic.code == "derived_cycle"
    assert diagnostic.location == location
    assert diagnostic.message.endswith(f": {path}")


def test_FR011_derived_dependency_errors_name_the_dependency():
    diagnostic = derived_error(
        {"a": ("m", "b + limit_m"), "b": ("m", "altitude_m + limit_s")}
    )
    assert diagnostic.code == "dimension_mismatch"
    assert diagnostic.location == at(1, "altitude_m + limit_s", derived="b")


def test_FR011_derived_quantities_are_checked_in_declaration_order():
    unknown = {"b": ("m", "altitud_m"), "a": ("s", "altitude_m")}
    assert derived_error(unknown).code == "unknown_name"
    assert derived_error(unknown).location == at(1, "altitud_m", derived="b")
    mismatch = {"a": ("s", "altitude_m"), "b": ("m", "altitud_m")}
    assert derived_error(mismatch).code == "derived_unit_mismatch"


def test_FR010_unknown_name_in_a_derived_quantity_names_it():
    diagnostic = derived_error({"x": ("m", "limit_m + altitud_m")})
    assert diagnostic.code == "unknown_name"
    assert diagnostic.location == at(11, "altitud_m", derived="x")


# First error wins: children left to right before their parent; a call's
# function name, then its arguments' own errors, then arity, then argument kinds.


@pytest.mark.parametrize(
    ("text", "code", "location"),
    [
        ("batery + altitud_m", "unknown_name", at(1, "batery")),
        ("battery_percent and altitud_m", "unknown_name", at(21, "altitud_m")),
        (
            "(limit_m + limit_s < count) and battery_percent",
            "dimension_mismatch",
            at(2, "limit_m + limit_s"),
        ),
        ("nrm(batery) < limit_m", "unknown_name", at(1, "nrm(batery)")),
        (
            "norm(battery_percent, limit_m) < limit_m",
            "arity_mismatch",
            at(1, "norm(battery_percent, limit_m)"),
        ),
        ("norm(batery) < limit_m", "unknown_name", at(6, "batery")),
        ("norm(batery, limit_m) < limit_m", "unknown_name", at(6, "batery")),
    ],
    ids=[
        "left-first",
        "child-before-parent",
        "inner-before-outer",
        "function-name-first",
        "arity-before-type",
        "argument-names",
        "arguments-before-arity",
    ],
)
def test_FR011_first_error_in_traversal_order_wins(text, code, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == code
    assert diagnostic.location == location


# Multi-line nodes: the location runs from the node's start to the end of its
# start line.


@pytest.mark.parametrize(
    ("text", "code", "location"),
    [
        ("altitude_m +\n  limit_m", "not_boolean_rule", at(1, "altitude_m +")),
        (
            "count < 1 and battery_percent +\n  limit_m > 0",
            "dimension_mismatch",
            at(15, "battery_percent +"),
        ),
        (
            "altitude_m < limit_m and\n  battery_percent",
            "type_mismatch",
            at(3, "battery_percent", line=2),
        ),
        (
            "count < 1\n  and (if limit_s > 0 then limit_m  \n else limit_s) < limit_m",
            "dimension_mismatch",
            at(8, "if limit_s > 0 then limit_m  ", line=2),
        ),
    ],
    ids=["root", "mid-line-start", "second-line", "trailing-blanks"],
)
def test_FR011_multiline_node_location_ends_with_its_start_line(text, code, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == code
    assert diagnostic.location == location


# Temporal keywords (contracts/ruleset.md "Temporal keywords"): prev and ago keep
# their value's type, held_for and within are bool, slope is its value's
# dimension per second. Every duration is a scalar in s; a literal duration
# (a number under any unary '-') that is not above zero is nonpositive_duration
# before its dimension is looked at, so 0, -5 and -0 are nonpositive_duration and
# a positive literal such as 5 is a dimensionless dimension_mismatch. A duration
# the keyword rejects on its own is located at the duration.


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("prev(altitude_m)", "m", "scalar[m]"),
        ("prev(position_ned_m)", "m", "vector[m]"),
        ("ago(battery_percent, limit_s)", "%", "scalar[%]"),
        ("ago(velocity_ned_mps, limit_s)", "m/s", "vector[m/s]"),
    ],
)
def test_FR007_prev_and_ago_keep_their_value_type(text, unit, expected):
    assert value_type(text, unit) == expected


@pytest.mark.parametrize(
    "text",
    [
        "prev(altitude_m < limit_m)",
        "ago(altitude_m < limit_m, limit_s)",
        "held_for(battery_percent < limit_percent, limit_s)",
        "within(altitude_m < limit_m, mission_time_s)",
    ],
    ids=["prev", "ago", "held_for", "within"],
)
def test_FR007_temporal_form_of_a_bool_is_bool(text):
    tree, annotations = check(text)
    assert str(annotations.type_of(tree)) == "bool"


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("slope(battery_percent, limit_s)", "%/s", "scalar[%/s]"),
        ("slope(altitude_m, mission_time_s)", "m/s", "scalar[m/s]"),
    ],
)
def test_FR008_slope_is_its_value_dimension_per_second(text, unit, expected):
    assert value_type(text, unit) == expected


def test_FR008_slope_may_infer_an_undeclarable_dimension():
    tree, annotations = check("slope(limit_mps, limit_s) > limit_mps / limit_s")
    assert str(annotations.type_of(tree.left)) == "scalar[m/s^2]"


@pytest.mark.parametrize(
    "text",
    [
        "mission_time_s - prev(mission_time_s) <= limit_s",
        "norm(position_ned_m - prev(position_ned_m))"
        " / (mission_time_s - prev(mission_time_s)) <= limit_mps",
        "held_for(battery_percent < limit_percent, limit_s)"
        " implies home_distance_m < ago(home_distance_m, limit_s)",
        "-slope(battery_percent, limit_s) <= rate_percent_per_s",
        "altitude_m + slope(altitude_m, limit_s) * limit_s <= limit_m",
    ],
    ids=[
        "telemetry-heartbeat",
        "no-sudden-jump",
        "battery-tier-low",
        "battery-drain-rate",
        "altitude-trend-ceiling",
    ],
)
def test_FR007_corpus_shaped_temporal_rule_is_bool(text):
    tree, annotations = check(text)
    assert str(annotations.type_of(tree)) == "bool"


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("held_for(battery_percent, limit_s)", at(10, "battery_percent")),
        ("within(position_ned_m, limit_s)", at(8, "position_ned_m")),
        ("slope(position_ned_m, limit_s) < limit_mps", at(7, "position_ned_m")),
        (
            "slope(altitude_m < limit_m, limit_s) < limit_mps",
            at(7, "altitude_m < limit_m"),
        ),
    ],
    ids=["held_for-scalar", "within-vector", "slope-vector", "slope-bool"],
)
def test_FR007_temporal_value_of_a_rejected_kind_is_type_mismatch(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "location"),
    [
        (
            "held_for(altitude_m < limit_m, position_ned_m)",
            at(32, "position_ned_m"),
        ),
        (
            "ago(altitude_m, altitude_m < limit_m) < limit_m",
            at(17, "altitude_m < limit_m"),
        ),
    ],
    ids=["vector", "bool"],
)
def test_FR007_duration_must_be_a_scalar(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "type_mismatch"
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("ago(altitude_m, limit_m) < limit_m", at(17, "limit_m")),
        ("held_for(altitude_m < limit_m, limit_mps)", at(32, "limit_mps")),
        ("within(altitude_m < limit_m, count)", at(30, "count")),
        ("slope(altitude_m, limit_mps) < limit_mps", at(19, "limit_mps")),
        ("held_for(altitude_m < limit_m, 5)", at(32, "5")),
        ("within(altitude_m < limit_m, 2.5)", at(30, "2.5")),
        ("held_for(altitude_m < limit_m, --5)", at(32, "--5")),
    ],
    ids=[
        "ago",
        "held_for",
        "within",
        "slope",
        "positive-literal",
        "positive-decimal",
        "double-negation",
    ],
)
def test_FR007_duration_not_in_seconds_is_dimension_mismatch(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "dimension_mismatch"
    assert diagnostic.location == location


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("held_for(altitude_m < limit_m, 0)", at(32, "0")),
        ("within(altitude_m < limit_m, 0.0)", at(30, "0.0")),
        ("ago(altitude_m, 00) < limit_m", at(17, "00")),
        ("ago(altitude_m, -5) < limit_m", at(17, "-5")),
        ("slope(altitude_m, -0) < limit_mps", at(19, "-0")),
        ("held_for(altitude_m < limit_m, -(2.5))", at(32, "-(2.5)")),
        ("within(altitude_m < limit_m, --0)", at(30, "--0")),
    ],
    ids=[
        "zero",
        "decimal-zero",
        "double-zero",
        "negative",
        "negative-zero",
        "negated-group",
        "double-negated-zero",
    ],
)
def test_FR007_literal_duration_not_above_zero_is_nonpositive_duration(text, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == "nonpositive_duration"
    assert diagnostic.location == location


def test_FR007_only_a_literal_duration_has_its_sign_checked():
    # Parameter values are bound in M2 and checked there (contracts/ruleset.md).
    tree, annotations = check("ago(altitude_m, -limit_s) < limit_m")
    assert str(annotations.type_of(tree.left.duration)) == "scalar[s]"
    assert str(annotations.type_of(tree)) == "bool"


@pytest.mark.parametrize(
    ("text", "code", "location"),
    [
        (
            "held_for(battery_percent, altitud_m)",
            "unknown_name",
            at(27, "altitud_m"),
        ),
        ("ago(batery, altitud_m) < limit_m", "unknown_name", at(5, "batery")),
        ("held_for(battery_percent, 0)", "type_mismatch", at(10, "battery_percent")),
        (
            "slope(position_ned_m, limit_m) < limit_mps",
            "type_mismatch",
            at(7, "position_ned_m"),
        ),
        ("prev(ago(altitude_m, 0)) < limit_m", "nonpositive_duration", at(22, "0")),
        ("ago(altitude_m, limit_m) < count", "dimension_mismatch", at(17, "limit_m")),
    ],
    ids=[
        "arguments-before-the-keyword",
        "value-argument-first",
        "value-before-duration",
        "value-kind-before-duration-dimension",
        "inner-keyword-first",
        "keyword-before-its-parent",
    ],
)
def test_FR011_temporal_first_error_in_traversal_order_wins(text, code, location):
    diagnostic = rule_error(text)
    assert diagnostic.code == code
    assert diagnostic.location == location
