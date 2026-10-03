"""FR-013–FR-015: real playback entrypoint, explicit tmp_path outputs, input hashes."""

import importlib.metadata
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import matplotlib
import matplotlib.image as mpl_image
import pytest

from assertion_engine.artifacts import canonical_bytes
from assertion_engine.playback import cli
from assertion_engine.playback.loader import load_pair
from assertion_engine.playback.matplotlib_view import MatplotlibView
from assertion_engine.playback.view_model import PlaybackSession


def write_pair(tmp_path, pair):
    paths = (tmp_path / "telemetry.json", tmp_path / "ground-truth.json")
    for path, document in zip(paths, pair):
        path.write_bytes(canonical_bytes(document))
    return paths


def hashes(paths):
    return tuple(sha256(path.read_bytes()).hexdigest() for path in paths)


def arguments(paths, output=None):
    result = ["--telemetry", str(paths[0]), "--ground-truth", str(paths[1])]
    if output is not None:
        result.extend(["--headless-output", str(output)])
    return result


def run_cli(args):
    env = {**os.environ, "MPLBACKEND": "Agg"}
    return subprocess.run(
        [sys.executable, "-m", "assertion_engine.playback.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_module_cli_renders_terminal_frame_without_window(
    tmp_path, artifact_pair, monkeypatch
):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    output = tmp_path / "terminal.png"
    result = run_cli([*arguments(paths, output), "--speed", "2.5"])
    assert result.returncode == 0, result.stderr
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert mpl_image.imread(output).std() > 0.05
    assert hashes(paths) == before

    # Run the same real main with only its rendering boundary observed.
    observed = {}
    original_save = MatplotlibView.save

    def save(view, path):
        observed["snapshot"] = view.session.snapshot
        observed["phase"] = view.session.phase.name
        observed["cursor"] = list(view.cursors["battery"].get_xdata())
        original_save(view, path)

    def fail_show(view):
        pytest.fail("headless playback must not open a window")

    monkeypatch.setattr(MatplotlibView, "save", save)
    monkeypatch.setattr(MatplotlibView, "show", fail_show)
    assert cli.main(arguments(paths, tmp_path / "observed.png")) == 0
    assert observed["snapshot"].sequence_number == 5
    assert observed["snapshot"].position_ned_m == (0, 0, 0)
    assert observed["phase"] == "landing"
    assert observed["cursor"] == [5, 5]
    assert hashes(paths) == before


def test_complete_control_sequence_never_changes_input_hashes(tmp_path, artifact_pair):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    now = [0.0]
    session = PlaybackSession(*load_pair(*paths), clock=lambda: now[0])
    session.play()
    now[0] = 1.25
    session.tick()
    session.pause()
    session.step()
    assert session.snapshot.mission_time_s == 2
    session.set_speed(4)
    session.play()
    now[0] += 1
    session.tick()
    assert session.state == "completed"
    assert session.snapshot.mission_time_s == 5
    session.restart()
    session.step()
    assert session.snapshot.mission_time_s == 1
    assert hashes(paths) == before


@pytest.mark.parametrize("speed", ["0", "-2", "nan", "inf", "invalid"])
def test_invalid_speed_has_no_output(tmp_path, artifact_pair, speed):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    output = tmp_path / "invalid.png"
    result = run_cli([*arguments(paths, output), "--speed", speed])
    assert result.returncode == 2
    assert "speed" in result.stderr.lower()
    assert not output.exists()
    assert hashes(paths) == before


@pytest.mark.parametrize(
    "kind", ["missing", "schema", "semantic", "source", "legacy", "canonical"]
)
def test_invalid_input_has_no_output(tmp_path, artifact_pair, kind):
    if kind == "schema":
        del artifact_pair[0]["snapshots"][0]["battery_percent"]
    elif kind == "semantic":
        artifact_pair[0]["snapshots"][2]["sequence_number"] = 4
    elif kind == "source":
        artifact_pair[1]["scenario"]["seed"] = 43
    elif kind == "legacy":
        artifact_pair[1]["artifact_version"] = "1.0.0"
        for phase in artifact_pair[1]["phases"]:
            del phase["start_sequence_number"]
    paths = write_pair(tmp_path, artifact_pair)
    if kind == "missing":
        paths[0].unlink()
    elif kind == "canonical":
        paths[0].write_bytes(b" " + paths[0].read_bytes())
    existing = tuple(path for path in paths if path.exists())
    before = hashes(existing)
    output = tmp_path / "rejected.png"
    result = run_cli(arguments(paths, output))
    assert result.returncode == 2
    assert result.stderr.strip()
    if kind == "legacy":
        assert "regenerate" in result.stderr.lower()
        assert "retain" in result.stderr.lower()
    assert not output.exists()
    assert hashes(existing) == before


def test_png_parent_must_exist_and_output_must_not_alias_input(tmp_path, artifact_pair):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    missing_parent = tmp_path / "absent" / "frame.png"
    result = run_cli(arguments(paths, missing_parent))
    assert result.returncode == 2
    assert "parent" in result.stderr.lower()
    assert not missing_parent.parent.exists()
    result = run_cli(arguments(paths, paths[0]))
    assert result.returncode == 2
    assert "input" in result.stderr.lower()
    alias = tmp_path / "alias.png"
    alias.symlink_to(paths[1])
    result = run_cli(arguments(paths, alias))
    assert result.returncode == 2
    assert hashes(paths) == before


@pytest.mark.parametrize("error_type", [OSError, ValueError, RuntimeError])
def test_render_failure_returns_one_preserves_inputs_and_cleans_staging(
    tmp_path, artifact_pair, monkeypatch, capsys, error_type
):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    output = tmp_path / "frame.png"
    output.write_bytes(b"previous output")

    def fail_save(view, path):
        path.write_bytes(b"partial image")
        raise error_type("render destination failed")

    monkeypatch.setattr(MatplotlibView, "save", fail_save)
    assert cli.main(arguments(paths, output)) == 1
    assert "render destination failed" in capsys.readouterr().err
    assert output.read_bytes() == b"previous output"
    assert hashes(paths) == before
    assert {path.name for path in tmp_path.iterdir()} == {
        "telemetry.json",
        "ground-truth.json",
        "frame.png",
    }


def test_gui_normal_close_returns_zero(tmp_path, artifact_pair, monkeypatch):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    observed = []
    monkeypatch.setattr(MatplotlibView, "show", lambda view: observed.append(view))
    assert cli.main(arguments(paths)) == 0
    assert len(observed) == 1
    assert observed[0].session.cursor == 0
    assert hashes(paths) == before


def test_headless_selects_agg_before_view_and_invalid_output_name_rejects(
    tmp_path, artifact_pair, monkeypatch, capsys
):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    seen = []
    original_init = MatplotlibView.__init__

    def init(view, session):
        seen.append(matplotlib.get_backend().lower())
        original_init(view, session)

    monkeypatch.setattr(MatplotlibView, "__init__", init)
    matplotlib.use("svg", force=True)
    try:
        assert cli.main(arguments(paths, tmp_path / "agg.png")) == 0
        assert seen == ["agg"]
    finally:
        matplotlib.use("Agg", force=True)
    assert cli.main([*arguments(paths), "--headless-output", ""]) == 2
    assert "file" in capsys.readouterr().err
    assert hashes(paths) == before


def test_unexpected_input_io_failure_is_operational_exit_one(
    tmp_path, artifact_pair, monkeypatch, capsys
):
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    output = tmp_path / "failed.png"

    def denied(*paths):
        raise PermissionError("input read denied")

    monkeypatch.setattr(cli, "load_pair", denied)
    assert cli.main(arguments(paths, output)) == 1
    assert "input read denied" in capsys.readouterr().err
    assert not output.exists()
    assert hashes(paths) == before


def test_installed_script_entrypoint(tmp_path, artifact_pair):
    registered = importlib.metadata.entry_points(group="console_scripts")
    if "assertion-playback" not in registered.names:
        pytest.skip("main must register playback after simulator releases pyproject")
    entry = registered["assertion-playback"]
    assert entry.value == "assertion_engine.playback.cli:main"
    paths = write_pair(tmp_path, artifact_pair)
    before = hashes(paths)
    output = tmp_path / "installed.png"
    result = subprocess.run(
        [
            str(Path(sys.executable).parent / "assertion-playback"),
            *arguments(paths, output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_bytes().startswith(b"\x89PNG")
    assert hashes(paths) == before
