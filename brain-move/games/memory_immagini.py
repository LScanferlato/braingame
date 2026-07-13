import random
import time
from games.base_game import BaseGame


class MemoryImmagini(BaseGame):
    FAMILIAR = {
        "nonno": "\U0001F474",
        "nonna": "\U0001F475",
        "mamma": "\U0001F469",
        "papa": "\U0001F468",
        "bambino": "\U0001F476",
        "bambina": "\U0001F467",
        "casa": "\U0001F3E0",
        "macchina": "\U0001F697",
        "cane": "\U0001F436",
        "gatto": "\U0001F431",
        "albero": "\U0001F333",
        "fiore": "\U0001F33C",
        "pane": "\U0001F35E",
        "mela": "\U0001F34E",
        "acqua": "\U0001F4A7",
        "sole": "\U0001F31E",
        "luna": "\U0001F319",
        "stella": "\u2B50",
        "cuore": "\u2764\uFE0F",
        "sorriso": "\U0001F60A",
        "libro": "\U0001F4DA",
        "palla": "\u26BD",
        "torta": "\U0001F370",
        "orologio": "\U0001F570",
    }

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "memory_immagini"
        self.display_name = "Memory Immagini"
        self.phase = "instruction"
        self.grid_rows = 0
        self.grid_cols = 0
        self.cards = []
        self.revealed = []
        self.matched = []
        self.first_card = None
        self.waiting = False
        self.wait_timer = 0
        self.pairs_found = 0
        self.total_pairs = 0
        self.attempts = 0
        self.instruction_timer = 0
        self.study_phase = False
        self.study_timer = 0
        self.study_duration = 5

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        self.grid_cols = min(3 + level, 6)
        self.grid_rows = min(2 + level // 2, 4)
        if self.grid_cols * self.grid_rows % 2 != 0:
            self.grid_rows += 1
        self.total_pairs = (self.grid_cols * self.grid_rows) // 2
        self.study_duration = max(3, 7 - level)
        self.phase = "instruction"
        self.instruction_timer = time.time()
        self.feedback_message = f"Memorizza le immagini! Hai {self.study_duration} secondi"

        keys = list(self.FAMILIAR.keys())
        random.shuffle(keys)
        chosen = keys[:self.total_pairs]
        deck = chosen * 2
        random.shuffle(deck)
        self.cards = []
        for label in deck:
            self.cards.append({"label": label, "icon": self.FAMILIAR[label]})
        self.revealed = [False] * len(self.cards)
        self.matched = [False] * len(self.cards)
        self.first_card = None
        self.waiting = False
        self.pairs_found = 0
        self.attempts = 0

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "instruction":
            if time.time() - self.instruction_timer > 2.0:
                self.phase = "study"
                self.study_timer = time.time()
                self.study_phase = True
                for i in range(len(self.cards)):
                    self.revealed[i] = True

        elif self.phase == "study":
            if time.time() - self.study_timer > self.study_duration:
                self.phase = "playing"
                for i in range(len(self.cards)):
                    self.revealed[i] = False
                self.feedback_message = "Trova le coppie!"

        elif self.phase == "playing" and self.waiting:
            self.wait_timer -= dt
            if self.wait_timer <= 0:
                self._end_wait()

    def select_card(self, idx):
        if self.phase != "playing" or self.waiting:
            return False
        if self.matched[idx] or self.revealed[idx]:
            return False

        self.revealed[idx] = True
        if self.first_card is None:
            self.first_card = idx
            return True

        self.attempts += 1
        second = idx
        if self.cards[self.first_card]["label"] == self.cards[second]["label"]:
            self.matched[self.first_card] = True
            self.matched[second] = True
            self.pairs_found += 1
            self.first_card = None
            self.feedback_message = f"Trovata coppia! {self.pairs_found}/{self.total_pairs}"
            if self.pairs_found == self.total_pairs:
                self._finish_game()
            return True
        else:
            self.waiting = True
            self.wait_timer = 1.2
            self._second_card = second
            self.feedback_message = "Non e' la coppia giusta"
            return True

    def _end_wait(self):
        self.revealed[self.first_card] = False
        self.revealed[self._second_card] = False
        self.first_card = None
        self.waiting = False

    def _finish_game(self):
        self.stop()
        accuracy = self.total_pairs / max(self.attempts, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "pairs_found": self.pairs_found,
            "attempts": self.attempts,
            "grid": f"{self.grid_rows}x{self.grid_cols}",
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 30))

    def get_progress(self):
        return self.pairs_found / max(self.total_pairs, 1)

    def is_card_revealed(self, idx):
        return self.revealed[idx]

    def is_card_matched(self, idx):
        return self.matched[idx]

    def get_card_icon(self, idx):
        if 0 <= idx < len(self.cards):
            return self.cards[idx]["icon"]
        return "?"
