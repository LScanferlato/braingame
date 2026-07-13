class FatigueDetector:
    """Rileva segni di affaticamento dall'analisi dei movimenti."""

    def __init__(self):
        self.movement_speeds = []
        self.instability_values = []
        self.trunk_angles = []
        self.window_size = 30
        self.speed_increase_threshold = 0.3
        self.instability_threshold = 0.5

    def update(self, pose_data, movement_detected):
        if pose_data is None:
            return

        speed = self._estimate_speed(pose_data)
        self.movement_speeds.append(speed)
        self.instability_values.append(pose_data.get("instability", 0))
        self.trunk_angles.append(pose_data.get("trunk_angle", 0))

        if len(self.movement_speeds) > self.window_size:
            self.movement_speeds.pop(0)
        if len(self.instability_values) > self.window_size:
            self.instability_values.pop(0)
        if len(self.trunk_angles) > self.window_size:
            self.trunk_angles.pop(0)

    def _estimate_speed(self, pose_data):
        if not hasattr(self, "_prev_hip"):
            self._prev_hip = pose_data["hip_center"]
            return 0.0
        prev = self._prev_hip
        curr = pose_data["hip_center"]
        dx = curr[0] - prev[0]
        dy = curr[1] - prev[1]
        speed = (dx ** 2 + dy ** 2) ** 0.5
        self._prev_hip = curr
        return speed

    def get_fatigue_level(self):
        if len(self.movement_speeds) < 10:
            return "bassa"

        recent = self.movement_speeds[-10:]
        earlier = self.movement_speeds[-20:-10] if len(self.movement_speeds) >= 20 else self.movement_speeds[:10]

        recent_speed = sum(recent) / len(recent)
        earlier_speed = sum(earlier) / len(earlier) if earlier else recent_speed

        recent_instab = sum(self.instability_values[-10:]) / min(10, len(self.instability_values))

        recent_trunk = sum(self.trunk_angles[-10:]) / min(10, len(self.trunk_angles))

        if recent_instab > self.instability_threshold:
            return "alta"
        if earlier_speed > 0 and recent_speed < earlier_speed * 0.5:
            return "alta"
        if recent_trunk > 20:
            return "media"

        return "bassa"

    def should_suggest_pause(self):
        level = self.get_fatigue_level()
        return level == "alta"

    def reset(self):
        self.movement_speeds = []
        self.instability_values = []
        self.trunk_angles = []
        if hasattr(self, "_prev_hip"):
            del self._prev_hip
