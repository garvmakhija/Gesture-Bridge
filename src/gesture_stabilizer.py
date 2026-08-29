from collections import deque
import time


class GestureStabilizer:
    def __init__(self, window_size=5, cooldown=0.8):
        self.history = deque(maxlen=window_size)
        self.current_gesture = "NO HAND"
        self.last_event = "NO HAND"
        self.last_event_time = 0.0
        self.cooldown = cooldown

    def update(self, gesture):
        if gesture == "UNKNOWN":
            return self.current_gesture, None

        self.history.append(gesture)

        if len(self.history) < self.history.maxlen:
            return self.current_gesture, None

        if len(set(self.history)) != 1:
            return self.current_gesture, None

        stable_gesture = self.history[-1]

        if stable_gesture != self.current_gesture:
            self.current_gesture = stable_gesture

            now = time.monotonic()

            if (
                stable_gesture != self.last_event
                or now - self.last_event_time >= self.cooldown
            ):
                self.last_event = stable_gesture
                self.last_event_time = now
                return stable_gesture, stable_gesture

        return self.current_gesture, None

    def reset(self):
        self.history.clear()
        self.current_gesture = "NO HAND"