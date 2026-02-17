from pathlib import Path
import urllib.request


DEFAULT_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


def ensure_hand_model(model_path: Path) -> None:
    """Ensure the MediaPipe hand model exists locally."""
    if model_path.exists():
        return

    model_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading model to {model_path} ...")
    urllib.request.urlretrieve(DEFAULT_MODEL_URL, str(model_path))
    print("Model downloaded.")

