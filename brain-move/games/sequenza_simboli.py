import random
import time
from games.base_game import BaseGame


class SequenzaSimboli(BaseGame):
    """Gioco memoria: ricorda e ripeti una sequenza di simboli e animali."""

    SYMBOLS = {
        "gatto": "\U0001F431",
        "cane": "\U0001F436",
        "coniglio": "\U0001F430",
        "delfino": "\U0001F42C",
        "farfalla": "\U0001F98B",
        "uccello": "\U0001F426",
        "stella": "\u2B50",
        "cuore": "\u2764\uFE0F",
        "sole": "\U0001F31E",
        "luna": "\U0001F319",
        "fiore": "\U0001F33C",
        "moneta": "\U0001FA99",
    }

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "sequenza_simboli"
        self.display_name = "Sequenza Simboli"
        self.sequence = []
        self.user_sequence = []
        self.available_symbols = []
        self.phase = "showing"
        self.show_index = 0
        self.show_timer = 0
        self.show_interval = 1.5
        self.round_number = 0
        self.max_rounds = 8
        self.correct_count = 0
        self.highlight_index = -1

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        seq_len = min(3 + level, 8)
        symbols = list(self.SYMBOLS.keys())
        self.available_symbols = random.sample(symbols, min(6, len(symbols)))
        self.sequence = random.choices(self.available_symbols, k=seq_len)
        self.user_sequence = []
        self.round_number = 0
        self.correct_count = 0
        self.phase = "showing"
        self.show_index = 0
        self.show_timer = time.time()
        self.highlight_index = 0
        self.feedback_message = "Osserva la sequenza!"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "showing":
            elapsed = time.time() - self.show_timer
            if elapsed >= self.show_interval:
                self.show_index += 1
                self.show_timer = time.time()
                if self.show_index >= len(self.sequence):
                    self.phase = "input"
                    self.highlight_index = -1
                    self.feedback_message = "Ripeti la sequenza cliccando i simboli"
                else:
                    self.highlight_index = self.show_index

        elif self.phase == "correct_flash":
            elapsed = time.time() - self.flash_timer
            if elapsed >= 0.8:
                self.round_number += 1
                if self.round_number >= self.max_rounds:
                    self._finish_game()
                else:
                    self._next_round()

        elif self.phase == "wrong_flash":
            elapsed = time.time() - self.flash_timer
            if elapsed >= 1.2:
                self._finish_game()

    def _next_round(self):
        level = self.difficulty.get_level()
        extra = min(self.round_number // 2, 2)
        new_len = min(3 + level + extra, len(self.SYMBOLS))
        self.sequence = random.choices(self.available_symbols, k=new_len)
        self.user_sequence = []
        self.phase = "showing"
        self.show_index = 0
        self.show_timer = time.time()
        self.highlight_index = 0
        self.feedback_message = f"Round {self.round_number + 1}: osserva!"

    def select_symbol(self, symbol):
        if self.phase != "input":
            return

        self.user_sequence.append(symbol)
        idx = len(self.user_sequence) - 1

        if self.user_sequence[idx] != self.sequence[idx]:
            self.phase = "wrong_flash"
            self.flash_timer = time.time()
            self.feedback_message = "Sbagliato!"
            return

        if len(self.user_sequence) == len(self.sequence):
            self.correct_count += 1
            self.scoring.add_score(self.name, 20)
            self.phase = "correct_flash"
            self.flash_timer = time.time()
            self.feedback_message = "Corretto!"

    def _finish_game(self):
        self.stop()
        accuracy = self.correct_count / max(self.round_number, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct_rounds": self.correct_count,
            "total_rounds": self.round_number,
            "sequence_length": len(self.sequence),
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 50))

    def get_current_show_item(self):
        if self.phase == "showing" and self.show_index < len(self.sequence):
            return self.SYMBOLS.get(self.sequence[self.show_index], "?")
        return None

    def get_available_symbols(self):
        return [(s, self.SYMBOLS[s]) for s in self.available_symbols]

    def get_progress(self):
        if self.phase == "showing":
            return self.show_index / max(len(self.sequence), 1) * 0.5
        elif self.phase in ("input", "correct_flash", "wrong_flash"):
            return 0.5 + 0.5 * (self.round_number / max(self.max_rounds, 1))
        return 0

    def get_round_info(self):
        return self.round_number + 1, self.max_rounds
