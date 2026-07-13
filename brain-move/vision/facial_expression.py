import math
import time

try:
    import mediapipe as mp
    import cv2
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False


class FacialExpressionDetector:
    """Rilevamento espressioni facciali e umore tramite MediaPipe Face Mesh."""

    MOOD_HAPPY = "felice"
    MOOD_NEUTRAL = "neutro"
    MOOD_FOCUSED = "concentrato"
    MOOD_TIRED = "stanco"
    MOOD_WORRIED = "preoccupato"

    MOOD_ICONS = {
        "felice": "\U0001F604",
        "neutro": "\U0001F610",
        "concentrato": "\U0001F914",
        "stanco": "\U0001F634",
        "preoccupato": "\U0001F61F",
    }

    MOOD_COLORS = {
        "felice": (80, 220, 80),
        "neutro": (180, 180, 200),
        "concentrato": (80, 160, 230),
        "stanco": (200, 160, 80),
        "preoccupato": (220, 120, 80),
    }

    MOOD_LABELS = {
        "felice": "Felice",
        "neutro": "Neutro",
        "concentrato": "Concentrato",
        "stanco": "Stanco",
        "preoccupato": "Preoccupato",
    }

    def __init__(self):
        self.face_mesh = None
        self.current_mood = self.MOOD_NEUTRAL
        self.mood_confidence = 0.0
        self.mood_history = []
        self.smile_score = 0.0
        self.eyebrow_score = 0.0
        self.eye_openness = 0.0
        self.last_update = 0
        self.update_interval = 0.5

        if HAS_MEDIAPIPE:
            try:
                self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
            except Exception:
                self.face_mesh = None

    def update(self, frame_rgb):
        if frame_rgb is None or self.face_mesh is None:
            return

        now = time.time()
        if now - self.last_update < self.update_interval:
            return
        self.last_update = now

        try:
            results = self.face_mesh.process(frame_rgb)
        except Exception:
            return

        if not results.multi_face_landmarks:
            return

        landmarks = results.multi_face_landmarks[0]
        lm = landmarks.landmark

        self.smile_score = self._compute_smile(lm)
        self.eyebrow_score = self._compute_eyebrows(lm)
        self.eye_openness = self._compute_eye_openness(lm)

        self._classify_mood()

    def _compute_smile(self, lm):
        mouth_left = lm[61]
        mouth_right = lm[291]
        mouth_top = lm[13]
        mouth_bottom = lm[14]

        width = abs(mouth_right.x - mouth_left.x)
        height = abs(mouth_bottom.y - mouth_top.y)
        if width < 0.001:
            return 0.0

        ratio = height / width

        left_corner_y = lm[61].y
        right_corner_y = lm[291].y
        center_y = (mouth_top.y + mouth_bottom.y) / 2
        corner_avg_y = (left_corner_y + right_corner_y) / 2

        curvature = (center_y - corner_avg_y) / max(width, 0.001)

        score = 0.0
        if ratio > 0.25:
            score += 0.3
        if curvature > 0.05:
            score += 0.4
        if ratio > 0.35 and curvature > 0.1:
            score += 0.3

        return min(max(score, 0.0), 1.0)

    def _compute_eyebrows(self, lm):
        left_brow = lm[70]
        right_brow = lm[300]
        left_eye = lm[159]
        right_eye = lm[386]

        brow_eye_dist_left = left_eye.y - left_brow.y
        brow_eye_dist_right = right_eye.y - right_brow.y
        avg_dist = (brow_eye_dist_left + brow_eye_dist_right) / 2

        score = 0.0
        if avg_dist > 0.06:
            score = 0.8
        elif avg_dist > 0.045:
            score = 0.4
        elif avg_dist < 0.025:
            score = -0.3

        return max(min(score, 1.0), -1.0)

    def _compute_eye_openness(self, lm):
        left_top = lm[159]
        left_bottom = lm[145]
        right_top = lm[386]
        right_bottom = lm[374]

        left_open = abs(left_top.y - left_bottom.y)
        right_open = abs(right_top.y - right_bottom.y)
        avg_open = (left_open + right_open) / 2

        score = min(avg_open / 0.04, 1.0)
        return max(score, 0.0)

    def _classify_mood(self):
        scores = {
            self.MOOD_HAPPY: 0.0,
            self.MOOD_NEUTRAL: 0.0,
            self.MOOD_FOCUSED: 0.0,
            self.MOOD_TIRED: 0.0,
            self.MOOD_WORRIED: 0.0,
        }

        if self.smile_score > 0.5:
            scores[self.MOOD_HAPPY] += self.smile_score

        if self.eye_openness < 0.3:
            scores[self.MOOD_TIRED] += (1.0 - self.eye_openness)

        if self.eyebrow_score > 0.3:
            scores[self.MOOD_WORRIED] += self.eyebrow_score * 0.7
        elif self.eyebrow_score < -0.1:
            scores[self.MOOD_FOCUSED] += 0.5

        if self.smile_score < 0.2 and self.eye_openness > 0.4:
            scores[self.MOOD_NEUTRAL] += 0.4

        best = max(scores, key=scores.get)
        best_score = scores[best]

        if best_score < 0.15:
            best = self.MOOD_NEUTRAL
            best_score = 0.3

        self.mood_history.append(best)
        if len(self.mood_history) > 6:
            self.mood_history.pop(0)

        from collections import Counter
        counts = Counter(self.mood_history)
        self.current_mood = counts.most_common(1)[0][0]
        self.mood_confidence = counts[self.current_mood] / len(self.mood_history)

    def get_mood(self):
        return self.current_mood

    def get_mood_icon(self):
        return self.MOOD_ICONS.get(self.current_mood, "\U0001F610")

    def get_mood_color(self):
        return self.MOOD_COLORS.get(self.current_mood, (180, 180, 200))

    def get_mood_label(self):
        return self.MOOD_LABELS.get(self.current_mood, "Neutro")

    def get_mood_confidence(self):
        return self.mood_confidence

    def get_details(self):
        return {
            "mood": self.current_mood,
            "smile": round(self.smile_score, 2),
            "eyebrow": round(self.eyebrow_score, 2),
            "eye_openness": round(self.eye_openness, 2),
            "confidence": round(self.mood_confidence, 2),
        }

    def close(self):
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None
