"""Literal artifact inputs shared by contract and downstream story tests."""

import json
from decimal import Decimal
from pathlib import Path

import pytest


@pytest.fixture
def artifact_pair():
    root = Path(__file__).parent / "fixtures" / "valid_artifacts"
    return tuple(
        json.loads((root / name).read_text(encoding="utf-8"), parse_float=Decimal)
        for name in ("telemetry.json", "ground-truth.json")
    )
