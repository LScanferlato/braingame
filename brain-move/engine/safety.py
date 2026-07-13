class SafetyEngine:
    def __init__(self):
        self.warnings = []
        self.events = []
        self.max_trunk_angle = 25
        self.max_instability = 0.7
        self.suggestions = {
            "busto_inclinato": "Mantieni la schiena dritta",
            "instabilita_alta": "Fermiamoci un momento e appoggiamoci",
            "passo_largo": "Fai passi piu piccoli",
            "uscita_frame": "Rimani nel raggio della telecamera",
        }

    def evaluate(self, pose_data):
        self.warnings = []
        if pose_data is None:
            return {"status": "no_pose", "message": "Non ti vedo bene, sistemiamoci meglio."}

        trunk_angle = pose_data.get("trunk_angle", 0)
        instability = pose_data.get("instability", 0)
        in_frame = pose_data.get("in_frame", True)

        if not in_frame:
            self.warnings.append("uscita_frame")
        if trunk_angle > self.max_trunk_angle:
            self.warnings.append("busto_inclinato")
        if instability > self.max_instability:
            self.warnings.append("instabilita_alta")

        if "instabilita_alta" in self.warnings or "uscita_frame" in self.warnings:
            return {"status": "pause", "message": "Fermiamoci un momento e appoggiamoci.", "warnings": self.warnings}

        if self.warnings:
            return {"status": "warning", "message": "Facciamo movimenti piu piccoli e lenti.", "warnings": self.warnings}

        return {"status": "ok", "message": "Movimento sicuro.", "warnings": []}

    def log_event(self, event_type, details=""):
        self.events.append({"type": event_type, "details": details})

    def get_events(self):
        return list(self.events)

    def reset(self):
        self.warnings = []
        self.events = []
