"""FR-011: byte expectations are literals, never target serializer output."""

from decimal import Decimal
from fractions import Fraction

import pytest

from assertion_engine.artifacts import (
    ArtifactValidationError,
    canonical_bytes,
    decode_json,
    quantize,
    validate_pair,
)


def test_FR011_sorted_compact_utf8_single_lf_repeated():
    value = {"z": [2, 1], "a": "中文"}
    expected = '{"a":"中文","z":[2,1]}\n'.encode()
    assert [canonical_bytes(value) for _ in range(3)] == [expected, expected, expected]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("0.0000005"), b'{"value":0}\n'),
        (Decimal("0.0000015"), b'{"value":0.000002}\n'),
        (Decimal("-0.0000005"), b'{"value":0}\n'),
        (Decimal("-0.0000015"), b'{"value":-0.000002}\n'),
        (Decimal("1.2345665"), b'{"value":1.234566}\n'),
        (Decimal("1.2345675"), b'{"value":1.234568}\n'),
        (Decimal("-0"), b'{"value":0}\n'),
        (-0.0, b'{"value":0}\n'),
        (Fraction(1, 3), b'{"value":0.333333}\n'),
        (Fraction(2, 3), b'{"value":0.666667}\n'),
    ],
)
def test_FR011_calculated_quantization(value, expected):
    assert canonical_bytes({"value": value}) == expected


def test_FR011_quantization_is_exact_ties_to_even():
    assert quantize(Fraction(1, 2_000_000)) == Decimal("0")
    assert quantize(Fraction(3, 2_000_000)) == Decimal("0.000002")
    assert quantize(Fraction(1, 3)) == Decimal("0.333333")
    assert quantize(Fraction(2, 3)) == Decimal("0.666667")


def test_FR011_source_inputs_preserved_derived_values_quantized():
    value = {
        "scenario": {
            "config": {
                "target_altitude_m": Decimal("0.3333334"),
                "hover_duration_s": Decimal("0.6666666"),
                "sample_interval_s": Fraction(1, 3),
                "sample_rate_hz": Fraction(3),
            }
        },
        "mission_time_s": Fraction(1, 3),
    }
    expected = (
        b'{"mission_time_s":0.333333,"scenario":{"config":'
        b'{"hover_duration_s":0.6666666,"sample_interval_s":0.333333,'
        b'"sample_rate_hz":3,"target_altitude_m":0.3333334}}}\n'
    )
    assert canonical_bytes(value) == expected


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), -float("inf"), Decimal("NaN"), Decimal("Infinity")],
)
def test_FR011_serialization_rejects_nonfinite(value):
    with pytest.raises(ArtifactValidationError):
        canonical_bytes({"scenario": {"config": {"target_altitude_m": value}}})
    with pytest.raises(ArtifactValidationError):
        quantize(value)


def test_FR011_decode_preserves_decimal_source_precision():
    decoded = decode_json('{"value":0.12345678901234567890123456789}')
    assert decoded["value"] == Decimal("0.12345678901234567890123456789")


@pytest.mark.parametrize("data", [b"\xff", "{", "[]", '{"x":}'])
def test_FR017_invalid_json_has_domain_error(data):
    with pytest.raises(ArtifactValidationError):
        decode_json(data)


def test_FR011_typed_pair_source_has_identical_canonical_bytes(artifact_pair):
    telemetry, truth = validate_pair(*artifact_pair)
    expected = (
        b'{"config":{"battery_drain_percent_per_s":0.2,"climb_rate_mps":1,'
        b'"cruise_speed_mps":1,"descent_rate_mps":1,"hover_duration_s":1,'
        b'"initial_battery_percent":100,"northbound_distance_m":1,'
        b'"observation_spacing_m":1,"sample_interval_s":1,"sample_rate_hz":1,'
        b'"schema_version":"1.0.0","target_altitude_m":1,'
        b'"vehicle_id":"vehicle-001"},"name":"fixture-flight",'
        b'"seed":42,"version":"1.0.0"}\n'
    )
    assert canonical_bytes(telemetry.scenario) == expected
    assert canonical_bytes(truth.scenario) == expected
    for typed in (telemetry, truth):
        encoded = canonical_bytes(typed)
        assert canonical_bytes(decode_json(encoded)) == encoded
