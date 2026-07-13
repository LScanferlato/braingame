import random
import time
from games.base_game import BaseGame


class MemoryCarte(BaseGame):
    """Gioco memoria: trova le coppie di carte con simboli e animali."""

    SYMBOLS = {
        "gatto": "\U0001F431",
        "cane": "\U0001F436",
        "leone": "\U0001F981",
        "coniglio": "\U0001F430",
        "tartaruga": "\U0001F422",
        "delfino": "\U0001F42C",
        "farfalla": "\U0001F98B",
        "uccello": "\U0001F426",
        "stella": "\u2B50",
        "cuore": "\u2764\uFE0F",
        "sole": "\U0001F31E",
        "luna": "\U0001F319",
        "fiore": "\U0001F33C",
        "albero": "\U0001F333",
        "montagna": "\u26F0\uFE0F",
        "onda": "\U0001F30A",
    }

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "memory_carte"
        self.display_name = "Memory Carte"
        self.grid = []
        self.revealed = []
        self.matched = []
        self.first_card = None
        self.second_card = None
        self.waiting = False
        self.wait_timer = 0
        self.wait_delay = 1.0
        self.pairs_found = 0
        self.total_pairs = 0
        self.attempts = 0
        self.max_attempts = 20
        self.cols = 4
        self.rows = 3
        self.show_all_timer = 0
        self.show_all_duration = 3.0
        self.phase = "preview"

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        if level <= 2:
            self.rows, self.cols = 3, 4
        elif level <= 3:
            self.rows, self.cols = 4, 4
        else:
            self.rows, self.cols = 4, 5

        total_cells = self.rows * self.cols
        self.total_pairs = total_cells // 2
        symbols = list(self.SYMBOLS.keys())
        chosen = random.sample(symbols, self.total_pairs)
        pairs = chosen * 2
        random.shuffle(pairs)
        self.grid = pairs
        self.revealed = [False] * len(self.grid)
        self.matched = [False] * len(self.grid)
        self.first_card = None
        self.second_card = None
        self.waiting = False
        self.pairs_found = 0
        self.attempts = 0
        self.phase = "preview"
        self.show_all_timer = time.time()
        self.revealed = [True] * len(self.grid)
        self.feedback_message = "Ricorda le posizioni delle carte!"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "preview":
            elapsed = time.time() - self.show_all_timer
            if elapsed >= self.show_all_duration:
                self.revealed = [False] * len(self.grid)
                self.phase = "playing"
                self.feedback_message = "Trova le coppie! Seleziona due carte"

        elif self.phase == "playing" and self.waiting:
            elapsed = time.time() - self.wait_timer
            if elapsed >= self.wait_delay:
                self._hide_pair()

    def select_card(self, index):
        if self.phase != "playing" or self.waiting:
            return
        if index < 0 or index >= len(self.grid):
            return
        if self.revealed[index] or self.matched[index]:
            return

        self.revealed[index] = True

        if self.first_card is None:
            self.first_card = index
            self.feedback_message = "Seleziona un'altra carta"
        elif self.second_card is None and index != self.first_card:
            self.second_card = index
            self.attempts += 1
            self._check_match()

    def _check_match(self):
        i, j = self.first_card, self.second_card
        if self.grid[i] == self.grid[j]:
            self.matched[i] = True
            self.matched[j] = True
            self.pairs_found += 1
            self.scoring.add_score(self.name, 15)
            self.feedback_message = f" Coppia trovata: {self.SYMBOLS[self.grid[i]]}!"
            self.first_card = None
            self.second_card = None
            if self.pairs_found == self.total_pairs:
                self._finish_game()
        else:
            self.waiting = True
            self.wait_timer = time.time()
            self.feedback_message = "Non corrispondono..."

    def _hide_pair(self):
        if self.first_card is not None:
            self.revealed[self.first_card] = False
        if self.second_card is not None:
            self.revealed[self.second_card] = False
        self.first_card = None
        self.second_card = None
        self.waiting = False
        self.feedback_message = "Trova le coppie!"

    def _finish_game(self):
        self.stop()
        accuracy = self.pairs_found / max(self.attempts, 1)
        self.result = {
            "completed": True,
            "accuracy": min(accuracy, 1.0),
            "pairs_found": self.pairs_found,
            "total_pairs": self.total_pairs,
            "attempts": self.attempts,
        }
        self.difficulty.adapt(min(accuracy, 1.0))
        self.scoring.add_score(self.name, int(accuracy * 40))

    def get_card_symbol(self, index):
        if 0 <= index < len(self.grid):
            return self.SYMBOLS.get(self.grid[index], "?")
        return ""

    def is_card_revealed(self, index):
        if 0 <= index < len(self.grid):
            return self.revealed[index] or self.matched[index]
        return False

    def is_card_matched(self, index):
        if 0 <= index < len(self.grid):
            return self.matched[index]
        return False

    def get_grid_size(self):
        return self.rows, self.cols

    def get_progress(self):
        return self.pairs_found / max(self.total_pairs, 1)
