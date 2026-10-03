"""Load canonical artifacts through the neutral validator without modifying inputs."""

from pathlib import Path

from assertion_engine.artifacts import (
    ArtifactValidationError,
    canonical_bytes,
    decode_json,
    validate_pair,
)
from assertion_engine.telemetry import GroundTruthArtifact, TelemetryArtifact


def load_pair(
    telemetry_path: str | Path, ground_truth_path: str | Path
) -> tuple[TelemetryArtifact, GroundTruthArtifact]:
    """Validate shape, source semantics and canonical bytes; return immutable values."""
    paths = (Path(telemetry_path), Path(ground_truth_path))
    raw = []
    for path in paths:
        try:
            raw.append(path.read_bytes())
        except (FileNotFoundError, IsADirectoryError) as error:
            raise ArtifactValidationError(
                f"invalid input path {path}: {error}"
            ) from error
    documents = tuple(decode_json(data) for data in raw)
    if documents[1].get("artifact_version") == "1.0.0":
        raise ArtifactValidationError(
            "ground truth 1.0.0 lacks sequence ownership boundaries; regenerate with "
            "the same scenario version, configuration and seed into a new output "
            "directory; retain the original artifacts"
        )
    pair = validate_pair(*documents)
    for path, data, document in zip(paths, raw, documents):
        if data != canonical_bytes(document):
            raise ArtifactValidationError(f"{path}: input bytes are not canonical JSON")
    return pair
