"""
Dependencies (install with: pip install -r requirements.txt):
- opencv-python
- mediapipe
- pyautogui
- numpy
"""

from pathlib import Path
import time
import urllib.request
from dataclasses import dataclass

import cv2
import mediapipe as mp
import pyautogui


@dataclass
class GestureState:
    """Track timing for gesture debouncing."""

    last_click_time: float = 0.0
    last_scroll_time: float = 0.0


HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
]


def ensure_hand_model(model_path: Path):
    """
    Ensure the MediaPipe Hand Landmarker model exists locally.
    """
    if model_path.exists():
        return

    model_path.parent.mkdir(parents=True, exist_ok=True)
    url = (
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
        "hand_landmarker/float16/1/hand_landmarker.task"
    )
    print(f"Downloading model to {model_path} ...")
    urllib.request.urlretrieve(url, str(model_path))
    print("Model downloaded.")


def distance(p1, p2):
    """Euclidean distance between two 2D points."""
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def is_finger_up(landmarks, tip_id, pip_id):
    """
    Finger is considered up if tip is visually higher than pip in image space.
    In OpenCV image coordinates, smaller y means higher on the image.
    """
    return landmarks[tip_id].y < landmarks[pip_id].y


def get_gesture(lm):
    """
    Return one of:
    - "PINCH"
    - "TWO_UP"
    - "TWO_DOWN"
    - "OPEN_PALM"
    - None
    """
    # Landmark indices in MediaPipe Hands/Tasks:
    # thumb tip = 4, index tip = 8, middle tip = 12
    # index pip = 6, middle pip = 10
    thumb_tip = (lm[4].x, lm[4].y)
    index_tip = (lm[8].x, lm[8].y)
    middle_tip = (lm[12].x, lm[12].y)

    index_up = is_finger_up(lm, tip_id=8, pip_id=6)
    middle_up = is_finger_up(lm, tip_id=12, pip_id=10)

    if distance(thumb_tip, index_tip) < 0.05:
        return "PINCH"

    ring_up = is_finger_up(lm, tip_id=16, pip_id=14)
    pinky_up = is_finger_up(lm, tip_id=20, pip_id=18)
    if index_up and middle_up and ring_up and pinky_up:
        return "OPEN_PALM"

    if index_up and middle_up:
        return "TWO_UP"

    wrist_y = lm[0].y
    if (not index_up) and (not middle_up):
        if lm[8].y > wrist_y and lm[12].y > wrist_y:
            return "TWO_DOWN"

    return None


def draw_hand(frame, lm):
    """
    Draw landmarks and connections for a single hand.
    """
    h, w, _ = frame.shape

    for a, b in HAND_CONNECTIONS:
        ax, ay = int(lm[a].x * w), int(lm[a].y * h)
        bx, by = int(lm[b].x * w), int(lm[b].y * h)
        cv2.line(frame, (ax, ay), (bx, by), (0, 255, 0), 2)

    for point in lm:
        px, py = int(point.x * w), int(point.y * h)
        cv2.circle(frame, (px, py), 4, (0, 200, 255), -1)


def main():
    # Fail-safe lets you move mouse to a corner to stop PyAutoGUI actions.
    pyautogui.FAILSAFE = True

    # Small pause keeps actions stable and avoids accidental flooding.
    pyautogui.PAUSE = 0.01

    # Get monitor size once for mapping normalized [0..1] coords to pixels.
    screen_w, screen_h = pyautogui.size()

    # Webcam setup.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # MediaPipe Tasks Hand Landmarker setup.
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python import vision

    model_path = Path("models") / "hand_landmarker.task"
    ensure_hand_model(model_path)

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    hand_landmarker = vision.HandLandmarker.create_from_options(options)

    state = GestureState()

    # Smoothing state for mouse movement.
    smooth_x, smooth_y = 0.0, 0.0
    alpha = 0.25  # lower = smoother, higher = more responsive

    click_cooldown = 0.45  # seconds
    scroll_cooldown = 0.20  # seconds
    scroll_amount = 120

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # Mirror image for more intuitive control.
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # MediaPipe Tasks expects mp.Image in SRGB format.
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(time.time() * 1000)
            result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)

            action_text = "No hand"

            if result.hand_landmarks:
                lm = result.hand_landmarks[0]
                draw_hand(frame, lm)

                # Use index fingertip (id=8) for cursor tracking.
                index_tip = lm[8]

                # Map normalized coords to screen pixels.
                target_x = int(index_tip.x * screen_w)
                target_y = int(index_tip.y * screen_h)

                # Exponential smoothing to reduce jitter.
                if smooth_x == 0 and smooth_y == 0:
                    smooth_x, smooth_y = target_x, target_y
                else:
                    smooth_x = smooth_x * (1 - alpha) + target_x * alpha
                    smooth_y = smooth_y * (1 - alpha) + target_y * alpha

                pyautogui.moveTo(int(smooth_x), int(smooth_y))

                # Gesture detection + debounced actions.
                gesture = get_gesture(lm)
                now = time.time()

                if gesture == "PINCH":
                    action_text = "PINCH -> LEFT CLICK"
                    if now - state.last_click_time >= click_cooldown:
                        pyautogui.click(button="left")
                        state.last_click_time = now

                elif gesture == "TWO_UP":
                    action_text = "TWO UP -> SCROLL UP"
                    if now - state.last_scroll_time >= scroll_cooldown:
                        pyautogui.scroll(scroll_amount)
                        state.last_scroll_time = now

                elif gesture == "TWO_DOWN":
                    action_text = "TWO DOWN -> SCROLL DOWN"
                    if now - state.last_scroll_time >= scroll_cooldown:
                        pyautogui.scroll(-scroll_amount)
                        state.last_scroll_time = now

                elif gesture == "OPEN_PALM":
                    action_text = "OPEN PALM -> NO ACTION"
                else:
                    action_text = "Tracking cursor"

                # Draw fingertip marker.
                cv2.circle(
                    frame,
                    (int(index_tip.x * w), int(index_tip.y * h)),
                    8,
                    (0, 255, 255),
                    -1,
                )

            # Overlay status text.
            cv2.putText(
                frame,
                action_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                "Press 'q' to quit",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Hand Controller", frame)

            # Clean exit on q key.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        hand_landmarker.close()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
