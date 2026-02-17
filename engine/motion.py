import math
from dataclasses import dataclass
from typing import Dict, List

from engine.types import FrameState
from engine.types import HandObservation
from engine.types import HandState
from engine.types import Vec3


@dataclass
class _History:
    position: Vec3
    velocity: Vec3
    acceleration: Vec3
    timestamp_ms: int


def _lerp(a: float, b: float, alpha: float) -> float:
    return (a * (1.0 - alpha)) + (b * alpha)


def _vec_lerp(a: Vec3, b: Vec3, alpha: float) -> Vec3:
    return Vec3(
        x=_lerp(a.x, b.x, alpha),
        y=_lerp(a.y, b.y, alpha),
        z=_lerp(a.z, b.z, alpha),
    )


def _vec_sub(a: Vec3, b: Vec3) -> Vec3:
    return Vec3(a.x - b.x, a.y - b.y, a.z - b.z)


def _vec_div(v: Vec3, scalar: float) -> Vec3:
    if scalar == 0:
        return Vec3(0.0, 0.0, 0.0)
    return Vec3(v.x / scalar, v.y / scalar, v.z / scalar)


def _vec_mag(v: Vec3) -> float:
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


class MotionEstimator:
    """Build per-hand motion state (position, velocity, acceleration)."""

    def __init__(self, smoothing_alpha: float = 0.35, max_stale_ms: int = 250):
        self.smoothing_alpha = smoothing_alpha
        self.max_stale_ms = max_stale_ms
        self._history: Dict[str, _History] = {}

    def _position_from_landmarks(self, landmarks) -> Vec3:
        # Index fingertip is used as control anchor for now.
        tip = landmarks[8]
        return Vec3(float(tip.x), float(tip.y), float(tip.z))

    def update(
        self, observations: List[HandObservation], timestamp_ms: int
    ) -> FrameState:
        hands: List[HandState] = []
        now = int(timestamp_ms)

        # Remove stale history entries.
        stale_sides = [
            side
            for side, hist in self._history.items()
            if now - hist.timestamp_ms > self.max_stale_ms
        ]
        for side in stale_sides:
            self._history.pop(side, None)

        for obs in observations:
            side = obs.side if obs.side in {"LEFT", "RIGHT"} else f"HAND_{len(hands)}"
            current = self._position_from_landmarks(obs.landmarks)

            if side not in self._history:
                pos = current
                vel = Vec3(0.0, 0.0, 0.0)
                acc = Vec3(0.0, 0.0, 0.0)
            else:
                prev = self._history[side]
                dt = max((now - prev.timestamp_ms) / 1000.0, 1e-3)

                pos = _vec_lerp(prev.position, current, self.smoothing_alpha)
                raw_vel = _vec_div(_vec_sub(pos, prev.position), dt)
                vel = _vec_lerp(prev.velocity, raw_vel, self.smoothing_alpha)

                raw_acc = _vec_div(_vec_sub(vel, prev.velocity), dt)
                acc = _vec_lerp(prev.acceleration, raw_acc, self.smoothing_alpha)

            speed = _vec_mag(vel)
            acc_mag = _vec_mag(acc)
            depth = -pos.z

            self._history[side] = _History(
                position=pos,
                velocity=vel,
                acceleration=acc,
                timestamp_ms=now,
            )

            hands.append(
                HandState(
                    side=side,
                    confidence=obs.confidence,
                    landmarks=obs.landmarks,
                    position=pos,
                    velocity=vel,
                    acceleration=acc,
                    speed=speed,
                    acceleration_magnitude=acc_mag,
                    depth=depth,
                    timestamp_ms=now,
                )
            )

        right = next((h for h in hands if h.side == "RIGHT"), None)
        left = next((h for h in hands if h.side == "LEFT"), None)
        return FrameState(hands=hands, right_hand=right, left_hand=left)

