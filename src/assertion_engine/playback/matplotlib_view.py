"""Synchronized artists and controls over the read-only playback session.

Algorithm source: docs/algorithms/001-m0-telemetry-and-playback.md §4.
Like flipping through an album, the timer changes the current saved snapshot.
Every marker, cursor and label reads that one snapshot. Ground-truth rounded
times place annotations; the session's sequence lookup chooses current styling.
"""

from pathlib import Path

from assertion_engine.playback.view_model import PlaybackSession, altitude, scalar_speed

PHASE_COLORS = {
    "takeoff": "#0072B2",
    "hover": "#E69F00",
    "northbound": "#009E73",
    "return": "#CC79A7",
    "landing": "#D55E00",
}


class MatplotlibView:
    """GUI and Agg rendering share these artists and the same event cursor."""

    def __init__(self, session: PlaybackSession):
        # CLI selects Agg before this first pyplot import for headless rendering.
        from matplotlib import pyplot as plt
        from matplotlib.widgets import Button, Slider

        self.session = session
        self.figure = plt.figure(figsize=(12, 8))
        grid = self.figure.add_gridspec(3, 2, width_ratios=(1, 1.5))
        self.axes = {"route": self.figure.add_subplot(grid[:, 0])}
        for index, name in enumerate(("altitude", "speed", "battery")):
            self.axes[name] = self.figure.add_subplot(
                grid[index, 1],
                sharex=self.axes.get("altitude") if index else None,
            )
        self.figure.subplots_adjust(
            left=0.07, right=0.97, top=0.88, bottom=0.2, hspace=0.65, wspace=0.35
        )
        snapshots = session.telemetry.snapshots
        times = [float(snapshot.mission_time_s) for snapshot in snapshots]
        east = [float(snapshot.position_ned_m[1]) for snapshot in snapshots]
        north = [float(snapshot.position_ned_m[0]) for snapshot in snapshots]
        route = self.axes["route"]
        (self.route_line,) = route.plot(
            east, north, color="#677580", label="Saved route"
        )
        (self.marker,) = route.plot([], [], "o", markersize=9, label="Current snapshot")
        route.set(xlabel="East (m)", ylabel="North (m)", title="N/E route")
        route.set_aspect("equal", adjustable="datalim")
        route.grid(alpha=0.25)
        route.legend(loc="upper right", fontsize=8)
        self.series = {}
        self.cursors = {}
        values = {
            "altitude": [float(altitude(snapshot)) for snapshot in snapshots],
            "speed": [scalar_speed(snapshot) for snapshot in snapshots],
            "battery": [float(snapshot.battery_percent) for snapshot in snapshots],
        }
        labels = {
            "altitude": "Altitude (m)",
            "speed": "Speed (m/s)",
            "battery": "Battery (%)",
        }
        self.phase_annotations = []
        for name in ("altitude", "speed", "battery"):
            axis = self.axes[name]
            (self.series[name],) = axis.plot(times, values[name], color="#263746")
            self.cursors[name] = axis.axvline(times[0], linewidth=1.5)
            axis.set(xlabel="Mission time (s)", ylabel=labels[name])
            axis.grid(alpha=0.2)
            for phase in session.ground_truth.phases:
                start, end = float(phase.start_time_s), float(phase.end_time_s)
                axis.axvspan(start, end, color=PHASE_COLORS[phase.name], alpha=0.12)
                if name == "altitude":
                    self.phase_annotations.append(
                        axis.text(
                            (start + end) / 2,
                            1.04,
                            phase.name,
                            transform=axis.get_xaxis_transform(),
                            ha="center",
                            va="bottom",
                            fontsize=8,
                            rotation=25,
                            color=PHASE_COLORS[phase.name],
                        )
                    )
        self.phase_label = self.figure.text(0.07, 0.95, "", fontsize=12, weight="bold")
        self.buttons = {}
        for index, name in enumerate(("play", "pause", "step", "restart")):
            button = Button(
                self.figure.add_axes((0.07 + index * 0.105, 0.07, 0.09, 0.055)),
                name.title(),
            )
            button.on_clicked(getattr(self, f"_on_{name}"))
            self.buttons[name] = button
        self.speed_slider = Slider(
            self.figure.add_axes((0.61, 0.08, 0.32, 0.035)),
            "Speed",
            min(0.1, session.speed),
            max(10, session.speed),
            valinit=session.speed,
            valfmt="%1.2fx",
        )
        self.speed_slider.on_changed(self._on_speed)
        self.timer = self.figure.canvas.new_timer(interval=25)
        self.timer.add_callback(self._on_timer)
        self.figure.canvas.mpl_connect("close_event", lambda event: self.timer.stop())
        self.update()

    def update(self):
        snapshot = self.session.snapshot
        time = float(snapshot.mission_time_s)
        color = PHASE_COLORS[self.session.phase.name]
        self.marker.set_data(
            [float(snapshot.position_ned_m[1])], [float(snapshot.position_ned_m[0])]
        )
        self.marker.set_color(color)
        for cursor in self.cursors.values():
            cursor.set_xdata([time, time])
            cursor.set_color(color)
        self.phase_label.set_text(
            f"Phase: {self.session.phase.name}   |   Mission time: "
            f"{snapshot.mission_time_s} s   |   Snapshot: {snapshot.sequence_number}"
            f"   |   {self.session.state}"
        )
        self.figure.canvas.draw_idle()

    def _on_play(self, event):
        self.session.play()
        self.update()

    def _on_pause(self, event):
        self.session.pause()
        self.update()

    def _on_step(self, event):
        self.session.step()
        self.update()

    def _on_restart(self, event):
        self.session.restart()
        self.update()

    def _on_speed(self, value):
        self.session.set_speed(value)
        self.update()

    def _on_timer(self):
        if self.session.state == "playing":
            self.session.tick()
            self.update()

    def save(self, path: Path):
        self.update()
        self.figure.savefig(path, format="png", dpi=120)

    def show(self):
        from matplotlib import pyplot as plt

        self.timer.start()
        try:
            plt.show()
        finally:
            self.timer.stop()

    def close(self):
        from matplotlib import pyplot as plt

        self.timer.stop()
        plt.close(self.figure)
