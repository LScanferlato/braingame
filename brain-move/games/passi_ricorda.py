import random
import time
from games.base_game import BaseGame


class PassiRicorda(BaseGame):
    """Gioco 2: Memoria + movimento - camminata sul posto e richiamo sequenza."""

    ITEMS = ["mela", "chiave", "fiore", "casa", "sole", "tazza", "libro", "stella"]
    ITEM_ICONS = {
        "mela": "\U0001F34E", "chiave": "\U0001F511", "fiore": "\U0001F33C",
        "casa": "\U0001F3E0", "sole": "\U0001F31E", "tazza": "\u2615",
        "libro": "\U0001F4D6", "stella": "\u2B50",
    }

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "passi_ricorda"
        self.display_name = "Passi e Ricorda"
        self.sequence = []
        self.user_answer = []
        self.phase = "showing"
        self.show_index = 0
        self.show_timer = 0
        self.show_interval = 2.0
        self.recall_options = []
        self.step_count = 0
        self.movement_valid = False
        self.correct_count = 0
        self.total_attempts = 0

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        seq_len = min(2 + level, len(self.ITEMS))
        self.sequence = random.sample(self.ITEMS, seq_len)
        self.user_answer = []
        self.recall_options = list(self.ITEMS)
        random.shuffle(self.recall_options)
        self.phase = "showing"
        self.show_index = 0
        self.show_timer = time.time()
        self.step_count = 0
        self.correct_count = 0
        self.total_attempts = 0
        self.feedback_message = "Guarda la sequenza e cammina sul posto"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "showing":
            elapsed = time.time() - self.show_timer
            if elapsed >= self.show_interval:
                self.show_index += 1
                self.show_timer = time.time()
                if self.show_index >= len(self.sequence):
                    self.phase = "moving"
                    self.feedback_message = "Ora cammina piano sul posto!"
                    self.movement_timer = time.time()
        elif self.phase == "moving":
            move_elapsed = time.time() - self.movement_timer
            if move_elapsed > 8:
                self.phase = "recall"
                self.feedback_message = "Scegli gli elementi nell'ordine giusto"
        elif self.phase == "recall":
            pass

    def select_item(self, item):
        if self.phase != "recall":
            return
        self.user_answer.append(item)
        if len(self.user_answer) == len(self.sequence):
            self._check_answer()

    def _check_answer(self):
        self.total_attempts += 1
        correct = self.user_answer == self.sequence
        if correct:
            self.correct_count += 1
            self.scoring.add_score(self.name, 20)
            self.feedback_message = "Perfetto, sequenza corretta!"
        else:
            self.feedback_message = "Non preoccuparti, riproviamo"

        if self.total_attempts >= 3:
            self.stop()
            accuracy = self.correct_count / self.total_attempts
            self.result = {
                "completed": True,
                "accuracy": accuracy,
                "correct": self.correct_count,
                "total": self.total_attempts,
                "sequence": self.sequence,
            }
            self.difficulty.adapt(accuracy)

    def get_current_item(self):
        if self.phase == "showing" and self.show_index < len(self.sequence):
            return self.sequence[self.show_index]
        return None

    def get_options(self):
        return self.recall_options

    def get_progress(self):
        if self.phase == "showing":
            return self.show_index / max(len(self.sequence), 1) * 0.3
        elif self.phase == "moving":
            return 0.3 + 0.3 * min((time.time() - self.movement_timer) / 8, 1)
        elif self.phase == "recall":
            return 0.6 + 0.4 * (len(self.user_answer) / max(len(self.sequence), 1))
        return 0
