class FallRiskDetector:
    """Rileva indicatori di rischio caduta."""

    def __init__(self):
        self.max_trunk_angle = 30
        self.max_instability = 0.8
        self.max_sudden_drop = 50
        self.event_log = []

    def evaluate(self, pose_data, prev_pose=None):
        if pose_data is None:
            return {"risk": "unknown", "events": []}

        events = []
        trunk_angle = pose_data.get("trunk_angle", 0)
        instability = pose_data.get("instability", 0)
        in_frame = pose_data.get("in_frame", True)

        if not in_frame:
            events.append("uscita_improvvisa_dal_frame")

        if trunk_angle > self.max_trunk_angle:
            events.append("busto_inclinato_pericolosamente")

        if instability > self.max_instability:
            events.append("instabilita_elevata")

        if prev_pose is not None:
            drop = prev_pose["hip_center"][1] - pose_data["hip_center"][1]
            if drop > self.max_sudden_drop:
                events.append("caduta_improvvisa_rilevata")

            shoulder_diff = abs(pose_data["shoulder_width"] - prev_pose["shoulder_width"])
            if prev_pose["shoulder_width"] > 0:
                shoulder_pct = shoulder_diff / prev_pose["shoulder_width"]
                if shoulder_pct > 0.4:
                    events.append("rotazione_brusca")

        risk = "ok"
        if len(events) >= 2:
            risk = "alto"
        elif len(events) == 1:
            risk = "medio"

        for e in events:
            self.event_log.append({"event": e})

        return {"risk": risk, "events": events}

    def should_pause(self, evaluation):
        return evaluation["risk"] in ("alto", "medio")

    def get_event_log(self):
        return list(self.event_log)

    def reset(self):
        self.event_log = []
