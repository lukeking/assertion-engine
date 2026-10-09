"""FR-013: fixture-only validation and immutable read-only playback loading."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from assertion_engine.artifacts import ArtifactValidationError, canonical_bytes
from assertion_engine.playback.loader import load_pair


def write_pair(tmp_path, pair):
    paths = (tmp_path / "telemetry.json", tmp_path / "ground-truth.json")
    for path, document in zip(paths, pair):
        path.write_bytes(canonical_bytes(document))
    return paths


def hashes(paths):
    return tuple(sha256(path.read_bytes()).hexdigest() for path in paths)


def test_load_immutable_fixture_pair(tmp_path, artifact_pair):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    telemetry, truth = load_pair(*paths)
    assert len(telemetry.snapshots) == 6
    assert truth.phases[-1].start_sequence_number == 4
    assert telemetry.scenario == truth.scenario
    assert isinstance(telemetry.snapshots, tuple)
    assert isinstance(truth.phases, tuple)
    with pytest.raises(FrozenInstanceError):
        telemetry.snapshots[0].battery_percent = 0
    with pytest.raises(TypeError):
        telemetry.scenario.config["vehicle_id"] = "changed"
    assert hashes(paths) == before


@pytest.mark.parametrize(
    ("side", "path", "value", "reason"),
    [
        (0, ("snapshots", 0, "battery_percent"), None, "battery_percent"),
        (0, ("snapshots", 2, "sequence_number"), 3, "sequence_number"),
        (0, ("artifact_version",), "9.0.0", "artifact_version"),
        (1, ("artifact_version",), "9.0.0", "artifact_version"),
        (1, ("scenario", "seed"), 43, "scenario"),
        (1, ("phases", 0, "name"), "hover", "phase"),
        (1, ("phases", 1, "start_sequence_number"), None, "start_sequence_number"),
        (1, ("phases", 1, "start_sequence_number"), 2, "start_sequence_number"),
        (1, ("phases", 1, "start_time_s"), 2, "start_time_s"),
    ],
)
def test_invalid_pair_rejected_without_changes(
    tmp_path, artifact_pair, side, path, value, reason
):
    pair = deepcopy(artifact_pair)
    target = pair[side]
    for key in path[:-1]:
        target = target[key]
    if value is None:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    paths = write_pair(tmp_path, pair)
    before = hashes(paths)
    with pytest.raises(ArtifactValidationError, match=reason):
        load_pair(*paths)
    assert hashes(paths) == before


def test_legacy_truth_explicit_migration_and_no_enrichment(tmp_path, artifact_pair):
    artifact_pair[1]["artifact_version"] = "1.0.0"
    for phase in artifact_pair[1]["phases"]:
        del phase["start_sequence_number"]
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    with pytest.raises(ArtifactValidationError) as error:
        load_pair(*paths)
    message = str(error.value).lower()
    for expected in ("1.0.0", "regenerate", "same", "version", "seed", "new", "retain"):
        assert expected in message
    assert hashes(paths) == before


@pytest.mark.parametrize("invalid", [b"{", b"[]", b'{"x":NaN}'])
def test_malformed_json_rejected(tmp_path, artifact_pair, invalid):
    paths = write_pair(tmp_path, artifact_pair)
    paths[0].write_bytes(invalid)
    with pytest.raises(ArtifactValidationError, match="JSON"):
        load_pair(*paths)


@pytest.mark.parametrize("side", [0, 1])
def test_noncanonical_bytes_rejected(tmp_path, artifact_pair, side):
    paths = write_pair(tmp_path, artifact_pair)
    paths[side].write_bytes(b" " + paths[side].read_bytes())
    before = hashes(paths)
    with pytest.raises(ArtifactValidationError, match="canonical"):
        load_pair(*paths)
    assert hashes(paths) == before


def test_missing_input_identifies_path(tmp_path, artifact_pair):
    paths = write_pair(tmp_path, artifact_pair)
    paths[0].unlink()
    with pytest.raises(ArtifactValidationError, match="telemetry.json"):
        load_pair(*paths)
