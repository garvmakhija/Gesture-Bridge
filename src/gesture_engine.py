import math
class GestureEngine:
    def _distance(self, a, b):
        return math.sqrt(
            (a.x - b.x) ** 2 +
            (a.y - b.y) ** 2 +
            (a.z - b.z) ** 2
        )
    def _angle(self, a, b, c):
        ab = (
            a.x - b.x,
            a.y - b.y,
            a.z - b.z
        )
        cb = (
            c.x - b.x,
            c.y - b.y,
            c.z - b.z
        )

        dot = (
            ab[0] * cb[0] +
            ab[1] * cb[1] +
            ab[2] * cb[2]
        )

        mag_ab = math.sqrt(
            ab[0] ** 2 +
            ab[1] ** 2 +
            ab[2] ** 2
        )

        mag_cb = math.sqrt(
            cb[0] ** 2 +
            cb[1] ** 2 +
            cb[2] ** 2
        )

        if mag_ab == 0 or mag_cb == 0:
            return 0

        value = dot / (mag_ab * mag_cb)
        value = max(-1.0, min(1.0, value))

        return math.degrees(math.acos(value))

    def _finger_straight(self, landmarks, mcp, pip, dip, tip):
        pip_angle = self._angle(
            landmarks[mcp],
            landmarks[pip],
            landmarks[dip]
        )

        dip_angle = self._angle(
            landmarks[pip],
            landmarks[dip],
            landmarks[tip]
        )

        return pip_angle > 155 and dip_angle > 155

    def _finger_curled(self, landmarks, mcp, pip, dip, tip):
        pip_angle = self._angle(
            landmarks[mcp],
            landmarks[pip],
            landmarks[dip]
        )

        dip_angle = self._angle(
            landmarks[pip],
            landmarks[dip],
            landmarks[tip]
        )

        return pip_angle < 150 or dip_angle < 150

    def _thumb_extended(self, landmarks):
        wrist = landmarks[0]
        index_mcp = landmarks[5]
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]

        palm_width = self._distance(
            wrist,
            index_mcp
        )

        thumb_reach = self._distance(
            thumb_tip,
            index_mcp
        )

        thumb_angle = self._angle(
            landmarks[2],
            landmarks[3],
            landmarks[4]
        )

        return (
            thumb_angle > 145
            and thumb_reach > palm_width * 0.65
            and self._distance(thumb_tip, wrist)
            > self._distance(thumb_ip, wrist) * 1.03
        )

    def _thumb_direction(self, landmarks):
        thumb_mcp = landmarks[2]
        thumb_tip = landmarks[4]

        dx = thumb_tip.x - thumb_mcp.x
        dy = thumb_tip.y - thumb_mcp.y

        length = math.sqrt(
            dx ** 2 +
            dy ** 2
        )

        if length == 0:
            return "UNKNOWN"

        vertical_ratio = abs(dy) / length

        if vertical_ratio < 0.55:
            return "SIDE"

        if dy < -0.08:
            return "UP"

        if dy > 0.08:
            return "DOWN"

        return "UNKNOWN"

    def detect(self, hand_landmarks):
        landmarks = hand_landmarks.landmark

        index_straight = self._finger_straight(
            landmarks, 5, 6, 7, 8
        )

        middle_straight = self._finger_straight(
            landmarks, 9, 10, 11, 12
        )

        ring_straight = self._finger_straight(
            landmarks, 13, 14, 15, 16
        )

        pinky_straight = self._finger_straight(
            landmarks, 17, 18, 19, 20
        )

        index_curled = self._finger_curled(
            landmarks, 5, 6, 7, 8
        )

        middle_curled = self._finger_curled(
            landmarks, 9, 10, 11, 12
        )

        ring_curled = self._finger_curled(
            landmarks, 13, 14, 15, 16
        )

        pinky_curled = self._finger_curled(
            landmarks, 17, 18, 19, 20
        )

        thumb_extended = self._thumb_extended(
            landmarks
        )

        curled_count = sum([
            index_curled,
            middle_curled,
            ring_curled,
            pinky_curled
        ])

        straight_count = sum([
            index_straight,
            middle_straight,
            ring_straight,
            pinky_straight
        ])

        if curled_count == 4:
            if thumb_extended:
                direction = self._thumb_direction(
                    landmarks
                )

                if direction == "UP":
                    return "THUMBS UP"

                if direction == "DOWN":
                    return "THUMBS DOWN"

            return "FIST"

        if (
            index_straight
            and not middle_straight
            and not ring_straight
            and not pinky_straight
        ):
            return "POINT UP"

        if (
            index_straight
            and middle_straight
            and not ring_straight
            and not pinky_straight
        ):
            return "VICTORY"

        if straight_count == 4:
            return "OPEN PALM"

        return "UNKNOWN"