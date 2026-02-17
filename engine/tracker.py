from pathlib import Path
from typing import List

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision

from engine.model import ensure_hand_model
from engine.types import HandObservation


class HandTracker:
    """MediaPipe Tasks hand tracker wrapper."""

    def __init__(
        self,
        model_path: Path,
        num_hands: int = 2,
        min_detection_confidence: float = 0.6,
        min_presence_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ):
        ensure_hand_model(model_path)

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    def detect(self, frame_bgr, timestamp_ms: int) -> List[HandObservation]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        observations: List[HandObservation] = []
        if not result.hand_landmarks:
            return observations

        for i, landmarks in enumerate(result.hand_landmarks):
            handedness = "UNKNOWN"
            confidence = 0.0

            if i < len(result.handedness) and result.handedness[i]:
                handedness = result.handedness[i][0].category_name.upper()
                confidence = float(result.handedness[i][0].score)

            observations.append(
                HandObservation(
                    side=handedness,
                    landmarks=landmarks,
                    confidence=confidence,
                )
            )

        return observations

    def close(self) -> None:
        self._landmarker.close()

