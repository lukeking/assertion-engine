"""FR-015/SC-005: Agg artists and registered controls share a single cursor."""

import matplotlib
import matplotlib.image as mpl_image
import pytest

from assertion_engine.artifacts import validate_pair
from assertion_engine.playback.matplotlib_view import MatplotlibView
from assertion_engine.playback.view_model import PlaybackSession
from tests.unit.playback.test_view_model import Clock, a1_literal_pair


def test_drawn_route_series_annotations_and_synchronized_cursor(
    tmp_path, artifact_pair
):
    assert matplotlib.get_backend().lower() == "agg"
    session = PlaybackSession(*validate_pair(*artifact_pair))
    view = MatplotlibView(session)
    try:
        assert view.axes["route"].get_xlabel() == "East (m)"
        assert view.axes["route"].get_ylabel() == "North (m)"
        assert list(view.route_line.get_xdata()) == [0, 0, 0, 0, 0, 0]
        assert list(view.route_line.get_ydata()) == [0, 0, 0, 1, 0, 0]
        expected = {
            "altitude": [0, 1, 1, 1, 1, 0],
            "speed": [1, 0, 1, 1, 1, 0],
            "battery": [100, 99.8, 99.6, 99.4, 99.2, 99],
        }
        for name, values in expected.items():
            assert list(view.series[name].get_xdata()) == [0, 1, 2, 3, 4, 5]
            assert list(view.series[name].get_ydata()) == pytest.approx(values)
            assert view.axes[name].get_xlabel() == "Mission time (s)"
            assert view.axes[name].get_ylabel()
            assert [
                (span.get_x(), span.get_width()) for span in view.axes[name].patches
            ] == [
                (0, 1),
                (1, 1),
                (2, 1),
                (3, 1),
                (4, 1),
            ]
        assert [text.get_text() for text in view.phase_annotations] == [
            "takeoff",
            "hover",
            "northbound",
            "return",
            "landing",
        ]
        assert [text.get_position()[0] for text in view.phase_annotations] == [
            0.5,
            1.5,
            2.5,
            3.5,
            4.5,
        ]
        for _ in range(3):
            session.step()
        view.update()
        view.figure.canvas.draw()
        assert list(view.marker.get_xdata()) == [0]
        assert list(view.marker.get_ydata()) == [1]
        for cursor in view.cursors.values():
            assert list(cursor.get_xdata()) == [3, 3]
        assert "return" in view.phase_label.get_text()
        assert "3" in view.phase_label.get_text()
        output = tmp_path / "frame.png"
        view.save(output)
        pixels = mpl_image.imread(output)
        assert pixels.shape[0] >= 400
        assert pixels.shape[1] >= 600
        assert pixels[:, :, :3].std() > 0.05
    finally:
        view.close()


def test_registered_widget_callbacks_and_timer_advance_events(artifact_pair):
    clock = Clock()
    session = PlaybackSession(*validate_pair(*artifact_pair), clock=clock)
    view = MatplotlibView(session)
    try:
        view.buttons["play"]._observers.process("clicked", None)
        assert session.state == "playing"
        clock.advance(1.1)
        callback, args, kwargs = view.timer.callbacks[0]
        callback(*args, **kwargs)
        assert session.cursor == 1
        assert list(view.cursors["altitude"].get_xdata()) == [1, 1]
        view.buttons["pause"]._observers.process("clicked", None)
        assert session.state == "paused"
        clock.advance(100)
        view.buttons["step"]._observers.process("clicked", None)
        assert session.cursor == 2
        assert list(view.cursors["battery"].get_xdata()) == [2, 2]
        view.speed_slider.set_val(3)
        assert session.speed == 3
        assert session.snapshot.mission_time_s == 2
        view.buttons["restart"]._observers.process("clicked", None)
        assert (session.cursor, session.state) == (0, "ready")
        assert list(view.cursors["speed"].get_xdata()) == [0, 0]
        assert "takeoff" in view.phase_label.get_text()
    finally:
        view.close()


def test_A1_display_collision_uses_sequence_phase_for_label_and_marker(artifact_pair):
    session = PlaybackSession(*a1_literal_pair(artifact_pair))
    view = MatplotlibView(session)
    try:
        takeoff_color = view.marker.get_color()
        session.step()
        view.update()
        view.figure.canvas.draw()
        assert "takeoff" in view.phase_label.get_text()
        assert "0.333333" in view.phase_label.get_text()
        assert view.marker.get_color() == takeoff_color
        assert list(view.cursors["altitude"].get_xdata()) == [0.333333, 0.333333]
        session.step()
        view.update()
        assert "hover" in view.phase_label.get_text()
        assert view.marker.get_color() != takeoff_color
    finally:
        view.close()
