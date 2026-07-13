import json
from pathlib import Path


class Profile:
    def __init__(self, profile_path=None):
        if profile_path is None:
            profile_path = Path(__file__).parent.parent / "data" / "user_profiles.json"
        self.path = Path(profile_path)
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path) as f:
                return json.load(f)
        return {
            "user_id": "default",
            "name": "Utente",
            "mobility_level": "medio",
            "requires_support": True,
            "preferred_mode": "standing_with_support",
            "webcam": {"enabled": True, "save_video": False, "pose_only": True},
            "safety": {"max_session_minutes": 24, "seated_fallback": True},
        }

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key, default=None):
        return self.data.get(key, default)
