"""FR-001/006/009/011: source validation before any output preparation."""

from decimal import Decimal
from fractions import Fraction

import pytest

from assertion_engine.artifacts import source_timeline
from assertion_engine.simulator.config import load_config
from assertion_engine.telemetry import ScenarioSource

BASELINE = {
    "schema_version": '"1.0.0"',
    "scenario_name": '"normal-flight"',
    "scenario_version": '"1.0.0"',
    "seed": "42",
    "vehicle_id": '"vehicle-001"',
    "target_altitude_m": "10.0",
    "climb_rate_mps": "1.0",
    "hover_duration_s": "5.0",
    "northbound_distance_m": "20.0",
    "cruise_speed_mps": "2.0",
    "descent_rate_mps": "1.0",
    "observation_spacing_m": "0.2",
    "initial_battery_percent": "100.0",
    "battery_drain_percent_per_s": "0.2",
}
NUMERIC = tuple(list(BASELINE)[5:])
POSITIVE = (
    "target_altitude_m",
    "climb_rate_mps",
    "northbound_distance_m",
    "cruise_speed_mps",
    "descent_rate_mps",
    "observation_spacing_m",
)


def scenario_file(tmp_path, overrides=None, missing=None):
    values = {**BASELINE, **(overrides or {})}
    if missing:
        values.pop(missing)
    path = tmp_path / "scenario.toml"
    path.write_text("".join(f"{key} = {value}\n" for key, value in values.items()))
    return path


def test_FR001_baseline_normalization_and_exact_rate(tmp_path):
    source = load_config(scenario_file(tmp_path))
    assert isinstance(source, ScenarioSource)
    assert (source.name, source.version, source.seed) == ("normal-flight", "1.0.0", 42)
    assert set(source.config) == {
        "schema_version",
        "vehicle_id",
        *NUMERIC,
        "sample_rate_hz",
        "sample_interval_s",
    }
    assert source.config["sample_rate_hz"] == 10
    assert source.config["sample_interval_s"] == Decimal("0.1")
    assert source.config["observation_spacing_m"] == Decimal("0.2")
    assert source_timeline(source.config) == (
        Fraction(10),
        Fraction(1, 10),
        (
            Fraction(0),
            Fraction(10),
            Fraction(15),
            Fraction(25),
            Fraction(35),
            Fraction(45),
        ),
        450,
    )


@pytest.mark.parametrize("field", BASELINE)
def test_FR001_every_required_field(tmp_path, field):
    with pytest.raises(ValueError, match=field):
        load_config(scenario_file(tmp_path, missing=field))


@pytest.mark.parametrize("field", NUMERIC)
@pytest.mark.parametrize("token", ['"2.0"', "true", "[2.0]"])
def test_FR001_numeric_types_are_not_coerced(tmp_path, field, token):
    with pytest.raises(ValueError, match=field):
        load_config(scenario_file(tmp_path, {field: token}))


@pytest.mark.parametrize("field", NUMERIC)
@pytest.mark.parametrize("token", ["nan", "inf", "-inf"])
def test_FR001_nonfinite_source_values(tmp_path, field, token):
    with pytest.raises(ValueError, match=field):
        load_config(scenario_file(tmp_path, {field: token}))


@pytest.mark.parametrize("field", POSITIVE)
@pytest.mark.parametrize("token", ["0", "-1"])
def test_FR001_positive_source_ranges(tmp_path, field, token):
    with pytest.raises(ValueError, match=field):
        load_config(scenario_file(tmp_path, {field: token}))


