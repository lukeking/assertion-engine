"""Read-only event cursor and display derivations, independent of I/O and GUI.

Algorithm source: docs/algorithms/001-m0-telemetry-and-playback.md §3.
The cursor flips through saved snapshots; phase ownership reads sequence boundaries.
Altitude is minus the stored down coordinate, and speed is the stored vector's norm.
The viewing clock controls when to flip, without changing any event or timeline.
"""

import math
from collections.abc import Callable
from fractions import Fraction
from time import monotonic

from assertion_engine.telemetry import (
    GroundTruthArtifact,
    TelemetryArtifact,
    TelemetrySnapshot,
)


def altitude(snapshot: TelemetrySnapshot):
    return -snapshot.position_ned_m[2]


def scalar_speed(snapshot: TelemetrySnapshot) -> float:
    return math.hypot(*(float(value) for value in snapshot.velocity_ned_mps))


def _positive_speed(value) -> float:
    try:
        speed = float(value)
    except (ValueError, TypeError) as error:
        raise ValueError("speed must be finite and greater than zero") from error
    if not math.isfinite(speed) or speed <= 0:
        raise ValueError("speed must be finite and greater than zero")
    return speed


class PlaybackSession:
    """A mutable viewing cursor over an already validated immutable artifact pair."""

    def __init__(
        self,
        telemetry: TelemetryArtifact,
        ground_truth: GroundTruthArtifact,
        *,
        speed: float = 1.0,
        clock: Callable[[], float] = monotonic,
    ):
        self._telemetry = telemetry
        self._ground_truth = ground_truth
        self._cursor = 0
        self._state = "ready"
        self._speed = _positive_speed(speed)
        self._clock = clock
        self._last_clock = None
        self._progress = Fraction(0)

    @property
    def telemetry(self):
        return self._telemetry

    @property
    def ground_truth(self):
        return self._ground_truth

    @property
    def cursor(self):
        return self._cursor

    @property
    def state(self):
        return self._state

    @property
    def speed(self):
        return self._speed

    @property
    def snapshot(self):
        return self.telemetry.snapshots[self.cursor]

    @property
    def phase(self):
        return next(
            phase
            for phase in reversed(self.ground_truth.phases)
            if phase.start_sequence_number <= self.snapshot.sequence_number
        )

    @property
    def altitude_m(self):
        return altitude(self.snapshot)

    @property
    def scalar_speed_mps(self):
        return scalar_speed(self.snapshot)

    def play(self):
        if self.state in ("playing", "completed"):
            return
        self._last_clock = Fraction(str(self._clock()))
        self._state = "playing"

    def pause(self):
        self.tick()
        if self.state != "completed":
            self._state = "paused"
        self._last_clock = None

    def step(self):
        """Advance exactly one event and stop automatic advancement."""
        self._cursor = min(self.cursor + 1, len(self.telemetry.snapshots) - 1)
        self._progress = Fraction(0)
        self._last_clock = None
        self._state = (
            "completed"
            if self.cursor == len(self.telemetry.snapshots) - 1
            else "paused"
        )

    def restart(self):
        self._cursor = 0
        self._progress = Fraction(0)
        self._last_clock = None
        self._state = "ready"

    def tick(self):
        """Consume stored event-time gaps with elapsed wall time at the current rate."""
        if self.state != "playing":
            return
        # Exact decimal readings avoid drift without advancing frames by a tolerance.
        now = Fraction(str(self._clock()))
        self._progress += (now - self._last_clock) * Fraction(str(self.speed))
        self._last_clock = now
        snapshots = self.telemetry.snapshots
        while self.cursor < len(snapshots) - 1:
            gap = Fraction(str(snapshots[self.cursor + 1].mission_time_s)) - Fraction(
                str(self.snapshot.mission_time_s)
            )
            if self._progress < gap:
                break
            self._progress -= gap
            self._cursor += 1
        if self.cursor == len(snapshots) - 1:
            self._state = "completed"
            self._last_clock = None
            self._progress = Fraction(0)

    def set_speed(self, speed):
        validated = _positive_speed(speed)
        self.tick()  # Settle elapsed wall time at the old rate before changing it.
        self._speed = validated
