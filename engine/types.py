from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class Vec3:
    x: float
    y: float
    z: float


@dataclass
class HandObservation:
    """Raw tracker output for one hand in current frame."""

    side: str  # LEFT or RIGHT
    landmarks: Sequence
    confidence: float


@dataclass
class HandState:
    """Smoothed motion state for one hand."""

    side: str
    confidence: float
    landmarks: Sequence
    position: Vec3
    velocity: Vec3
    acceleration: Vec3
    speed: float
    acceleration_magnitude: float
    depth: float
    timestamp_ms: int


@dataclass
class FrameState:
    """State container for the current frame."""

    hands: List[HandState]
    right_hand: Optional[HandState]
    left_hand: Optional[HandState]

