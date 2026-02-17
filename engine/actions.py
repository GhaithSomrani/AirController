import json
from pathlib import Path
import time
import webbrowser

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
        profile_path: Path | None = None,
    ):
        self.click_cooldown = click_cooldown
        self.scroll_cooldown = scroll_cooldown
        self.scroll_amount = scroll_amount
        self.cursor_alpha = cursor_alpha
        self.gesture_state = GestureState()
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        self.last_dynamic_time = 0.0
        self.dynamic_cooldown = 0.30
        self.mappings = []
        self.actions = {}
        self.last_triggered = {}

        self.screen_w, self.screen_h = pyautogui.size()
        self._load_profile(profile_path)

    def _load_profile(self, profile_path: Path | None):
        if not profile_path:
            return
        if not profile_path.exists():
            print(f"Warning: profile not found: {profile_path}")
            return

        data = json.loads(profile_path.read_text(encoding="utf-8"))
        self.mappings = data.get("mappings", [])
        self.actions = data.get("actions", {})
        self.dynamic_cooldown = float(data.get("global", {}).get("dynamic_cooldown", 0.30))

    def _execute_action(self, action_id: str):
        action = self.actions.get(action_id)
        if not action:
            return

        kind = action.get("type")

        if kind == "mouse_click":
            pyautogui.click(button=action.get("button", "left"))
            return
        if kind == "scroll":
            pyautogui.scroll(int(action.get("amount", self.scroll_amount)))
            return
        if kind == "key":
            pyautogui.press(action.get("key", "space"))
            return
        if kind == "hotkey":
            keys = action.get("keys", [])
            if keys:
                pyautogui.hotkey(*keys)
            return
        if kind == "open_url":
            url = action.get("url", "")
            if url:
                webbrowser.open(url, new=2)
            return
        if kind == "type_text":
            pyautogui.write(action.get("text", ""), interval=0.02)
            return
        if kind == "sequence":
            steps = action.get("steps", [])
            for step in steps:
                self._execute_inline_step(step)
            return

    def _execute_inline_step(self, step):
        kind = step.get("type")
        if kind == "sleep":
            time.sleep(float(step.get("seconds", 0.1)))
            return
        if kind == "key":
            pyautogui.press(step.get("key", "space"))
            return
        if kind == "hotkey":
            keys = step.get("keys", [])
            if keys:
                pyautogui.hotkey(*keys)
            return
        if kind == "type_text":
            pyautogui.write(step.get("text", ""), interval=0.02)
            return
        if kind == "open_url":
            url = step.get("url", "")
            if url:
                webbrowser.open(url, new=2)
            return

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
        """Apply configured mappings; fallback to built-in defaults if no profile."""
        now = time.time()
        right = gestures.get("RIGHT")
        left = gestures.get("LEFT")
        right_name = right.name if right else None
        left_name = left.name if left else None

        if self.mappings and self.actions:
            candidates = []
            for mapping in self.mappings:
                side = mapping.get("side", "RIGHT")
                required_name = mapping.get("gesture")
                action_id = mapping.get("action")
                min_conf = float(mapping.get("min_confidence", 0.80))
                priority = int(mapping.get("priority", 0))
                cooldown = float(mapping.get("cooldown_s", self.dynamic_cooldown))

                cand = gestures.get(side)
                if not cand:
                    continue
                if cand.name != required_name or cand.confidence < min_conf:
                    continue

                mapping_key = f"{side}:{required_name}:{action_id}"
                if now - self.last_triggered.get(mapping_key, 0.0) < cooldown:
                    continue

                candidates.append((priority, cand.confidence, mapping_key, side, cand, action_id))

            if candidates:
                candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
                _, _, mapping_key, side, cand, action_id = candidates[0]
                self._execute_action(action_id)
                self.last_triggered[mapping_key] = now
                return f"{side} {cand.name} ({cand.confidence:.2f}) -> {action_id}"

            return "Tracking hands (profile mode)"

        action_text = "Tracking hands"
        if right_name == "PINCH":
            action_text = f"RIGHT PINCH ({right.confidence:.2f}) -> LEFT CLICK"
            if now - self.gesture_state.last_click_time >= self.click_cooldown:
                pyautogui.click(button="left")
                self.gesture_state.last_click_time = now
        elif left_name == "PINCH":
            action_text = f"LEFT PINCH ({left.confidence:.2f}) -> RIGHT CLICK"
            if now - self.gesture_state.last_click_time >= self.click_cooldown:
                pyautogui.click(button="right")
                self.gesture_state.last_click_time = now
        elif right_name == "TWO_UP":
            action_text = f"RIGHT TWO UP ({right.confidence:.2f}) -> SCROLL UP"
            if now - self.gesture_state.last_scroll_time >= self.scroll_cooldown:
                pyautogui.scroll(self.scroll_amount)
                self.gesture_state.last_scroll_time = now
        elif right_name == "TWO_DOWN":
            action_text = f"RIGHT TWO DOWN ({right.confidence:.2f}) -> SCROLL DOWN"
            if now - self.gesture_state.last_scroll_time >= self.scroll_cooldown:
                pyautogui.scroll(-self.scroll_amount)
                self.gesture_state.last_scroll_time = now
        elif right_name == "OPEN_PALM" or left_name == "OPEN_PALM":
            action_text = "OPEN PALM -> NO ACTION"
        elif right_name in {"SWIPE_LEFT", "SWIPE_RIGHT", "SWIPE_UP", "SWIPE_DOWN", "PUSH", "PULL"}:
            action_text = f"RIGHT {right_name} ({right.confidence:.2f})"
            if now - self.last_dynamic_time >= 0.30:
                if right_name == "SWIPE_LEFT":
                    pyautogui.press("left")
                elif right_name == "SWIPE_RIGHT":
                    pyautogui.press("right")
                elif right_name == "SWIPE_UP":
                    pyautogui.press("pageup")
                elif right_name == "SWIPE_DOWN":
                    pyautogui.press("pagedown")
                elif right_name == "PUSH":
                    pyautogui.hotkey("ctrl", "+")
                elif right_name == "PULL":
                    pyautogui.hotkey("ctrl", "-")
                self.last_dynamic_time = now
        else:
            action_text = "Tracking hands"

        return action_text
