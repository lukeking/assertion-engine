"""SC-001–003: the registered command publishes reproducible literal baseline."""

import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from assertion_engine.artifacts import decode_json, validate_pair

BASELINE_TOML = """schema_version = "1.0.0"
scenario_name = "normal-flight"
scenario_version = "1.0.0"
seed = 42
vehicle_id = "vehicle-001"
target_altitude_m = 10.0
climb_rate_mps = 1.0
hover_duration_s = 5.0
northbound_distance_m = 20.0
cruise_speed_mps = 2.0
descent_rate_mps = 1.0
observation_spacing_m = 0.2
initial_battery_percent = 100.0
battery_drain_percent_per_s = 0.2
"""


def test_SC001_three_runs_publish_complete_identical_pairs(tmp_path):
    scenario = tmp_path / "normal-flight.toml"
    scenario.write_text(BASELINE_TOML)
    executable = Path(sys.executable).parent / "assertion-sim"
    assert executable.is_file(), "test must exercise the registered console script"
    hashes = []
    pairs = []
    outputs = [tmp_path / "run1", tmp_path / "run2", tmp_path / "new" / "deep" / "run3"]
    for output in outputs:
        result = subprocess.run(
            [
                str(executable),
                "generate",
                "--scenario",
                str(scenario),
                "--output",
                str(output),
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        assert len(result.stdout.splitlines()) == 1
        report = json.loads(result.stdout)
        assert (
            result.stdout
            == json.dumps(report, separators=(",", ":"), sort_keys=True) + "\n"
        )
        assert set(report) == {
            "telemetry",
            "ground_truth",
            "telemetry_sha256",
            "ground_truth_sha256",
        }
        assert set(path.name for path in output.iterdir()) == {
            "telemetry.json",
            "ground-truth.json",
        }
        assert all("staging" not in p.name for p in output.parent.iterdir())
        pair = []
        for name, key in [
            ("telemetry.json", "telemetry"),
            ("ground-truth.json", "ground_truth"),
        ]:
            assert report[key] == str(output / name)
            data = (output / name).read_bytes()
            assert data.endswith(b"\n") and not data.endswith(b"\n\n")
            digest = hashlib.sha256(data).hexdigest()
            assert re.fullmatch("[0-9a-f]{64}", report[key + "_sha256"])
            assert digest == report[key + "_sha256"]
            pair.append(data)
        hashes.append((report["telemetry_sha256"], report["ground_truth_sha256"]))
        pairs.append(pair)
    assert hashes[0] == hashes[1] == hashes[2]
    assert pairs[0] == pairs[1] == pairs[2]
    # Logged hashes are evidence for T016, with destinations owned by tmp_path.
    print("CP3_REPRODUCTION_HASHES=" + json.dumps(hashes, separators=(",", ":")))
    telemetry, truth = [decode_json(data) for data in pairs[0]]
    validate_pair(telemetry, truth)
    assert telemetry["artifact_version"] == "1.0.0"
    assert truth["artifact_version"] == "2.0.0"
    assert (
        telemetry["scenario"]
        == truth["scenario"]
        == {
            "name": "normal-flight",
            "version": "1.0.0",
            "seed": 42,
            "config": {
                "schema_version": "1.0.0",
                "vehicle_id": "vehicle-001",
                "target_altitude_m": 10,
                "climb_rate_mps": 1,
                "hover_duration_s": 5,
                "northbound_distance_m": 20,
                "cruise_speed_mps": 2,
                "descent_rate_mps": 1,
                "observation_spacing_m": Decimal("0.2"),
                "sample_rate_hz": 10,
                "sample_interval_s": Decimal("0.1"),
                "initial_battery_percent": 100,
                "battery_drain_percent_per_s": Decimal("0.2"),
            },
        }
    )
    states = telemetry["snapshots"]
    assert len(states) == 451
    # Independent integer-index/decimal oracle checks every baseline snapshot.
    for k, snapshot in enumerate(states):
        time = Decimal(k) / 10
        if k < 100:
            position, velocity = [0, 0, -time], [0, 0, -1]
        elif k < 150:
            position, velocity = [0, 0, -10], [0, 0, 0]
        elif k < 250:
            position, velocity = [(Decimal(k) - 150) / 5, 0, -10], [2, 0, 0]
        elif k < 350:
            position, velocity = [(350 - Decimal(k)) / 5, 0, -10], [-2, 0, 0]
        elif k < 450:
            position, velocity = [0, 0, (Decimal(k) - 450) / 10], [0, 0, 1]
        else:
            position, velocity = [0, 0, 0], [0, 0, 0]
        assert snapshot == {
            "vehicle_id": "vehicle-001",
            "sequence_number": k,
            "mission_time_s": time,
            "position_ned_m": position,
            "velocity_ned_mps": velocity,
            "battery_percent": 100 - Decimal(k) / 50,
        }
    assert truth["terminal_time_s"] == 45
    assert truth["phases"] == [
        {
            "name": "takeoff",
            "start_time_s": 0,
            "end_time_s": 10,
            "start_sequence_number": 0,
        },
        {
            "name": "hover",
            "start_time_s": 10,
            "end_time_s": 15,
            "start_sequence_number": 100,
        },
        {
            "name": "northbound",
            "start_time_s": 15,
            "end_time_s": 25,
            "start_sequence_number": 150,
        },
        {
            "name": "return",
            "start_time_s": 25,
            "end_time_s": 35,
            "start_sequence_number": 250,
        },
        {
            "name": "landing",
            "start_time_s": 35,
            "end_time_s": 45,
            "start_sequence_number": 350,
        },
    ]


def test_T013_checked_in_baseline_matches_literal_source():
    import tomllib

    path = Path(__file__).resolve().parents[2] / "scenarios" / "normal-flight.toml"
    assert path.is_file()
    assert tomllib.loads(path.read_text()) == tomllib.loads(BASELINE_TOML)
