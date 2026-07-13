import time


class BaseGame:
    """Classe base per tutti i giochi Brain-Move."""

    def __init__(self, difficulty_engine, scoring_engine):
        self.difficulty = difficulty_engine
        self.scoring = scoring_engine
        self.name = "base_game"
        self.display_name = "Gioco Base"
        self.running = False
        self.state = "idle"
        self.result = {}
        self.feedback_message = ""
        self.start_time = None
        self.duration_seconds = 0

    def start(self):
        self.running = True
        self.state = "playing"
        self.start_time = time.time()
        self.feedback_message = f"Preparati per {self.display_name}"

    def stop(self):
        self.running = False
        self.state = "finished"
        if self.start_time:
            self.duration_seconds = time.time() - self.start_time

    def update(self, pose_data=None, dt=0):
        raise NotImplementedError

    def get_state(self):
        return {
            "name": self.name,
            "display_name": self.display_name,
            "state": self.state,
            "feedback": self.feedback_message,
            "duration": self.duration_seconds,
            "result": self.result,
        }

    def is_finished(self):
        return self.state == "finished"

    def get_result(self):
        return self.result

    def get_progress(self):
        return 0
