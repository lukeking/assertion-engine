"""FR-001 and CLI contract: actual main/entrypoint failures and write boundaries."""

import subprocess
import sys
from pathlib import Path

import pytest

from assertion_engine.artifacts import ArtifactValidationError
from assertion_engine.simulator import cli

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


@pytest.fixture
def scenario(tmp_path):
    path = tmp_path / "scenario.toml"
    path.write_text(BASELINE_TOML)
    return path


def arguments(scenario, output):
    return ["generate", "--scenario", str(scenario), "--output", str(output)]


@pytest.mark.parametrize(
    "mode", ["missing-scenario", "unknown-flag", "missing-command"]
)
def test_cli_invalid_arguments_have_no_parent_side_effects(
    tmp_path, scenario, capsys, mode
):
    output = tmp_path / "absent" / "nested" / "result"
    argv = arguments(scenario, output)
    if mode == "missing-scenario":
        argv = ["generate", "--output", str(output)]
    elif mode == "unknown-flag":
        argv += ["--unknown"]
    else:
        argv = argv[1:]
    assert cli.main(argv) == 2
    assert not (tmp_path / "absent").exists()
    assert not output.exists()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err


@pytest.mark.parametrize(
    ("before", "after", "diagnostic"),
    [
        ("seed = 42\n", "", "seed"),
        ("climb_rate_mps = 1.0", "climb_rate_mps = 0", "climb_rate_mps"),
        ("hover_duration_s = 5.0", "hover_duration_s = 5.05", "terminal"),
        ("hover_duration_s = 5.0", "hover_duration_s = 5.0000004", "terminal"),
        ("target_altitude_m = 10.0", "target_altitude_m = nan", "target_altitude_m"),
        ('schema_version = "1.0.0"', 'schema_version = "2.0.0"', "schema_version"),
    ],
)
def test_cli_invalid_config_has_no_parent_side_effects(
    tmp_path, scenario, capsys, before, after, diagnostic
):
    scenario.write_text(BASELINE_TOML.replace(before, after))
    output = tmp_path / "absent" / "nested" / "result"
    assert cli.main(arguments(scenario, output)) == 2
    assert not (tmp_path / "absent").exists()
    assert not output.exists()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert diagnostic in captured.err


@pytest.mark.parametrize("mode", ["directory", "file", "dangling-symlink"])
def test_cli_existing_target_is_preserved(tmp_path, scenario, capsys, mode):
    output = tmp_path / "existing"
    if mode == "directory":
        output.mkdir()
        sentinel = output / "sentinel"
        sentinel.write_bytes(b"original")
    elif mode == "file":
        output.write_bytes(b"original")
    else:
        output.symlink_to(tmp_path / "does-not-exist")
    assert cli.main(arguments(scenario, output)) == 2
    assert set(tmp_path.iterdir()) == {scenario, output}
    if mode == "directory":
        assert set(output.iterdir()) == {sentinel}
        assert sentinel.read_bytes() == b"original"
    elif mode == "file":
        assert output.read_bytes() == b"original"
    else:
        assert output.is_symlink()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert str(output) in captured.err


def test_cli_parent_creation_failure_is_operational(tmp_path, scenario, capsys):
    ancestor = tmp_path / "file-ancestor"
    ancestor.write_bytes(b"original")
    output = ancestor / "nested" / "result"
    assert cli.main(arguments(scenario, output)) == 1
    assert ancestor.read_bytes() == b"original"
    assert not output.exists()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert str(output.parent) in captured.err


@pytest.mark.parametrize(
    "boundary", ["mkdir", "staging", "telemetry.json", "ground-truth.json", "publish"]
)
def test_cli_operational_failures_clean_only_invocation_staging(
    tmp_path, scenario, monkeypatch, capsys, boundary
):
    parent = tmp_path / "parent"
    parent.mkdir()
    sentinel = parent / "sentinel"
    sentinel.write_bytes(b"original")
    output = parent / "result"

    def fail(*args, **kwargs):
        raise OSError("injected failure")

    if boundary == "mkdir":
        monkeypatch.setattr(Path, "mkdir", fail)
    elif boundary == "staging":
        import tempfile

        monkeypatch.setattr(tempfile, "mkdtemp", fail)
    elif boundary == "publish":
        monkeypatch.setattr(Path, "rename", fail)
    else:
        real_write = Path.write_bytes

        def write(path, data):
            if path.name == boundary:
                raise OSError("injected failure")
            return real_write(path, data)

        monkeypatch.setattr(Path, "write_bytes", write)
    assert cli.main(arguments(scenario, output)) == 1
    assert not output.exists()
    assert set(parent.iterdir()) == {sentinel}
    assert sentinel.read_bytes() == b"original"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert str(parent) in captured.err
    assert "injected failure" in captured.err


def test_cli_created_parents_remain_after_staging_failure(
    tmp_path, scenario, monkeypatch, capsys
):
    output = tmp_path / "new" / "nested" / "result"

    def fail(path, data):
        raise OSError("staging denied")

    monkeypatch.setattr(Path, "write_bytes", fail)
    assert cli.main(arguments(scenario, output)) == 1
    assert output.parent.is_dir()
    assert list(output.parent.iterdir()) == []
    assert not output.exists()
    assert str(output.parent) in capsys.readouterr().err


def test_cli_complete_pair_validation_precedes_all_directory_creation(
    tmp_path, scenario, monkeypatch, capsys
):
    output = tmp_path / "new" / "nested" / "result"
    calls = []

    def reject_pair(telemetry, truth):
        assert not (tmp_path / "new").exists()
        assert len(telemetry["snapshots"]) == 451
        assert truth["terminal_time_s"] == 45
        calls.append("validated")
        raise ArtifactValidationError("in-memory pair rejected")

    monkeypatch.setattr(cli, "validate_pair", reject_pair)
    assert cli.main(arguments(scenario, output)) == 1
    assert calls == ["validated"]
    assert not (tmp_path / "new").exists()
    assert not output.exists()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "in-memory pair rejected" in captured.err


@pytest.mark.parametrize("mode", ["invalid-config", "existing", "parent-file"])
def test_registered_cli_exit_codes_and_path_diagnostics(tmp_path, scenario, mode):
    executable = Path(sys.executable).parent / "assertion-sim"
    assert executable.is_file()
    output = tmp_path / "missing" / "nested" / "result"
    expected = 2
    diagnostic = "terminal"
    if mode == "invalid-config":
        scenario.write_text(
            BASELINE_TOML.replace(
                "hover_duration_s = 5.0", "hover_duration_s = 5.0000004"
            )
        )
    elif mode == "existing":
        output = tmp_path / "existing"
        output.mkdir()
        (output / "sentinel").write_bytes(b"original")
        diagnostic = str(output)
    else:
        ancestor = tmp_path / "file"
        ancestor.write_bytes(b"original")
        output = ancestor / "nested" / "result"
        expected = 1
        diagnostic = str(output.parent)
    result = subprocess.run(
        [str(executable), *arguments(scenario, output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected
    assert result.stdout == ""
    assert diagnostic in result.stderr
    assert not (tmp_path / "missing").exists()
    if mode == "existing":
        assert (output / "sentinel").read_bytes() == b"original"
        assert set(output.iterdir()) == {output / "sentinel"}
    else:
        assert not output.exists()
