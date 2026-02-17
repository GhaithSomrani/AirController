from dataclasses import dataclass
from typing import Dict


@dataclass
class GestureState:
    """Track timing for gesture debouncing."""

    last_click_time: float = 0.0
    last_scroll_time: float = 0.0


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


def detect_gestures_for_frame(frame_state) -> Dict[str, str]:
    """Return gesture dictionary keyed by hand side."""
    output: Dict[str, str] = {}
    for hand in frame_state.hands:
        output[hand.side] = detect_simple_gesture(hand.landmarks)
    return output

