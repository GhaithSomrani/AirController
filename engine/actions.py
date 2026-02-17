import time

import pyautogui

from engine.gestures import GestureState


class ActionEngine:
    """Translate detected gestures into OS input actions."""

    def __init__(
        self,
        click_cooldown: float = 0.45,
        scroll_cooldown: float = 0.20,
        scroll_amount: int = 120,
        cursor_alpha: float = 0.25,
    ):
        self.click_cooldown = click_cooldown
        self.scroll_cooldown = scroll_cooldown
        self.scroll_amount = scroll_amount
        self.cursor_alpha = cursor_alpha
        self.gesture_state = GestureState()
        self.smooth_x = 0.0
        self.smooth_y = 0.0

        self.screen_w, self.screen_h = pyautogui.size()

    def move_cursor_from_hand(self, hand_state):
        index_tip = hand_state.landmarks[8]
        target_x = int(index_tip.x * self.screen_w)
        target_y = int(index_tip.y * self.screen_h)

        if self.smooth_x == 0 and self.smooth_y == 0:
            self.smooth_x, self.smooth_y = target_x, target_y
        else:
            self.smooth_x = self.smooth_x * (1 - self.cursor_alpha) + target_x * self.cursor_alpha
            self.smooth_y = self.smooth_y * (1 - self.cursor_alpha) + target_y * self.cursor_alpha

        pyautogui.moveTo(int(self.smooth_x), int(self.smooth_y))

    def apply(self, gestures):
        """
        Default mapping:
        - RIGHT PINCH -> left click
        - LEFT PINCH -> right click
        - RIGHT TWO_UP -> scroll up
        - RIGHT TWO_DOWN -> scroll down
        """
        now = time.time()
        action_text = "Tracking"

        right = gestures.get("RIGHT")
        left = gestures.get("LEFT")

        if right == "PINCH":
            action_text = "RIGHT PINCH -> LEFT CLICK"
            if now - self.gesture_state.last_click_time >= self.click_cooldown:
                pyautogui.click(button="left")
                self.gesture_state.last_click_time = now
        elif left == "PINCH":
            action_text = "LEFT PINCH -> RIGHT CLICK"
            if now - self.gesture_state.last_click_time >= self.click_cooldown:
                pyautogui.click(button="right")
                self.gesture_state.last_click_time = now
        elif right == "TWO_UP":
            action_text = "RIGHT TWO UP -> SCROLL UP"
            if now - self.gesture_state.last_scroll_time >= self.scroll_cooldown:
                pyautogui.scroll(self.scroll_amount)
                self.gesture_state.last_scroll_time = now
        elif right == "TWO_DOWN":
            action_text = "RIGHT TWO DOWN -> SCROLL DOWN"
            if now - self.gesture_state.last_scroll_time >= self.scroll_cooldown:
                pyautogui.scroll(-self.scroll_amount)
                self.gesture_state.last_scroll_time = now
        elif right == "OPEN_PALM" or left == "OPEN_PALM":
            action_text = "OPEN PALM -> NO ACTION"
        else:
            action_text = "Tracking hands"

        return action_text

