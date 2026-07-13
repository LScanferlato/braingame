import time
import json
from pathlib import Path


class Session:
    def __init__(self, profile, scoring, difficulty, safety):
        self.profile = profile
        self.scoring = scoring
        self.difficulty = difficulty
        self.safety = safety
        self.session_id = time.strftime("%Y-%m-%d-%H%M%S")
        self.start_time = None
        self.game_log = []
        self.current_game = None

    def start(self):
        self.start_time = time.time()
        self.safety.reset()

    def log_game(self, game_name, result):
        entry = {
            "session_id": self.session_id,
            "game": game_name,
            "difficulty": self.difficulty.get_level(),
            "result": result,
            "timestamp": time.time(),
        }
        self.game_log.append(entry)

    def end(self):
        duration = time.time() - self.start_time if self.start_time else 0
        summary = {
            "session_id": self.session_id,
            "duration_seconds": round(duration, 1),
            "total_score": self.scoring.get_total(),
            "final_difficulty": self.difficulty.get_level(),
            "safety_events": self.safety.get_events(),
            "games": self.game_log,
        }
        self._save(summary)
        return summary

    def _save(self, summary):
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        path = data_dir / f"session_{self.session_id}.json"
        with open(path, "w") as f:
            json.dump(summary, f, indent=2)

    def get_elapsed_minutes(self):
        if self.start_time is None:
            return 0
        return (time.time() - self.start_time) / 60.0
