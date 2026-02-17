"""
Dependencies (install with: pip install -r requirements.txt):
- opencv-python
- mediapipe
- pyautogui
- numpy
"""

from pathlib import Path
import time

import cv2
import pyautogui

from engine.actions import ActionEngine
from engine.gestures import detect_gestures_for_frame
from engine.motion import MotionEstimator
from engine.overlay import draw_frame_overlay
from engine.overlay import draw_hand
from engine.tracker import HandTracker


def pick_cursor_hand(frame_state):
    """
    Prefer RIGHT hand for cursor control.
    Fallback to LEFT, then first detected hand.
    """
    if frame_state.right_hand:
        return frame_state.right_hand
    if frame_state.left_hand:
        return frame_state.left_hand
    if frame_state.hands:
        return frame_state.hands[0]
    return None


def main():
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.01

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    model_path = Path("models") / "hand_landmarker.task"
    tracker = HandTracker(model_path=model_path, num_hands=2)
    motion = MotionEstimator(smoothing_alpha=0.35, max_stale_ms=250)
    actions = ActionEngine(
        click_cooldown=0.45,
        scroll_cooldown=0.20,
        scroll_amount=120,
        cursor_alpha=0.25,
    )

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            timestamp_ms = int(time.time() * 1000)

            observations = tracker.detect(frame, timestamp_ms)
            frame_state = motion.update(observations, timestamp_ms)

            # Draw all tracked hands.
            for hand in frame_state.hands:
                color = (255, 120, 0) if hand.side == "LEFT" else (0, 255, 0)
                draw_hand(frame, hand.landmarks, color=color)

            # Cursor hand and gesture handling.
            cursor_hand = pick_cursor_hand(frame_state)
            if cursor_hand:
                actions.move_cursor_from_hand(cursor_hand)

            gestures = detect_gestures_for_frame(frame_state)
            action_text = actions.apply(gestures)

            draw_frame_overlay(frame, frame_state, action_text)
            cv2.imshow("AirController", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

