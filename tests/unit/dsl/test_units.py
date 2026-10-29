"""FR-013: dimensions as integer exponents over (m, s, %) and the unit table."""

import pytest

from assertion_engine.dsl.units import UNITS, Dimension, dimension_of

# contracts/ruleset.md "Units and dimensions", copied literally.
CONTRACT_UNITS = {
    "1": (0, 0, 0),
    "%": (0, 0, 1),
    "m": (1, 0, 0),
    "s": (0, 1, 0),
    "m/s": (1, -1, 0),
    "%/s": (0, -1, 1),
}


def exponents(dimension):
    return (dimension.length, dimension.time, dimension.battery)


@pytest.mark.parametrize(("unit", "triple"), CONTRACT_UNITS.items())
def test_FR013_unit_maps_to_its_contract_triple(unit, triple):
    assert exponents(dimension_of(unit)) == triple


def test_FR013_unit_table_is_exactly_the_six_declarable_units():
    assert {unit: exponents(UNITS[unit]) for unit in UNITS} == CONTRACT_UNITS


@pytest.mark.parametrize("unit", ["km", "", "m/s/s", "s/m", "%/m", "M", " m"])
def test_FR013_unknown_unit_is_rejected(unit):
    with pytest.raises(ValueError, match="not a declarable unit"):
        dimension_of(unit)


def test_FR013_multiplication_adds_every_exponent():
    assert Dimension(1, 2, 3) * Dimension(4, 5, 6) == Dimension(5, 7, 9)


def test_FR013_division_subtracts_every_exponent():
    assert Dimension(1, 2, 3) / Dimension(4, 5, 6) == Dimension(-3, -3, -3)


def test_FR013_unit_arithmetic_matches_the_corpus_checks():
    # research.md 量綱驗算: s x %/s = %, % / %/s = s, m / s = m/s.
    assert dimension_of("s") * dimension_of("%/s") == dimension_of("%")
    assert dimension_of("%") / dimension_of("%/s") == dimension_of("s")
    assert dimension_of("m") / dimension_of("s") == dimension_of("m/s")


@pytest.mark.parametrize("unit", CONTRACT_UNITS)
def test_FR013_declarable_dimension_formats_as_its_unit(unit):
    assert str(dimension_of(unit)) == unit


@pytest.mark.parametrize(
    ("triple", "label"),
    [
        ((2, 0, 0), "m^2"),
        ((0, -1, 0), "1/s"),
        ((1, -2, 0), "m/s^2"),
        ((1, 1, 0), "m*s"),
        ((1, 0, 1), "m*%"),
        ((-1, 0, 1), "%/m"),
        ((0, -1, -1), "1/(s*%)"),
        ((2, -3, 1), "m^2*%/s^3"),
        ((-1, -1, -2), "1/(m*s*%^2)"),
    ],
)
def test_FR013_inferred_dimension_formats_as_a_label(triple, label):
    # Positive exponents over a slash, bases in (m, s, %) order; a product of
    # two or more bases under the slash is parenthesized.
    assert str(Dimension(*triple)) == label


def test_FR013_dimension_is_immutable_and_compares_by_value():
    assert Dimension(1, -1, 0) == dimension_of("m/s")
    assert hash(Dimension(1, -1, 0)) == hash(dimension_of("m/s"))
    with pytest.raises(AttributeError):
        dimension_of("m").length = 2
