import math
import os

try:
    import mediapipe as mp
    import cv2
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False


class PoseDetector:
    """Rilevamento pose del corpo tramite MediaPipe PoseLandmarker (simulazione OpenPose)."""

    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.cap = None
        self.landmarks = None
        self.model_path = os.path.join(os.path.dirname(__file__), "..", "data", "pose_landmarker.task")

        if HAS_MEDIAPIPE and os.path.exists(self.model_path):
            self.base_options = mp.tasks.BaseOptions(model_asset_path=self.model_path)
            self.options = mp.tasks.vision.PoseLandmarkerOptions(
                base_options=self.base_options,
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                min_pose_detection_confidence=min_detection_confidence,
                min_pose_presence_confidence=min_tracking_confidence,
                min_tracking_confidence=min_tracking_confidence,
                num_poses=1,
            )
            self.landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(self.options)
        else:
            self.landmarker = None
            if not os.path.exists(self.model_path):
                print(f"[WARN] Modello pose non trovato: {self.model_path}")
                print("[INFO] Uso modalita sintetica")

        self.timestamp = 0
        self._instability_buffer = []

    def open_camera(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return True

    def read_frame(self):
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def detect(self, frame):
        if frame is None:
            return None
        if not HAS_MEDIAPIPE or self.landmarker is None:
            return self._synthetic_detection(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self.timestamp += 33
        result = self.landmarker.detect_for_video(mp_image, self.timestamp)

        if not result.pose_landmarks:
            return None

        lm = result.pose_landmarks[0]
        h, w = frame.shape[:2]

        def px(idx):
            return (lm[idx].x * w, lm[idx].y * h)

        nose = px(0)
        l_shoulder = px(11)
        r_shoulder = px(12)
        l_hip = px(23)
        r_hip = px(24)
        l_knee = px(25)
        r_knee = px(26)
        l_ankle = px(27)
        r_ankle = px(28)
        l_wrist = px(15)
        r_wrist = px(16)
        l_elbow = px(13)
        r_elbow = px(14)

        shoulder_center = ((l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2)
        hip_center = ((l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2)
        shoulder_width = abs(l_shoulder[0] - r_shoulder[0])
        trunk_angle = self._trunk_angle(l_shoulder, r_shoulder, l_hip, r_hip)
        instability = self._compute_instability(hip_center[0])

        return {
            "in_frame": True,
            "nose": nose,
            "l_shoulder": l_shoulder,
            "r_shoulder": r_shoulder,
            "l_hip": l_hip,
            "r_hip": r_hip,
            "l_knee": l_knee,
            "r_knee": r_knee,
            "l_ankle": l_ankle,
            "r_ankle": r_ankle,
            "l_wrist": l_wrist,
            "r_wrist": r_wrist,
            "l_elbow": l_elbow,
            "r_elbow": r_elbow,
            "shoulder_center": shoulder_center,
            "hip_center": hip_center,
            "shoulder_width": shoulder_width,
            "trunk_angle": trunk_angle,
            "instability": instability,
            "knee_hip_ratio": (l_knee[1] + r_knee[1]) / 2 / max((l_hip[1] + r_hip[1]) / 2, 1),
        }

    def _trunk_angle(self, l_shoulder, r_shoulder, l_hip, r_hip):
        sc = ((l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2)
        hc = ((l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2)
        dx = sc[0] - hc[0]
        dy = sc[1] - hc[1]
        angle = abs(math.degrees(math.atan2(dx, dy)))
        return min(angle, 90.0)

    def _compute_instability(self, hip_x):
        self._instability_buffer.append(hip_x)
        if len(self._instability_buffer) > 30:
            self._instability_buffer.pop(0)
        if len(self._instability_buffer) < 5:
            return 0.0
        diffs = [abs(self._instability_buffer[i] - self._instability_buffer[i - 1])
                 for i in range(1, len(self._instability_buffer))]
        avg_diff = sum(diffs) / len(diffs)
        return min(avg_diff * 10, 1.0)

    def _synthetic_detection(self, frame):
        """Fallback: genera dati sintetici quando MediaPipe non e disponibile."""
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        return {
            "in_frame": True,
            "nose": (cx, cy - 120),
            "l_shoulder": (cx - 60, cy - 80),
            "r_shoulder": (cx + 60, cy - 80),
            "l_hip": (cx - 40, cy + 20),
            "r_hip": (cx + 40, cy + 20),
            "l_knee": (cx - 45, cy + 100),
            "r_knee": (cx + 45, cy + 100),
            "l_ankle": (cx - 50, cy + 180),
            "r_ankle": (cx + 50, cy + 180),
            "l_wrist": (cx - 100, cy - 30),
            "r_wrist": (cx + 100, cy - 30),
            "l_elbow": (cx - 80, cy - 50),
            "r_elbow": (cx + 80, cy - 50),
            "shoulder_center": (cx, cy - 80),
            "hip_center": (cx, cy + 20),
            "shoulder_width": 120,
            "trunk_angle": 5.0,
            "instability": 0.1,
            "knee_hip_ratio": 1.5,
        }

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if hasattr(self, 'landmarker') and self.landmarker is not None:
            self.landmarker.close()