@pytest.mark.parametrize(
    ("field", "token", "diagnostic"),
    [
        ("hover_duration_s", "-1", "hover_duration_s"),
        ("initial_battery_percent", "-1", "initial_battery_percent"),
        ("initial_battery_percent", "101", "initial_battery_percent"),
        ("battery_drain_percent_per_s", "-1", "battery_drain_percent_per_s"),
        ("battery_drain_percent_per_s", "3", "battery"),
        ("seed", "-1", "seed"),
        ("seed", "true", "seed"),
        ("seed", "42.0", "seed"),
        ("seed", '"42"', "seed"),
        ("schema_version", '"2.0.0"', "schema_version"),
        ("schema_version", "1", "schema_version"),
        ("scenario_version", '"1.0"', "scenario_version"),
        ("scenario_version", "1", "scenario_version"),
        ("scenario_name", '""', "scenario_name"),
        ("scenario_name", "42", "scenario_name"),
        ("vehicle_id", '""', "vehicle_id"),
        ("vehicle_id", "true", "vehicle_id"),
        ("sample_rate_hz", "10", "sample_rate_hz"),
        ("generated_at", '"today"', "generated_at"),
        ("observation_spacing_m", "0.0000001", "metadata"),
        ("observation_spacing_m", "10000000", "metadata"),
        ("observation_spacing_m", "0.0000016", "strictly increasing"),
    ],
)
def test_FR001_invalid_source_diagnostics(tmp_path, field, token, diagnostic):
    with pytest.raises(ValueError, match=diagnostic):
        load_config(scenario_file(tmp_path, {field: token}))


@pytest.mark.parametrize("hover", ["5.05", "5.0000004"])
def test_FR006_exact_terminal_alignment_precedes_rounding(tmp_path, hover):
    with pytest.raises(ValueError, match="terminal.*align"):
        load_config(scenario_file(tmp_path, {"hover_duration_s": hover}))


def test_FR006_three_hz_and_internal_off_grid_are_valid(tmp_path):
    source = load_config(
        scenario_file(
            tmp_path,
            {
                "target_altitude_m": "1",
                "hover_duration_s": "1",
                "northbound_distance_m": "3",
                "cruise_speed_mps": "3",
                "observation_spacing_m": "1",
            },
        )
    )
    assert isinstance(source, ScenarioSource)
    assert source.config["sample_rate_hz"] == 3
    assert source.config["sample_interval_s"] == Decimal("0.333333")
    assert source_timeline(source.config)[-1] == 15
    source = load_config(
        scenario_file(
            tmp_path,
            {
                "target_altitude_m": "0.3333334",
                "hover_duration_s": "0.6666666",
                "northbound_distance_m": "3",
                "cruise_speed_mps": "3",
                "descent_rate_mps": "0.3333334",
                "observation_spacing_m": "1",
            },
        )
    )
    assert isinstance(source, ScenarioSource)
    assert source.config["target_altitude_m"] == Decimal("0.3333334")
    assert source_timeline(source.config)[-1] == 12


def test_FR011_preserve_source_decimal_beyond_float_precision(tmp_path):
    source = load_config(
        scenario_file(
            tmp_path,
            {
                "battery_drain_percent_per_s": "0.123456789012345678901234567890123456",
                "scenario_version": '"2.3.4"',
                "seed": "0",
            },
        )
    )
    assert isinstance(source, ScenarioSource)
    assert source.config["battery_drain_percent_per_s"] == Decimal(
        "0.123456789012345678901234567890123456"
    )
    assert (source.version, source.seed) == ("2.3.4", 0)


def test_FR009_zero_hover_drain_and_terminal_battery_are_accepted(tmp_path):
    source = load_config(
        scenario_file(
            tmp_path,
            {
                "hover_duration_s": "0",
                "initial_battery_percent": "0",
                "battery_drain_percent_per_s": "0",
            },
        )
    )
    assert isinstance(source, ScenarioSource)
    assert source_timeline(source.config)[-1] == 400
    source = load_config(scenario_file(tmp_path, {"initial_battery_percent": "9"}))
    assert isinstance(source, ScenarioSource)


def test_FR001_read_and_toml_errors_identify_scenario_path(tmp_path):
    path = tmp_path / "missing.toml"
    with pytest.raises(ValueError, match="missing.toml"):
        load_config(path)
    path.write_text("target_altitude_m = [")
    with pytest.raises(ValueError, match="missing.toml"):
        load_config(path)
