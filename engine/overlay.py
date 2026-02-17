import cv2


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


def draw_hand(frame, lm, color=(0, 255, 0)):
    h, w, _ = frame.shape

    for a, b in HAND_CONNECTIONS:
        ax, ay = int(lm[a].x * w), int(lm[a].y * h)
        bx, by = int(lm[b].x * w), int(lm[b].y * h)
        cv2.line(frame, (ax, ay), (bx, by), color, 2)

    for point in lm:
        px, py = int(point.x * w), int(point.y * h)
        cv2.circle(frame, (px, py), 4, (0, 200, 255), -1)


def draw_frame_overlay(frame, frame_state, action_text: str, gestures=None):
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

    y = 95
    for hand in frame_state.hands:
        line = (
            f"{hand.side} | depth={hand.depth:.3f} "
            f"speed={hand.speed:.3f} acc={hand.acceleration_magnitude:.3f}"
        )
        cv2.putText(
            frame,
            line,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 0),
            2,
        )
        y += 25

    if gestures:
        y += 5
        for side, candidate in gestures.items():
            line = f"{side} gesture={candidate.name} conf={candidate.confidence:.2f} src={candidate.source}"
            cv2.putText(
                frame,
                line,
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (180, 255, 180),
                2,
            )
            y += 22
