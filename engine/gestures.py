from collections import deque
from dataclasses import dataclass
from typing import Deque
from typing import Dict
from typing import List
from typing import Optional


@dataclass
class GestureState:
    """Track timing for gesture debouncing."""

    last_click_time: float = 0.0
    last_scroll_time: float = 0.0


@dataclass
class GestureCandidate:
    name: str
    confidence: float
    source: str  # STATIC or DYNAMIC


def _distance(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def _is_finger_up(landmarks, tip_id, pip_id):
    return landmarks[tip_id].y < landmarks[pip_id].y


def detect_simple_gesture(lm):
    """Return one of: PINCH, TWO_UP, TWO_DOWN, OPEN_PALM, or None."""
    thumb_tip = (lm[4].x, lm[4].y)
    index_tip = (lm[8].x, lm[8].y)

    index_up = _is_finger_up(lm, tip_id=8, pip_id=6)
    middle_up = _is_finger_up(lm, tip_id=12, pip_id=10)

    if _distance(thumb_tip, index_tip) < 0.05:
        return "PINCH"

    ring_up = _is_finger_up(lm, tip_id=16, pip_id=14)
    pinky_up = _is_finger_up(lm, tip_id=20, pip_id=18)
    if index_up and middle_up and ring_up and pinky_up:
        return "OPEN_PALM"

    if index_up and middle_up:
        return "TWO_UP"

    wrist_y = lm[0].y
    if (not index_up) and (not middle_up):
        if lm[8].y > wrist_y and lm[12].y > wrist_y:
            return "TWO_DOWN"

    return None


def _candidate(name: str, confidence: float, source: str) -> GestureCandidate:
    return GestureCandidate(name=name, confidence=max(0.0, min(confidence, 1.0)), source=source)


class GestureRecognizer:
    """
    Hybrid recognizer:
    - static gestures from single frame landmarks
    - dynamic gestures from temporal motion window
    """

    def __init__(self, history_size: int = 18):
        self.history_size = history_size
        self.history: Dict[str, Deque] = {}

        # Dynamic thresholds in normalized camera units.
        self.swipe_dx_threshold = 0.12
        self.swipe_dy_threshold = 0.12
        self.push_pull_dz_threshold = 0.045
        self.min_avg_speed = 0.8

    def _update_history(self, frame_state):
        for hand in frame_state.hands:
            if hand.side not in self.history:
                self.history[hand.side] = deque(maxlen=self.history_size)
            self.history[hand.side].append(hand)

    def _detect_static_for_hand(self, hand) -> Optional[GestureCandidate]:
        name = detect_simple_gesture(hand.landmarks)
        if not name:
            return None

        # Static confidence can be refined later with explicit geometric margins.
        return _candidate(name=name, confidence=0.82, source="STATIC")

    def _detect_dynamic_for_hand(self, side: str) -> Optional[GestureCandidate]:
        points: List = list(self.history.get(side, []))
        if len(points) < 6:
            return None

        first = points[0]
        last = points[-1]

        dx = last.position.x - first.position.x
        dy = last.position.y - first.position.y
        dz = last.position.z - first.position.z

        avg_speed = sum(p.speed for p in points) / len(points)
        duration_s = max((last.timestamp_ms - first.timestamp_ms) / 1000.0, 1e-3)

        # Require enough temporal energy so small jitter is ignored.
        if avg_speed < self.min_avg_speed and duration_s < 0.12:
            return None

        abs_dx = abs(dx)
        abs_dy = abs(dy)
        abs_dz = abs(dz)

        if abs_dx > self.swipe_dx_threshold and abs_dx > abs_dy:
            conf = min(1.0, abs_dx / self.swipe_dx_threshold) * 0.7 + min(0.3, avg_speed / 3.0)
            return _candidate("SWIPE_RIGHT" if dx > 0 else "SWIPE_LEFT", conf, "DYNAMIC")

        if abs_dy > self.swipe_dy_threshold and abs_dy > abs_dx:
            conf = min(1.0, abs_dy / self.swipe_dy_threshold) * 0.7 + min(0.3, avg_speed / 3.0)
            return _candidate("SWIPE_DOWN" if dy > 0 else "SWIPE_UP", conf, "DYNAMIC")

        if abs_dz > self.push_pull_dz_threshold:
            conf = min(1.0, abs_dz / self.push_pull_dz_threshold) * 0.7 + min(0.3, avg_speed / 3.0)
            # MediaPipe z gets more negative when hand moves closer.
            return _candidate("PUSH" if dz > 0 else "PULL", conf, "DYNAMIC")

        return None

    def detect_for_frame(self, frame_state) -> Dict[str, GestureCandidate]:
        """
        Return best gesture candidate by hand side.
        Dynamic gestures are favored only when confidence is strong.
        """
        self._update_history(frame_state)
        output: Dict[str, GestureCandidate] = {}

        for hand in frame_state.hands:
            static_candidate = self._detect_static_for_hand(hand)
            dynamic_candidate = self._detect_dynamic_for_hand(hand.side)

            if dynamic_candidate and dynamic_candidate.confidence >= 0.86:
                output[hand.side] = dynamic_candidate
            elif static_candidate:
                output[hand.side] = static_candidate
            elif dynamic_candidate:
                output[hand.side] = dynamic_candidate

        return output
