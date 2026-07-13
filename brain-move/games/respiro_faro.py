import random
import time
from games.base_game import BaseGame


class RespiroFaro(BaseGame):
    """Gioco 1: Respirazione guidata con animazione faro/sfera."""

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "respiro_faro"
        self.display_name = "Respiro del Faro"
        self.phase = "inspira"
        self.cycle_duration = 8.0
        self.phase_duration = 4.0
        self.cycle_count = 0
        self.total_cycles = 6
        self.phase_start = 0
        self.circle_scale = 0.3
        self.target_scale = 1.0
        self.instructions = [
            "Inspira lentamente...",
            "Espiral lentamente...",
            "Mantieni il ritmo...",
        ]

    def start(self):
        super().start()
        self.phase_start = time.time()
        self.phase = "inspira"
        self.target_scale = 1.0
        self.feedback_message = "Inspira lentamente..."

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        elapsed = time.time() - self.phase_start

        if elapsed < self.phase_duration:
            progress = elapsed / self.phase_duration
            if self.phase == "inspira":
                self.circle_scale = 0.3 + 0.7 * progress
            else:
                self.circle_scale = 1.0 - 0.7 * progress
        else:
            self.phase = "espira" if self.phase == "inspira" else "inspira"
            self.phase_start = time.time()
            self.cycle_count += 1

            if self.cycle_count >= self.total_cycles:
                self.stop()
                self.result = {"completed": True, "cycles": self.cycle_count}
                self.scoring.add_score(self.name, 10)
                self.feedback_message = "Ottimo controllo, sessione completata!"
                return

            self.feedback_message = random.choice(self.instructions)

    def get_circle_scale(self):
        return self.circle_scale

    def get_progress(self):
        return min(self.cycle_count / self.total_cycles, 1.0)
