"""FR-017/FR-018, SC-006: permanent, independently authored gate violations."""

from pathlib import Path

import pytest

from assertion_engine.artifacts import (
    ArtifactValidationError,
    canonical_bytes,
    decode_json,
    validate_pair,
)

INVALID = Path(__file__).parents[1] / "fixtures" / "invalid_artifacts"

# T003 transcribed by hand into the data-model.md canonical byte format.
# This oracle is independent of both the generator and canonical_bytes.
CANONICAL_TELEMETRY = (
    b'{"artifact_version":"1.0.0","scenario":{"config":'
    b'{"battery_drain_percent_per_s":0.2,"climb_rate_mps":1,'
    b'"cruise_speed_mps":1,"descent_rate_mps":1,"hover_duration_s":1,'
    b'"initial_battery_percent":100,"northbound_distance_m":1,'
    b'"observation_spacing_m":1,"sample_interval_s":1,"sample_rate_hz":1,'
    b'"schema_version":"1.0.0","target_altitude_m":1,'
    b'"vehicle_id":"vehicle-001"},"name":"fixture-flight",'
    b'"seed":42,"version":"1.0.0"},"snapshots":['
    b'{"battery_percent":100,"mission_time_s":0,"position_ned_m":[0,0,0],'
    b'"sequence_number":0,"vehicle_id":"vehicle-001","velocity_ned_mps":[0,0,-1]},'
    b'{"battery_percent":99.8,"mission_time_s":1,"position_ned_m":[0,0,-1],'
    b'"sequence_number":1,"vehicle_id":"vehicle-001","velocity_ned_mps":[0,0,0]},'
    b'{"battery_percent":99.6,"mission_time_s":2,"position_ned_m":[0,0,-1],'
    b'"sequence_number":2,"vehicle_id":"vehicle-001","velocity_ned_mps":[1,0,0]},'
    b'{"battery_percent":99.4,"mission_time_s":3,"position_ned_m":[1,0,-1],'
    b'"sequence_number":3,"vehicle_id":"vehicle-001","velocity_ned_mps":[-1,0,0]},'
    b'{"battery_percent":99.2,"mission_time_s":4,"position_ned_m":[0,0,-1],'
    b'"sequence_number":4,"vehicle_id":"vehicle-001","velocity_ned_mps":[0,0,1]},'
    b'{"battery_percent":99,"mission_time_s":5,"position_ned_m":[0,0,0],'
    b'"sequence_number":5,"vehicle_id":"vehicle-001","velocity_ned_mps":[0,0,0]}]}\n'
)


def assert_canonical_telemetry(data):
    # A test-level byte gate: validate_pair deliberately accepts decoded documents.
    assert data == CANONICAL_TELEMETRY, "FR-011/FR-018 SC-006: noncanonical bytes"


def test_FR004_FR010_SC002_extra_phase_rejected(artifact_pair):
    telemetry, truth = artifact_pair
    invalid = decode_json((INVALID / "extra-phase.telemetry.json").read_bytes())
    with pytest.raises(
        ArtifactValidationError,
        match=r"snapshots\.0: Additional properties.*'phase'.*unexpected",
    ):
        validate_pair(invalid, truth)
    assert invalid["snapshots"][0].pop("phase") == "takeoff"
    assert invalid == telemetry  # Exactly one added field, no other defect.


def test_FR004_SC002_missing_field_rejected(artifact_pair):
    telemetry, truth = artifact_pair
    invalid = decode_json((INVALID / "missing-field.telemetry.json").read_bytes())
    with pytest.raises(
        ArtifactValidationError,
        match=r"snapshots\.0: 'battery_percent' is a required property",
    ):
        validate_pair(invalid, truth)
    assert "battery_percent" not in invalid["snapshots"][0]
    invalid["snapshots"][0]["battery_percent"] = 100
    assert invalid == telemetry


def test_FR006_SC002_wrong_sequence_rejected(artifact_pair):
    telemetry, truth = artifact_pair
    invalid = decode_json((INVALID / "wrong-sequence.telemetry.json").read_bytes())
    with pytest.raises(
        ArtifactValidationError,
        match=r"snapshots\[2\]\.sequence_number is not contiguous",
    ):
        validate_pair(invalid, truth)
    assert invalid["snapshots"][2]["sequence_number"] == 3
    invalid["snapshots"][2]["sequence_number"] = 2
    assert invalid == telemetry


def test_FR011_mismatched_source_rejected(artifact_pair):
    telemetry, truth = artifact_pair
    invalid = decode_json(
        (INVALID / "mismatched-source.ground-truth.json").read_bytes()
    )
    with pytest.raises(
        ArtifactValidationError, match="artifact pair scenario source differs"
    ):
        validate_pair(telemetry, invalid)
    assert invalid["scenario"]["seed"] == 43
    invalid["scenario"]["seed"] = 42
    assert invalid == truth


def test_FR011_FR018_SC006_canonical_positive_controls(artifact_pair):
    telemetry, truth = artifact_pair
    assert decode_json(CANONICAL_TELEMETRY) == telemetry
    typed, _ = validate_pair(telemetry, truth)
    assert_canonical_telemetry(CANONICAL_TELEMETRY)
    assert_canonical_telemetry(canonical_bytes(telemetry))
    assert_canonical_telemetry(canonical_bytes(typed))


def test_FR011_FR018_SC006_noncanonical_bytes_rejected(artifact_pair):
    telemetry, truth = artifact_pair
    invalid = (INVALID / "noncanonical.telemetry.json").read_bytes()
    # Formatting is the only defect; the shape and paired semantics remain valid.
    document = decode_json(invalid)
    assert document == telemetry
    validate_pair(document, truth)
    with pytest.raises(AssertionError, match="FR-011/FR-018 SC-006: noncanonical"):
        assert_canonical_telemetry(invalid)
    assert invalid == CANONICAL_TELEMETRY + b"\n"
